<script setup lang="ts">
import { ref, computed, watch, onMounted, defineAsyncComponent } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  useContract,
  useReviewResult,
  useUpdateContractType,
  useClauseLocations,
} from '@/composables/useContracts'
import {
  ArrowLeft,
  Search,
  AlertTriangle,
  Edit,
  FileText,
  Sparkles,
  BookOpen,
  Loader2,
} from 'lucide-vue-next'
import {
  CONTRACT_TYPE_MAP,
  RISK_LEVEL_MAP,
  parseTextBlocks,
  formatDateShort,
  truncateText,
} from '@/lib/utils'
import { cn } from '@/lib/utils'
import PdfViewer from '@/components/PdfViewer.vue'

const ContractUnderstanding = defineAsyncComponent(() => import('@/components/contracts/ContractUnderstanding.vue'))

const route = useRoute()
const router = useRouter()
const id = computed(() => route.params.id as string)

const { data: contract, isLoading: contractLoading } = useContract(id.value)
const { data: review, isLoading: reviewLoading, isError: reviewError } = useReviewResult(id.value)
const { data: clauseLocations } = useClauseLocations(id.value)
const updateType = useUpdateContractType()
const pdfViewerRef = ref<InstanceType<typeof PdfViewer> | null>(null)

const activeTab = ref('review')
const editingType = ref(false)
const contractType = ref('')
const searchText = ref('')
const highlightedBlocks = ref<number[]>([])
const currentHighlightIndex = ref(-1)
const searchMatches = ref<number[]>([])
const blockRefs = ref<Record<number, HTMLElement | null>>({})
const textBlocks = computed(() => parseTextBlocks(contract.value?.content_text || ''))
const isPdfContract = computed(() => contract.value?.file_path?.toLowerCase()?.endsWith('.pdf'))

// Progress
const progress = ref(0)
const statusText = ref('准备中...')
let progressInterval: ReturnType<typeof setInterval> | null = null

onMounted(() => {
  if (contract.value?.review_status === 'pending' || contract.value?.review_status === 'processing') {
    startProgress()
  } else {
    progress.value = 100
  }
})

watch(() => contract.value?.review_status, (status) => {
  if (status === 'pending' || status === 'processing') {
    progress.value = 0
    startProgress()
  } else {
    progress.value = 100
    stopProgress()
  }
})

function startProgress() {
  stopProgress()
  progressInterval = setInterval(() => {
    progress.value = Math.min(progress.value + 2, 95)
    if (progress.value < 25) statusText.value = '正在解析合同文档...'
    else if (progress.value < 50) statusText.value = '正在检索相关法律法规...'
    else if (progress.value < 75) statusText.value = '正在分析合同条款...'
    else statusText.value = '正在生成审查报告...'
  }, 500)
}

function stopProgress() {
  if (progressInterval) clearInterval(progressInterval)
}

watch(contract, (c) => {
  if (c) contractType.value = c.contract_type || ''
}, { immediate: true })

watch(searchText, (val) => {
  if (!val.trim()) { searchMatches.value = []; return }
  const search = val.toLowerCase()
  searchMatches.value = textBlocks.value
    .map((b, i) => ({ b: b.toLowerCase(), i }))
    .filter(({ b }) => b.includes(search))
    .map(({ i }) => i)
})

function highlightClause(clause: { original_text?: string }) {
  if (!clause.original_text || !textBlocks.value.length) return
  const search = clause.original_text.toLowerCase()
  const matched: number[] = []
  textBlocks.value.forEach((block, idx) => {
    const b = block.toLowerCase()
    if (b.includes(search) || search.includes(b)) matched.push(idx)
  })
  if (matched.length === 0) {
    const keywords = search.split(/[，。、；：""''（）]/).filter((k) => k.length > 5)
    keywords.forEach((kw) => {
      textBlocks.value.forEach((block, idx) => {
        if (block.toLowerCase().includes(kw) && !matched.includes(idx)) matched.push(idx)
      })
    })
  }
  if (matched.length > 0) {
    highlightedBlocks.value = matched
    currentHighlightIndex.value = matched[0]
    setTimeout(() => blockRefs.value[matched[0]]?.scrollIntoView({ behavior: 'smooth', block: 'center' }), 50)
  }
}

