<template>
  <div class="pdf-viewer">
    <!-- 工具栏 -->
    <div class="viewer-toolbar">
      <div class="toolbar-left">
        <el-button-group>
          <el-button icon="ZoomOut" @click="zoomOut" :disabled="scale <= 0.5" />
          <el-button icon="ZoomIn" @click="zoomIn" :disabled="scale >= 3" />
          <el-button @click="fitWidth">适应宽度</el-button>
        </el-button-group>
        <span class="zoom-level">{{ Math.round(scale * 100) }}%</span>
      </div>
      <div class="toolbar-center">
        <el-button-group>
          <el-button icon="ArrowLeft" @click="prevPage" :disabled="currentPage <= 1" />
          <el-button disabled>
            {{ currentPage }} / {{ totalPages }}
          </el-button>
          <el-button icon="ArrowRight" @click="nextPage" :disabled="currentPage >= totalPages" />
        </el-button-group>
      </div>
      <div class="toolbar-right">
        <el-checkbox v-model="showHighlights" label="显示高亮" />
        <el-button icon="View" @click="toggleHighlightPanel">
          条款列表
        </el-button>
      </div>
    </div>

    <!-- 主内容区 -->
    <div class="viewer-main">
      <!-- PDF 渲染区 -->
      <div class="pdf-container" ref="containerRef">
        <div v-if="loading" class="loading-overlay">
          <el-skeleton :rows="5" animated />
          <p>正在加载 PDF...</p>
        </div>
        <div v-else-if="error" class="error-overlay">
          <el-result icon="error" :title="errorMessage" />
        </div>
        <canvas
          v-show="!loading && !error"
          ref="canvasRef"
          class="pdf-canvas"
          @click="handleCanvasClick"
        />
        <!-- 高亮层 -->
        <svg
          v-if="showHighlights && currentHighlights.length"
          class="highlight-layer"
          :style="{
            width: canvasWidth + 'px',
            height: canvasHeight + 'px',
            left: canvasLeft + 'px',
            top: canvasTop + 'px'
          }"
        >
          <rect
            v-for="(hl, idx) in currentHighlights"
            :key="idx"
            :x="hl.x"
            :y="hl.y"
            :width="hl.width"
            :height="hl.height"
            :fill="getHighlightColor(hl.risk_level)"
            :fill-opacity="0.3"
            :stroke="getHighlightColor(hl.risk_level)"
            stroke-width="1"
            class="highlight-rect"
            :data-clause="idx"
            @click.stop="handleHighlightClick(idx, hl)"
          />
        </svg>
      </div>

      <!-- 条款列表侧边栏 -->
      <div v-if="showClausePanel" class="clause-panel">
        <div class="panel-header">
          <h4>风险条款</h4>
          <el-button icon="Close" text @click="showClausePanel = false" />
        </div>
        <div class="clause-list">
          <div
            v-for="(clause, idx) in clauseLocations"
            :key="idx"
            class="clause-item"
            :class="'clause-' + clause.risk_level"
            @click="jumpToClause(clause)"
          >
            <div class="clause-header">
              <span class="clause-title">{{ clause.clause_title || '条款 ' + (idx + 1) }}</span>
              <el-tag :type="getRiskTag(clause.risk_level)" size="small">
                {{ getRiskText(clause.risk_level) }}
              </el-tag>
            </div>
            <p class="clause-preview">{{ truncateText(clause.clause_text, 80) }}</p>
            <span class="clause-page">第 {{ clause.page + 1 }} 页</span>
          </div>
        </div>
      </div>
    </div>

    <!-- 点击高亮后的条款详情 -->
    <el-dialog
      v-model="showClauseDetail"
      :title="selectedClause?.clause_title || '条款详情'"
      width="600px"
    >
      <div v-if="selectedClause" class="clause-detail">
        <el-tag :type="getRiskTag(selectedClause.risk_level)" class="risk-tag">
          {{ getRiskText(selectedClause.risk_level) }}
        </el-tag>
        <div class="detail-section">
          <h5>原文</h5>
          <p class="clause-text">{{ selectedClause.clause_text }}</p>
        </div>
        <div class="detail-section">
          <h5>位置</h5>
          <p>第 {{ (selectedClause.page || 0) + 1 }} 页</p>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, shallowRef, computed, onMounted, onUnmounted, watch, nextTick, toRaw } from 'vue'
import { contractsApi } from '@/api/contracts'
import axios from 'axios'

const props = defineProps({
  contractId: {
    type: String,
    required: true
  },
  highlightedPdfUrl: {
    type: String,
    default: null
  }
})

const containerRef = ref(null)
const canvasRef = ref(null)

const loading = ref(false)
const error = ref(false)
const errorMessage = ref('')

// PDF 状态
const pdfDoc = shallowRef(null)
const currentPage = ref(1)
const totalPages = ref(0)
const scale = ref(1.0)
const canvasWidth = ref(0)
const canvasHeight = ref(0)
const canvasLeft = ref(0)
const canvasTop = ref(0)

