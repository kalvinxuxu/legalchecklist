<script setup lang="ts">
import { ref, shallowRef, computed, onMounted, onUnmounted, watch, nextTick } from 'vue'
import * as pdfjsLib from 'pdfjs-dist'
import { Loader2, AlertTriangle } from 'lucide-vue-next'
import api from '@/lib/api'
import { cn } from '@/lib/utils'
import type { BBox, EvidenceLocation } from '@/types/document'

// Configure pdf.js worker - use local worker file via Vite ?url import
pdfjsLib.GlobalWorkerOptions.workerSrc = new URL(
  'pdfjs-dist/legacy/build/pdf.worker.min.mjs',
  import.meta.url
).href

interface Props {
  contractId: string
  highlights?: Array<{
    page: number
    bbox?: BBox
    locations?: EvidenceLocation[]
    risk_level?: string
    clause_title?: string
    evidence_id?: string
    resolution_status?: 'resolved' | 'fuzzy_fallback' | 'page_only' | 'unresolved'
  }>
  highlightClauseId?: string | null
}

const props = withDefaults(defineProps<Props>(), {
  highlights: () => [],
  highlightClauseId: null
})

const emit = defineEmits<{
  (e: 'clause-click', clause: { page: number; bbox: { x0: number; y0: number; x1: number; y1: number } }): void
}>()

const containerRef = ref<HTMLElement | null>(null)
const canvasRef = ref<HTMLCanvasElement | null>(null)
const highlightSvgRef = ref<SVGSVGElement | null>(null)

const loading = ref(true)
const error = ref(false)
const errorMessage = ref('')

const pdfDoc = shallowRef<pdfjsLib.PDFDocumentProxy | null>(null)
const currentPage = ref(1)
const totalPages = ref(0)
const scale = ref(1.0)
const canvasWidth = ref(0)
const canvasHeight = ref(0)

const showHighlightLayer = ref(true)
const activeEvidenceId = ref<string | null>(null)
const activeEvidenceLocationIndex = ref(0)

// 竞态保护：跟踪当前加载任务
let currentLoadingTask: pdfjsLib.PDFDocumentLoadingTask | null = null

// Load PDF
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
    const response = await api.get(
      `/contracts/${props.contractId}/file`,
      { responseType: 'arraybuffer' }
    ) as ArrayBuffer

    currentLoadingTask = pdfjsLib.getDocument({ data: response })
    pdfDoc.value = await currentLoadingTask.promise
    currentLoadingTask = null
    totalPages.value = pdfDoc.value.numPages

    await renderPage(1)
    // 首次打开时直接按查看区域宽度渲染，避免 A4 页面以固定 100% 缩放显示过小。
    await fitWidthWhenReady()
  } catch (err: any) {
    if (err?.name !== 'AbortException') {
      console.error('PDF load failed:', err)
      error.value = true
      errorMessage.value = 'PDF加载失败'
    }
  } finally {
    loading.value = false
  }
}

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

// Render page
const renderPage = async (pageNum: number) => {
  if (!pdfDoc.value || !canvasRef.value) return

  const page = await pdfDoc.value.getPage(pageNum)
  const viewport = page.getViewport({ scale: scale.value })

  const canvas = canvasRef.value
  const context = canvas.getContext('2d')
  if (!context) return

  canvas.width = viewport.width
  canvas.height = viewport.height
  canvasWidth.value = viewport.width
  canvasHeight.value = viewport.height

  await page.render({
    canvasContext: context,
    viewport: viewport,
    canvas: canvas
  } as any).promise

  // Update SVG highlight layer size
  if (highlightSvgRef.value) {
    highlightSvgRef.value.setAttribute('width', String(viewport.width))
    highlightSvgRef.value.setAttribute('height', String(viewport.height))
  }
}