// Highlight clause in PDF viewer (for PDF contracts)
function highlightPdfClause(clause: { original_text?: string }) {
  if (!clauseLocations?.value?.length || !clauseLocations.value[0]) return

  // Find matching clause location by text similarity
  if (clause.original_text) {
    const search = clause.original_text.toLowerCase()
    const match = clauseLocations.value.find(loc =>
      loc.clause_text?.toLowerCase().includes(search.slice(0, 50)) ||
      search.includes(loc.clause_text?.toLowerCase().slice(0, 50) || '')
    )
    if (match && match.page !== undefined && match.bbox) {
      pdfViewerRef.value?.jumpToClause(match.page, match.bbox)
      return
    }
  }

  // Fallback: highlight first matching clause
  if (clauseLocations.value[0] && clauseLocations.value[0].page !== undefined) {
    const loc = clauseLocations.value[0]
    if (loc.bbox) {
      pdfViewerRef.value?.jumpToClause(loc.page, loc.bbox)
    }
  }
}

function handleBlockClick(idx: number) {
  currentHighlightIndex.value = idx
}

async function updateContractType(newType: string) {
  if (!contract.value) return
  try {
    await updateType.mutateAsync({ id: contract.value.id, contractType: newType })
    contractType.value = newType
    editingType.value = false
  } catch {}
}

function getTypeVariant(type: string) {
  return (CONTRACT_TYPE_MAP[type]?.variant || 'secondary') as 'primary' | 'success' | 'warning' | 'destructive' | 'info' | 'secondary' | 'outline' | 'ghost' | 'default'
}

function getRiskVariant(level?: string) {
  if (!level) return 'secondary'
  return (RISK_LEVEL_MAP[level]?.variant || 'secondary') as 'primary' | 'success' | 'warning' | 'destructive' | 'info' | 'secondary' | 'outline' | 'ghost' | 'default'
}

function scrollToSection(sectionId: string) {
  window.document.getElementById(sectionId)?.scrollIntoView({ behavior: 'smooth' })
}

const CONTRACT_TYPE_OPTIONS = ['NDA', '劳动合同', '采购合同', '销售合同', '服务合同', '租赁合同', '借款合同', '投资合同', '合作协议', '其他']
</script>