// 高亮相关
const showHighlights = ref(true)
const showClausePanel = ref(false)
const clauseLocations = ref([])
const selectedClause = ref(null)
const showClauseDetail = ref(false)

// 竞态保护：跟踪当前加载任务
let currentLoadingTask: any = null

// 安全销毁 PDF
async function destroyPdf() {
  if (!pdfDoc.value) return
  try {
    await pdfDoc.value.destroy()
  } catch (e) {
    console.warn('PDF destroy warning:', e)
  }
  pdfDoc.value = null
}

// 加载 PDF
const loadPdf = async () => {
  // 取消上一个还在加载中的任务
  if (currentLoadingTask) {
    try {
      await currentLoadingTask.destroy()
    } catch (e) {
      // ignore
    }
    currentLoadingTask = null
  }

  await destroyPdf()

  loading.value = true
  error.value = false

  try {
    // 动态加载 pdf.js
    if (!window.pdfjsLib) {
      await loadPdfJs()
    }

    window.pdfjsLib.GlobalWorkerOptions.workerSrc =
      '/lib/pdf.worker.min.js'

    // 获取 PDF 数据（使用 axios 带认证token）
    let pdfData
    if (props.highlightedPdfUrl) {
      // 外部URL直接使用
      const response = await axios.get(props.highlightedPdfUrl, { responseType: 'arraybuffer' })
      pdfData = response.data
    } else {
      // 通过后端API获取，需要携带认证token
      const token = localStorage.getItem('token')
      const response = await axios.get(
        `/api/v1/contracts/${props.contractId}/highlighted-pdf`,
        {
          responseType: 'arraybuffer',
          headers: token ? { Authorization: `Bearer ${token}` } : {}
        }
      )
      pdfData = response.data
    }

    currentLoadingTask = window.pdfjsLib.getDocument({ data: pdfData })
    pdfDoc.value = await currentLoadingTask.promise
    currentLoadingTask = null
    totalPages.value = toRaw(pdfDoc.value).numPages

    // 渲染第一页
    await renderPage(1)

    // 加载条款位置
    await loadClauseLocations()
  } catch (err: any) {
    if (err?.name !== 'AbortException') {
      console.error('PDF 加载失败:', err)
      error.value = true
      errorMessage.value = 'PDF 加载失败'
    }
  } finally {
    loading.value = false
  }
}

// 加载 pdf.js
const loadPdfJs = () => {
  return new Promise((resolve, reject) => {
    if (window.pdfjsLib) {
      resolve()
      return
    }
    const script = document.createElement('script')
    script.src = '/lib/pdf.min.js'
    script.onload = resolve
    script.onerror = reject
    document.head.appendChild(script)
  })
}

// 渲染指定页面
const renderPage = async (pageNum) => {
  if (!pdfDoc.value) return

  // 使用 toRaw 获取 pdf.js 原始对象，避免 Vue 代理导致的问题
  const rawPdfDoc = toRaw(pdfDoc.value)
  const page = await rawPdfDoc.getPage(pageNum)
  const viewport = page.getViewport({ scale: scale.value })

  const canvas = canvasRef.value
  if (!canvas) return

  const context = canvas.getContext('2d')
  canvas.width = viewport.width
  canvas.height = viewport.height
  canvasWidth.value = viewport.width
  canvasHeight.value = viewport.height

  // 计算 canvas 位置（居中）
  const container = containerRef.value
  if (container) {
    canvasLeft.value = (container.clientWidth - viewport.width) / 2
    canvasTop.value = 0
  }

  await page.render({
    canvasContext: context,
    viewport: viewport
  }).promise
}

// 加载条款位置
const loadClauseLocations = async () => {
  try {
    const locations = await contractsApi.getClauseLocations(props.contractId)
    clauseLocations.value = locations
  } catch (err) {
    console.error('条款位置加载失败:', err)
  }
}

// 当前页的高亮
const currentHighlights = computed(() => {
  return clauseLocations.value
    .filter(c => c.page === currentPage.value - 1 && c.bbox)
    .map(c => ({
      ...c,
      x: (c.bbox.x0 || 0) * scale.value,
      y: (c.bbox.y0 || 0) * scale.value,
      width: ((c.bbox.x1 || 0) - (c.bbox.x0 || 0)) * scale.value,
      height: ((c.bbox.y1 || 0) - (c.bbox.y0 || 0)) * scale.value
    }))
})

// 翻页
const prevPage = () => {
  if (currentPage.value > 1) {
    currentPage.value--
    renderPage(currentPage.value)
  }
}

const nextPage = () => {
  if (currentPage.value < totalPages.value) {
    currentPage.value++
    renderPage(currentPage.value)
  }
}

// 缩放
const zoomIn = () => {
  scale.value = Math.min(3, scale.value + 0.25)
  renderPage(currentPage.value)
}