// Current page highlights
const currentHighlights = computed(() => {
  if (!showHighlightLayer.value) return []

  return props.highlights.flatMap(h => (h.locations?.length ? h.locations.map(location => ({ ...h, page: location.page, bbox: location.bbox })) : [h]))
    .filter(h => h.page === currentPage.value - 1 && h.bbox)
    .map(h => {
      const bbox = h.bbox!
      return {
        ...h,
        active: !!h.evidence_id && h.evidence_id === activeEvidenceId.value,
        x: bbox.x0 * scale.value,
        y: bbox.y0 * scale.value,
        width: (bbox.x1 - bbox.x0) * scale.value,
        height: (bbox.y1 - bbox.y0) * scale.value
      }
    })
})

// Get highlight color by risk level
const getHighlightColor = (level?: string) => {
  const colors: Record<string, string> = {
    high: '#C62828',
    medium: '#E65100',
    low: '#2E7D32'
  }
  return colors[level || ''] || '#1565C0'
}

// Navigation
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

const goToPage = (page: number) => {
  if (page >= 1 && page <= totalPages.value) {
    currentPage.value = page
    renderPage(page)
  }
}

// Zoom
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
    if (containerWidth <= 0) return
    scale.value = containerWidth / 595
    renderPage(currentPage.value)
  }
}

// PDF 可能在 Tabs/Flex 布局完成前加载，此时容器宽度为 0；等待布局完成后重试。
const fitWidthWhenReady = async () => {
  await nextTick()
  for (let attempt = 0; attempt < 4; attempt += 1) {
    if (containerRef.value?.clientWidth && pdfDoc.value) {
      fitWidth()
      return
    }
    await new Promise<void>(resolve => requestAnimationFrame(() => resolve()))
  }
}

// Handle highlight click
const handleHighlightClick = (h: (typeof props.highlights)[0]) => {
  if (h.bbox) {
    emit('clause-click', { page: h.page, bbox: h.bbox })
  }
}

// Expose method to jump to a specific clause
const jumpToClause = (page: number, bbox: { x0: number; y0: number; x1: number; y1: number }) => {
  goToPage(page + 1)
  // The current viewer renders one bounded page canvas; changing the page is
  // the reliable navigation primitive and the SVG overlay renders the bbox.
}

const evidenceLocations = (evidenceId: string) => {
  const locations = props.highlights
    .filter(item => item.evidence_id === evidenceId)
    .flatMap(item => item.locations?.length ? item.locations : [{ page: item.page, bbox: item.bbox }])
    .filter(location => location.bbox)
  return locations.filter((location, index, all) =>
    all.findIndex(candidate => candidate.page === location.page &&
      candidate.bbox?.x0 === location.bbox?.x0 && candidate.bbox?.y0 === location.bbox?.y0 &&
      candidate.bbox?.x1 === location.bbox?.x1 && candidate.bbox?.y1 === location.bbox?.y1) === index,
  )
}

const jumpToEvidence = (evidenceId: string) => {
  const locations = evidenceLocations(evidenceId)
  const location = locations[0]
  if (location?.bbox) {
    activeEvidenceId.value = evidenceId
    activeEvidenceLocationIndex.value = 0
    jumpToClause(location.page, location.bbox)
  }
}

const moveEvidenceLocation = (direction: 1 | -1) => {
  if (!activeEvidenceId.value) return
  const locations = evidenceLocations(activeEvidenceId.value)
  if (!locations.length) return
  activeEvidenceLocationIndex.value = (activeEvidenceLocationIndex.value + direction + locations.length) % locations.length
  const location = locations[activeEvidenceLocationIndex.value]
  if (location?.bbox) jumpToClause(location.page, location.bbox)
}

// Watch for highlight changes
watch(() => props.highlightClauseId, async (newId) => {
  if (newId) {
    const h = props.highlights.find(h => h.bbox && `clause-${h.page}-${h.bbox.x0}` === newId)
    if (h && h.bbox) {
      jumpToClause(h.page, h.bbox)
    }
  }
})

// Watch contractId
watch(() => props.contractId, () => {
  loadPdf()
})