<template>
  <div class="flex flex-col h-full">
    <!-- Header -->
    <div class="flex items-center justify-between px-6 py-4 bg-card border-b border-border">
      <div class="flex items-center gap-3">
        <UiButton variant="ghost" size="icon" @click="router.push('/workspace/contracts')">
          <ArrowLeft class="w-4 h-4" />
        </UiButton>
        <h1 class="text-lg font-semibold">审查报告</h1>
      </div>
      <div class="flex items-center gap-3">
        <template v-if="editingType">
          <UiSelect v-model="contractType" class="w-[160px]">
            <UiSelectItem v-for="t in CONTRACT_TYPE_OPTIONS" :key="t" :value="t">{{ t }}</UiSelectItem>
          </UiSelect>
          <UiButton size="sm" @click="updateContractType(contractType)">确认</UiButton>
        </template>
        <template v-else>
          <UiBadge :variant="getTypeVariant(contractType)" class="cursor-pointer" @click="editingType = true">
            {{ CONTRACT_TYPE_MAP[contractType]?.label || contractType || '点击设置类型' }}
          </UiBadge>
          <span class="text-sm text-muted-foreground">{{ formatDateShort(contract?.created_at) }}</span>
        </template>
      </div>
    </div>

    <!-- Loading -->
    <div v-if="contractLoading" class="flex-1 flex items-center justify-center">
      <div class="text-center">
        <Loader2 class="w-8 h-8 animate-spin mx-auto mb-4 text-primary-600" />
        <p class="text-muted-foreground">加载中...</p>
      </div>
    </div>

    <!-- Review In Progress -->
    <div v-else-if="contract?.review_status === 'pending' || contract?.review_status === 'processing'" class="flex-1 flex items-center justify-center">
      <UiCard class="w-full max-w-md">
        <UiCardContent class="py-12 text-center">
          <div class="w-16 h-16 bg-primary-50 rounded-full flex items-center justify-center mx-auto mb-4">
            <FileText class="w-8 h-8 text-primary-600" />
          </div>
          <h2 class="text-lg font-semibold mb-2">正在审查合同</h2>
          <p class="text-sm text-muted-foreground mb-6">这可能需要 30-60 秒，请耐心等待...</p>
          <UiProgress :modelValue="progress" class="mb-2" />
          <p class="text-xs text-muted-foreground">{{ statusText }}</p>
        </UiCardContent>
      </UiCard>
    </div>

    <!-- Error -->
    <div v-else-if="reviewError || contract?.review_status === 'failed'" class="flex-1 flex items-center justify-center">
      <UiCard class="w-full max-w-md">
        <UiCardContent class="py-12 text-center">
          <div class="w-16 h-16 bg-danger-50 rounded-full flex items-center justify-center mx-auto mb-4">
            <AlertTriangle class="w-8 h-8 text-danger-500" />
          </div>
          <h2 class="text-lg font-semibold mb-2">审查失败</h2>
          <p class="text-sm text-muted-foreground mb-6">{{ contract?.review_error || '审查过程中出现错误' }}</p>
          <UiButton @click="router.push('/workspace/contracts')">返回合同列表</UiButton>
        </UiCardContent>
      </UiCard>
    </div>

    <!-- Main Content -->
    <div v-else class="flex-1 flex flex-col overflow-hidden">
      <!-- Contract Info Bar -->
      <div class="px-6 py-3 bg-card border-b border-border flex items-center gap-6">
        <h2 class="text-base font-medium">{{ contract?.file_name }}</h2>
        <div class="flex items-center gap-4 text-sm text-muted-foreground">
          <span v-if="contract?.content_text">约 {{ Math.round((contract.content_text.length || 0) / 500) }} 页</span>
          <span v-if="review?.confidence_score">置信度: {{ Math.round(review.confidence_score * 100) }}%</span>
        </div>
      </div>

      <!-- Tabs -->
      <UiTabs v-model="activeTab" class="flex-1 flex flex-col overflow-hidden">
        <div class="px-6 bg-card border-b border-border">
          <UiTabsList>
            <UiTabsTrigger value="review" class="gap-2">
              <FileText class="w-4 h-4" />
              审查报告
            </UiTabsTrigger>
            <UiTabsTrigger value="understanding" class="gap-2">
              <Sparkles class="w-4 h-4" />
              合同理解
            </UiTabsTrigger>
            <UiTabsTrigger value="original" class="gap-2">
              <BookOpen class="w-4 h-4" />
              合同原文
            </UiTabsTrigger>
          </UiTabsList>
        </div>

        <!-- Tab: Review -->
        <UiTabsContent value="review" class="flex-1 overflow-hidden flex flex-col">
          <div v-if="isPdfContract" class="flex-1 flex overflow-hidden">
            <!-- Left: PDF Viewer -->
            <div class="flex-1 flex flex-col bg-card border-r border-border overflow-hidden">
              <PdfViewer
                ref="pdfViewerRef"
                :contract-id="id"
                :highlights="clauseLocations || []"
              />
            </div>

            <!-- Right: Review Results -->
            <div class="w-[420px] flex-shrink-0 overflow-y-auto p-4 bg-muted/50 space-y-4">
              <!-- Stats -->
              <div class="grid grid-cols-2 gap-3">
                <div
                  class="bg-card rounded-lg p-4 border border-border cursor-pointer hover:shadow-sm transition-shadow"
                  @click="scrollToSection('risk-section')"
                >
                  <div class="flex items-center gap-3">
                    <div class="w-8 h-8 bg-danger-50 rounded-lg flex items-center justify-center">
                      <AlertTriangle class="w-4 h-4 text-danger-500" />
                    </div>
                    <div>
                      <p class="text-xl font-bold">{{ review?.risk_clauses?.length || 0 }}</p>
                      <p class="text-xs text-muted-foreground">风险条款</p>
                    </div>
                  </div>
                </div>
                <div
                  class="bg-card rounded-lg p-4 border border-border cursor-pointer hover:shadow-sm transition-shadow"
                  @click="scrollToSection('missing-section')"
                >
                  <div class="flex items-center gap-3">
                    <div class="w-8 h-8 bg-warning-50 rounded-lg flex items-center justify-center">
                      <AlertTriangle class="w-4 h-4 text-warning-500" />
                    </div>
                    <div>
                      <p class="text-xl font-bold">{{ review?.missing_clauses?.length || 0 }}</p>
                      <p class="text-xs text-muted-foreground">缺失条款</p>
                    </div>
                  </div>
                </div>
              </div>

              <!-- Risk Clauses -->
              <div v-if="review?.risk_clauses?.length" id="risk-section" class="bg-card rounded-lg p-4 border border-border">
                <h4 class="text-sm font-semibold flex items-center gap-2 mb-3">
                  <AlertTriangle class="w-4 h-4 text-danger-500" />
                  风险条款
                </h4>
                <div class="space-y-2">
                  <div
                    v-for="(clause, idx) in review.risk_clauses"
                    :key="idx"
                    class="p-3 rounded-md border-l-[3px] bg-muted/50 cursor-pointer hover:translate-x-0.5 transition-all"
                    :style="{ borderLeftColor: RISK_LEVEL_MAP[clause.risk_level || 'medium']?.color }"
                    @click="highlightPdfClause(clause)"
                  >
                    <div class="flex items-start justify-between gap-2 mb-1">
                      <span class="text-sm font-medium">{{ clause.title || `风险条款 ${idx + 1}` }}</span>
                      <UiBadge :variant="getRiskVariant(clause.risk_level)" class="flex-shrink-0">
                        {{ RISK_LEVEL_MAP[clause.risk_level || 'medium']?.label }}
                      </UiBadge>
                    </div>
                    <p v-if="clause.original_text" class="text-xs text-muted-foreground italic mb-1">
                      "{{ truncateText(clause.original_text, 60) }}"
                    </p>
                    <p v-if="clause.risk_description" class="text-xs">{{ clause.risk_description }}</p>
                  </div>
                </div>
              </div>

              <!-- Missing Clauses -->
              <div v-if="review?.missing_clauses?.length" id="missing-section" class="bg-card rounded-lg p-4 border border-border">
                <h4 class="text-sm font-semibold flex items-center gap-2 mb-3">
                  <AlertTriangle class="w-4 h-4 text-warning-500" />
                  缺失条款
                </h4>
                <div class="space-y-2">
                  <div v-for="(clause, idx) in review.missing_clauses" :key="idx" class="p-3 rounded-md border-l-[3px] border-l-warning-500 bg-muted/50">
                    <div class="flex items-start justify-between gap-2 mb-1">
                      <span class="text-sm font-medium">{{ clause.title }}</span>
                      <UiBadge variant="warning" class="flex-shrink-0">缺失</UiBadge>
                    </div>
                    <p v-if="clause.description" class="text-xs mb-1">{{ clause.description }}</p>
                    <p v-if="clause.suggestion" class="text-xs text-muted-foreground"><strong>建议：</strong>{{ clause.suggestion }}</p>
                  </div>
                </div>
              </div>

              <!-- Suggestions -->
              <div v-if="review?.suggestions?.length" class="bg-card rounded-lg p-4 border border-border">
                <h4 class="text-sm font-semibold flex items-center gap-2 mb-3">
                  <Edit class="w-4 h-4 text-purple-500" />
                  修改建议
                </h4>
                <div class="space-y-2">
                  <div v-for="(s, idx) in review.suggestions" :key="idx" class="p-3 rounded-md border-l-[3px] border-l-purple-500 bg-muted/50">
                    <span class="text-sm font-medium">{{ s.title }}</span>
                    <p v-if="s.content" class="text-xs text-muted-foreground mt-1">{{ s.content }}</p>
                  </div>
                </div>
              </div>
            </div>
          </div>
          <div v-else class="flex-1 flex overflow-hidden">
            <!-- Left: Original Text -->
            <div class="flex-1 flex flex-col bg-card border-r border-border overflow-hidden">
              <div class="px-4 py-3 border-b border-border flex items-center justify-between">
                <h3 class="text-sm font-medium">合同原文</h3>
                <div class="relative">
                  <Search class="absolute left-2.5 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-muted-foreground" />
                  <input
                    v-model="searchText"
                    type="text"
                    placeholder="搜索..."
                    class="pl-8 pr-3 py-1 text-sm border border-input rounded-md w-48 focus:outline-none focus:ring-1 focus:ring-ring"
                  />
                </div>
              </div>
              <div class="flex-1 overflow-y-auto p-4 space-y-1">
                <div
                  v-for="(block, idx) in textBlocks"
                  :key="idx"
                  :ref="(el) => { if (el) blockRefs[idx] = el as HTMLElement }"
                  @click="handleBlockClick(idx)"
                  :class="cn(
                    'flex gap-3 p-2 rounded-md cursor-pointer transition-colors border-l-[3px]',
                    highlightedBlocks.includes(idx) ? 'bg-danger-50 border-l-danger-500' : '',
                    searchMatches.includes(idx) && !highlightedBlocks.includes(idx) ? 'bg-warning-50 border-l-warning-500' : '',
                    currentHighlightIndex === idx && !highlightedBlocks.includes(idx) ? 'bg-accent border-l-muted-foreground' : '',
                    !highlightedBlocks.includes(idx) && !searchMatches.includes(idx) && currentHighlightIndex !== idx ? 'border-l-transparent hover:bg-accent' : '',
                  )"
                >
                  <span class="flex-shrink-0 w-6 h-6 bg-muted rounded-full flex items-center justify-center text-xs text-muted-foreground">
                    {{ idx + 1 }}
                  </span>
                  <p class="text-sm whitespace-pre-wrap leading-relaxed">{{ block }}</p>
                </div>
              </div>
            </div>

            <!-- Right: Review Results -->
            <div class="w-[420px] flex-shrink-0 overflow-y-auto p-4 bg-muted/50 space-y-4">
              <!-- Stats -->
              <div class="grid grid-cols-2 gap-3">
                <div
                  class="bg-card rounded-lg p-4 border border-border cursor-pointer hover:shadow-sm transition-shadow"
                  @click="scrollToSection('risk-section')"
                >
                  <div class="flex items-center gap-3">
                    <div class="w-8 h-8 bg-danger-50 rounded-lg flex items-center justify-center">
                      <AlertTriangle class="w-4 h-4 text-danger-500" />
                    </div>
                    <div>
                      <p class="text-xl font-bold">{{ review?.risk_clauses?.length || 0 }}</p>
                      <p class="text-xs text-muted-foreground">风险条款</p>
                    </div>
                  </div>
                </div>
                <div
                  class="bg-card rounded-lg p-4 border border-border cursor-pointer hover:shadow-sm transition-shadow"
                  @click="scrollToSection('missing-section')"
                >
                  <div class="flex items-center gap-3">
                    <div class="w-8 h-8 bg-warning-50 rounded-lg flex items-center justify-center">
                      <AlertTriangle class="w-4 h-4 text-warning-500" />
                    </div>
                    <div>
                      <p class="text-xl font-bold">{{ review?.missing_clauses?.length || 0 }}</p>
                      <p class="text-xs text-muted-foreground">缺失条款</p>
                    </div>
                  </div>
                </div>
              </div>

              <!-- Risk Clauses -->
              <div v-if="review?.risk_clauses?.length" id="risk-section" class="bg-card rounded-lg p-4 border border-border">
                <h4 class="text-sm font-semibold flex items-center gap-2 mb-3">
                  <AlertTriangle class="w-4 h-4 text-danger-500" />
                  风险条款
                </h4>
                <div class="space-y-2">
                  <div
                    v-for="(clause, idx) in review.risk_clauses"
                    :key="idx"
                    class="p-3 rounded-md border-l-[3px] bg-muted/50 cursor-pointer hover:translate-x-0.5 transition-all"
                    :style="{ borderLeftColor: RISK_LEVEL_MAP[clause.risk_level || 'medium']?.color }"
                    @click="highlightClause(clause)"
                  >
                    <div class="flex items-start justify-between gap-2 mb-1">
                      <span class="text-sm font-medium">{{ clause.title || `风险条款 ${idx + 1}` }}</span>
                      <UiBadge :variant="getRiskVariant(clause.risk_level)" class="flex-shrink-0">
                        {{ RISK_LEVEL_MAP[clause.risk_level || 'medium']?.label }}
                      </UiBadge>
                    </div>
                    <p v-if="clause.original_text" class="text-xs text-muted-foreground italic mb-1">
                      "{{ truncateText(clause.original_text, 60) }}"
                    </p>
                    <p v-if="clause.risk_description" class="text-xs">{{ clause.risk_description }}</p>
                  </div>
                </div>
              </div>

              <!-- Missing Clauses -->
              <div v-if="review?.missing_clauses?.length" id="missing-section" class="bg-card rounded-lg p-4 border border-border">
                <h4 class="text-sm font-semibold flex items-center gap-2 mb-3">
                  <AlertTriangle class="w-4 h-4 text-warning-500" />
                  缺失条款
                </h4>
                <div class="space-y-2">
                  <div v-for="(clause, idx) in review.missing_clauses" :key="idx" class="p-3 rounded-md border-l-[3px] border-l-warning-500 bg-muted/50">
                    <div class="flex items-start justify-between gap-2 mb-1">
                      <span class="text-sm font-medium">{{ clause.title }}</span>
                      <UiBadge variant="warning" class="flex-shrink-0">缺失</UiBadge>
                    </div>
                    <p v-if="clause.description" class="text-xs mb-1">{{ clause.description }}</p>
                    <p v-if="clause.suggestion" class="text-xs text-muted-foreground"><strong>建议：</strong>{{ clause.suggestion }}</p>
                  </div>
                </div>
              </div>

              <!-- Suggestions -->
              <div v-if="review?.suggestions?.length" class="bg-card rounded-lg p-4 border border-border">
                <h4 class="text-sm font-semibold flex items-center gap-2 mb-3">
                  <Edit class="w-4 h-4 text-purple-500" />
                  修改建议
                </h4>
                <div class="space-y-2">
                  <div v-for="(s, idx) in review.suggestions" :key="idx" class="p-3 rounded-md border-l-[3px] border-l-purple-500 bg-muted/50">
                    <span class="text-sm font-medium">{{ s.title }}</span>
                    <p v-if="s.content" class="text-xs text-muted-foreground mt-1">{{ s.content }}</p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </UiTabsContent>

        <!-- Tab: Understanding -->
        <UiTabsContent value="understanding" class="flex-1 overflow-y-auto p-6 bg-muted/30">
          <ContractUnderstanding :contract-id="id" />
        </UiTabsContent>

        <!-- Tab: Original -->
        <UiTabsContent value="original" class="flex-1 overflow-hidden">
          <div class="flex-1 flex flex-col bg-card overflow-hidden">
            <div class="px-4 py-3 border-b border-border flex items-center justify-between">
              <h3 class="text-sm font-medium">合同原文</h3>
              <div class="relative">
                <Search class="absolute left-2.5 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-muted-foreground" />
                <input
                  v-model="searchText"
                  type="text"
                  placeholder="搜索..."
                  class="pl-8 pr-3 py-1 text-sm border border-input rounded-md w-48 focus:outline-none focus:ring-1 focus:ring-ring"
                />
              </div>
            </div>
            <div class="flex-1 overflow-y-auto p-4 space-y-1">
              <div
                v-for="(block, idx) in textBlocks"
                :key="idx"
                @click="handleBlockClick(idx)"
                :class="cn(
                  'flex gap-3 p-2 rounded-md cursor-pointer transition-colors border-l-[3px]',
                  searchMatches.includes(idx) ? 'bg-warning-50 border-l-warning-500' : '',
                  currentHighlightIndex === idx ? 'bg-accent border-l-muted-foreground' : '',
                  'border-l-transparent hover:bg-accent',
                )"
              >
                <span class="flex-shrink-0 w-6 h-6 bg-muted rounded-full flex items-center justify-center text-xs text-muted-foreground">
                  {{ idx + 1 }}
                </span>
                <p class="text-sm whitespace-pre-wrap leading-relaxed">{{ block }}</p>
              </div>
            </div>
          </div>
        </UiTabsContent>
      </UiTabs>
    </div>
  </div>
</template>