const zoomOut = () => {
  scale.value = Math.max(0.5, scale.value - 0.25)
  renderPage(currentPage.value)
}

const fitWidth = () => {
  if (containerRef.value && pdfDoc.value) {
    const containerWidth = containerRef.value.clientWidth - 40
    scale.value = containerWidth / 595 // 假设 PDF 宽度为 595
    renderPage(currentPage.value)
  }
}

// 跳转高亮位置
const jumpToClause = (clause) => {
  if (clause.page !== undefined) {
    currentPage.value = clause.page + 1
    renderPage(currentPage.value)
  }
  showClausePanel.value = false
}

// 点击画布
const handleCanvasClick = (e) => {
  // 可以实现点击高亮区域查看详情
}

// 点击高亮
const handleHighlightClick = (idx, hl) => {
  const clauses = clauseLocations.value.filter(
    c => c.page === currentPage.value - 1
  )
  if (clauses[idx]) {
    selectedClause.value = clauses[idx]
    showClauseDetail.value = true
  }
}

// 切换高亮面板
const toggleHighlightPanel = () => {
  showClausePanel.value = !showClausePanel.value
}

// 辅助方法
const getRiskTag = (level) => {
  const map = { 'high': 'danger', 'medium': 'warning', 'low': 'success' }
  return map[level] || 'info'
}

const getRiskText = (level) => {
  const map = { 'high': '高风险', 'medium': '中风险', 'low': '低风险' }
  return map[level] || level
}

const getHighlightColor = (level) => {
  const map = {
    'high': '#F56C6C',
    'medium': '#E6A23C',
    'low': '#67C23A'
  }
  return map[level] || '#409EFF'
}

const truncateText = (text, maxLen) => {
  if (!text) return ''
  return text.length > maxLen ? text.slice(0, maxLen) + '...' : text
}

onMounted(() => {
  loadPdf()
})

watch(() => props.contractId, () => {
  loadPdf()
})

onUnmounted(() => {
  // 取消正在加载的任务
  if (currentLoadingTask) {
    try {
      currentLoadingTask.destroy()
    } catch (e) {
      // ignore
    }
    currentLoadingTask = null
  }
  destroyPdf()
})
</script>

<style scoped>
.pdf-viewer {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: var(--color-bg-light);
}

.viewer-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 16px;
  background: var(--color-bg-white);
  border-bottom: 1px solid var(--color-border);
  gap: 16px;
}

.toolbar-left,
.toolbar-center,
.toolbar-right {
  display: flex;
  align-items: center;
  gap: 12px;
}

.zoom-level {
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
  min-width: 50px;
}

.viewer-main {
  display: flex;
  flex: 1;
  overflow: hidden;
}

.pdf-container {
  flex: 1;
  position: relative;
  overflow: auto;
  display: flex;
  justify-content: center;
  padding: 20px;
}

.pdf-canvas {
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
}

.loading-overlay,
.error-overlay {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  background: var(--color-bg-white);
  padding: 24px;
  border-radius: var(--radius-md);
  text-align: center;
}

.highlight-layer {
  position: absolute;
  pointer-events: none;
}

.highlight-rect {
  pointer-events: auto;
  cursor: pointer;
  transition: fill-opacity 0.2s;
}

.highlight-rect:hover {
  fill-opacity: 0.5;
}

.clause-panel {
  width: 320px;
  background: var(--color-bg-white);
  border-left: 1px solid var(--color-border);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  border-bottom: 1px solid var(--color-border);
}

.panel-header h4 {
  margin: 0;
  font-size: var(--font-size-base);
}

.clause-list {
  flex: 1;
  overflow-y: auto;
  padding: 8px;
}

.clause-item {
  padding: 12px;
  border-radius: var(--radius-sm);
  margin-bottom: 8px;
  cursor: pointer;
  border-left: 3px solid var(--color-border);
  transition: background-color 0.2s;
}

.clause-item:hover {
  background: var(--color-bg-light);
}

.clause-item.clause-high {
  border-left-color: var(--color-red-text);
}

.clause-item.clause-medium {
  border-left-color: var(--color-orange-text);
}

.clause-item.clause-low {
  border-left-color: var(--color-green-text);
}

.clause-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 6px;
}

.clause-title {
  font-weight: 600;
  font-size: var(--font-size-sm);
  color: var(--color-text-primary);
}

.clause-preview {
  font-size: var(--font-size-xs);
  color: var(--color-text-secondary);
  margin: 0 0 6px 0;
  line-height: 1.4;
}

.clause-page {
  font-size: var(--font-size-xs);
  color: var(--color-text-tertiary);
}

.clause-detail {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.risk-tag {
  align-self: flex-start;
}

.detail-section h5 {
  margin: 0 0 8px 0;
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
}

.clause-text {
  padding: 12px;
  background: var(--color-bg-light);
  border-radius: var(--radius-sm);
  font-size: var(--font-size-sm);
  line-height: 1.6;
  margin: 0;
  white-space: pre-wrap;
}
</style>