onMounted(() => {
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

defineExpose({ jumpToClause, jumpToEvidence })
</script>

<template>
  <div class="pdf-viewer">
    <!-- Toolbar -->
    <div class="flex items-center justify-between px-4 py-2 bg-card border-b border-border">
      <div class="flex items-center gap-2">
        <UiButton variant="outline" size="icon" @click="zoomOut" :disabled="scale <= 0.5">
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20 12H4" />
          </svg>
        </UiButton>
        <span class="text-sm w-12 text-center">{{ Math.round(scale * 100) }}%</span>
        <UiButton variant="outline" size="icon" @click="zoomIn" :disabled="scale >= 3">
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
          </svg>
        </UiButton>
        <UiButton variant="outline" size="sm" @click="fitWidth">适应宽度</UiButton>
      </div>

      <div class="flex items-center gap-2">
        <UiButton variant="outline" size="icon" @click="prevPage" :disabled="currentPage <= 1">
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" />
          </svg>
        </UiButton>
        <span class="text-sm">
          {{ currentPage }} / {{ totalPages }}
        </span>
        <UiButton variant="outline" size="icon" @click="nextPage" :disabled="currentPage >= totalPages">
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
          </svg>
        </UiButton>
      </div>

      <div v-if="activeEvidenceId && evidenceLocations(activeEvidenceId).length > 1" class="flex items-center gap-1">
        <UiButton variant="outline" size="icon" title="上一处证据" @click="moveEvidenceLocation(-1)">
          <span class="text-sm">‹</span>
        </UiButton>
        <span class="text-xs text-muted-foreground">
          证据 {{ activeEvidenceLocationIndex + 1 }} / {{ evidenceLocations(activeEvidenceId).length }}
        </span>
        <UiButton variant="outline" size="icon" title="下一处证据" @click="moveEvidenceLocation(1)">
          <span class="text-sm">›</span>
        </UiButton>
      </div>

      <div class="flex items-center gap-2">
        <label class="flex items-center gap-2 text-sm cursor-pointer">
          <input type="checkbox" v-model="showHighlightLayer" class="rounded" />
          显示高亮
        </label>
      </div>
    </div>

    <!-- PDF Container -->
    <div ref="containerRef" class="flex-1 overflow-auto p-5 flex justify-center">
      <!-- Loading -->
      <div v-if="loading" class="flex items-center justify-center h-full">
        <Loader2 class="w-8 h-8 animate-spin text-muted-foreground" />
        <span class="ml-2 text-muted-foreground">正在加载PDF...</span>
      </div>

      <!-- Error -->
      <div v-else-if="error" class="flex flex-col items-center justify-center h-full text-center">
        <AlertTriangle class="w-12 h-12 text-danger-500 mb-4" />
        <p class="text-lg font-medium text-danger-500">加载失败</p>
        <p class="text-sm text-muted-foreground">{{ errorMessage }}</p>
      </div>

      <!-- PDF Canvas -->
      <div v-else class="relative">
        <canvas ref="canvasRef" class="pdf-canvas shadow-lg" />

        <!-- Highlight SVG Overlay -->
        <svg
          v-if="showHighlightLayer && currentHighlights.length"
          ref="highlightSvgRef"
          class="absolute top-0 left-0 pointer-events-none"
          :style="{ width: canvasWidth + 'px', height: canvasHeight + 'px' }"
        >
          <rect
            v-for="(h, idx) in currentHighlights"
            :key="idx"
            :x="h.x"
            :y="h.y"
            :width="h.width"
            :height="h.height"
            :fill="getHighlightColor(h.risk_level)"
            :fill-opacity="h.active ? 0.55 : 0.22"
            :stroke="getHighlightColor(h.risk_level)"
            :stroke-width="h.active ? 4 : 2"
            class="cursor-pointer pointer-events-auto transition-all"
            @click.stop="handleHighlightClick(h)"
          />
        </svg>
      </div>
    </div>
  </div>
</template>

<style scoped>
.pdf-viewer {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: var(--color-bg, #f8f9fa);
}

.pdf-canvas {
  display: block;
}
</style>
