<script setup lang="ts">
import { ref, shallowRef, computed, onMounted, onUnmounted, watch, nextTick } from 'vue'
import * as pdfjsLib from 'pdfjs-dist'
import api from '@/lib/api'
import { cn } from '@/lib/utils'

// Configure pdf.js worker - use local worker file via Vite ?url import
pdfjsLib.GlobalWorkerOptions.workerSrc = new URL(
  'pdfjs-dist/legacy/build/pdf.worker.min.mjs',
  import.meta.url
).href

interface Props {
  contractId: string
  highlights?: Array<{
    page: number
    bbox?: { x0: number; y0: number; x1: number; y1: number }
    risk_level?: string
    clause_title?: string
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

  return props.highlights
    .filter(h => h.page === currentPage.value - 1 && h.bbox)
    .map(h => {
      const bbox = h.bbox!
      return {
        ...h,
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
    scale.value = containerWidth / 595
    renderPage(currentPage.value)
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
  // Scroll highlight into view would need container scroll
  if (containerRef.value) {
    const y = bbox.y0 * scale.value
    containerRef.value.scrollTo({ top: y - 100, behavior: 'smooth' })
  }
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

defineExpose({ jumpToClause })
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
            fill-opacity="0.3"
            :stroke="getHighlightColor(h.risk_level)"
            stroke-width="2"
            class="cursor-pointer pointer-events-auto hover:fill-opacity-50 transition-all"
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
