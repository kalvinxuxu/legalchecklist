<script setup lang="ts">
import { ref, computed, watch, defineAsyncComponent } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useQueryClient } from '@tanstack/vue-query'
import {
  useContract,
  useReviewStatus,
  useReviewResult,
  useUpdateContractType,
  useClauseLocations,
} from '@/composables/useContracts'
import { useDocumentIngestion } from '@/composables/useDocumentIngestion'
import { useExportReport, type ExportOptions, type ExportType } from '@/composables/useExportReport'
import {
  ArrowLeft,
  Search,
  AlertTriangle,
  Edit,
  FileText,
  Sparkles,
  BookOpen,
  Loader2,
  Shield,
  Download,
  Check,
  FileUp,
  FileSearch,
  FileOutput,
} from 'lucide-vue-next'
import {
  CONTRACT_TYPE_MAP,
  RISK_LEVEL_MAP,
  parseTextBlocks,
  formatDateShort,
  truncateText,
} from '@/lib/utils'
import { cn } from '@/lib/utils'
import api from '@/lib/api'
import { useToast } from '@/composables/useToast'
import { useReviewDelivery } from '@/composables/useReviewDelivery'
import PdfViewer from '@/components/PdfViewer.vue'
import RuleJudgment from '@/components/review/RuleJudgment.vue'
import ReviewConfig from '@/components/review/ReviewConfig.vue'

const ContractUnderstanding = defineAsyncComponent(() => import('@/components/contracts/ContractUnderstanding.vue'))

const route = useRoute()
const router = useRouter()
const id = computed(() => route.params.id as string)

const { data: contract, isLoading: contractLoading } = useContract(id.value)
const { data: reviewStatus } = useReviewStatus(id.value)
const { data: review, isLoading: reviewLoading, isError: reviewError } = useReviewResult(id.value)
// 只有当审查完成时才查询 clause-locations，避免 400 错误
const effectiveReviewStatus = computed(() => reviewStatus.value?.review_status || contract.value?.review_status)
const { data: clauseLocations } = useClauseLocations(id.value, computed(() => effectiveReviewStatus.value === 'completed'))
const { data: ingestionStatus } = useDocumentIngestion(id.value)
const updateType = useUpdateContractType()
const { exportReviewReport } = useExportReport()
const pdfViewerRef = ref<InstanceType<typeof PdfViewer> | null>(null)
const queryClient = useQueryClient()
const { toast } = useToast()
const { exportOpinion, exportOpinionDocx, saveEmailDraft, previewEmailDraft } = useReviewDelivery()
const showEmailDraftDialog = ref(false)
const savingEmailDraft = ref(false)
const loadingEmailDraft = ref(false)
const emailDraftAttachments = ref<Array<{ filename: string; content_type: string }>>([])
const emailDraft = ref({ from_email: 'kalvinxuxu@qq.com', to: '', subject: '合同审查意见', body: '', idempotency_key: crypto.randomUUID() })

// 导出对话框
const showExportDialog = ref(false)
const exportType = ref<ExportType>('review_report')
const exportOptions = ref<ExportOptions>({
  export_type: 'review_report',
  include_risk_clauses: true,
  include_missing_clauses: true,
  include_suggestions: true,
  include_rule_judgments: true,
  include_policy_references: true,
})

// 流程阶段定义
type ReviewPhase = 'archived' | 'reviewing' | 'report'

// 当前流程阶段
const currentPhase = computed<ReviewPhase>(() => {
  if (!contract.value) return 'archived'
  const status = effectiveReviewStatus.value
  if (status === 'pending') return 'archived'
  if (status === 'processing') return 'reviewing'
  return 'report'
})

// 步骤状态
const stepStatus = computed(() => ({
  upload: 'completed', // 上传已完成（合同已存档）
  review: currentPhase.value === 'archived' ? 'pending' : currentPhase.value === 'reviewing' ? 'active' : 'completed',
  report: currentPhase.value === 'report' ? 'active' : currentPhase.value === 'archived' || currentPhase.value === 'reviewing' ? 'pending' : 'completed',
}))

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

// 审查立场配置
const showConfigDialog = ref(false)
const reviewConfig = ref<{
  party_position?: string | null
  contract_amount?: number | null
  risk_preference?: string | null
}>({})

// Progress
const progress = computed(() => reviewStatus.value?.progress ?? (effectiveReviewStatus.value === 'completed' ? 100 : 0))
const statusText = computed(() => reviewStatus.value?.stage_label || '等待任务队列...')
const isStalled = computed(() => reviewStatus.value?.status === 'stalled')

watch(contract, (c) => {
  if (c) contractType.value = c.contract_type || ''
}, { immediate: true })

// 当 contract 可用时加载审查配置
watch(() => contract.value, (c) => {
  if (c) loadReviewConfig()
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
async function highlightPdfClause(clause: { original_text?: string; evidence_id?: string }) {
  if (clause.evidence_id && !clauseLocations?.value?.some(loc => loc.evidence_id === clause.evidence_id)) {
    try {
      const resolved = await api.get(`/contracts/${id.value}/evidence/${clause.evidence_id}`) as { locations?: Array<{ page: number; bbox?: { x0: number; y0: number; x1: number; y1: number } }> }
      const first = resolved.locations?.find(location => location.bbox)
      if (first?.bbox) {
        pdfViewerRef.value?.jumpToClause(first.page, first.bbox)
        return
      }
    } catch (error) {
      console.warn('Evidence lookup failed', error)
    }
  }
  if (!clauseLocations?.value?.length) {
    toast({ title: '无法定位原文', description: '当前没有可用的 PDF 证据位置，请重新生成审查结果。', variant: 'destructive' })
    return
  }
  const match = clause.evidence_id
    ? clauseLocations.value.find(loc => loc.evidence_id === clause.evidence_id)
    : clauseLocations.value.find(loc => loc.clause_text === clause.original_text)
  const first = match && clauseLocations.value.find(loc => loc.evidence_id === match.evidence_id && loc.bbox)
  if (first?.bbox) {
    if (clause.evidence_id) pdfViewerRef.value?.jumpToEvidence(clause.evidence_id)
    else pdfViewerRef.value?.jumpToClause(first.page, first.bbox)
    return
  }
  toast({ title: '无法定位原文', description: '该意见没有可解析的 PDF 证据位置，请人工核对。', variant: 'destructive' })
}

function highlightSuggestion(suggestion: { content?: string; evidence_id?: string }) {
  if (suggestion.evidence_id) {
    void highlightPdfClause(suggestion)
    return
  }
  const content = suggestion.content || ''
  const related = review.value?.risk_clauses?.find(clause =>
    clause.suggestion && (clause.suggestion.includes(content) || content.includes(clause.suggestion)),
  )
  if (related) void highlightPdfClause(related)
  else toast({ title: '无法定位原文', description: '该综合建议未关联到具体条款，请人工核对。', variant: 'destructive' })
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

// 加载审查立场配置
async function loadReviewConfig() {
  try {
    const res = await api.get(`/contracts/${id.value}/review-config`)
    reviewConfig.value = {
      party_position: res.party_position || null,
      contract_amount: res.contract_amount || null,
      risk_preference: res.risk_preference || null
    }
  } catch (e) {
    console.error('Failed to load review config:', e)
  }
}

// 保存审查立场配置并重新审查
async function saveReviewConfig() {
  try {
    await api.post(`/contracts/${id.value}/review-config`, reviewConfig.value)
    showConfigDialog.value = false
    // 触发重新审查
    await reReviewContract()
  } catch (e) {
    console.error('Failed to save review config:', e)
  }
}

// 开始审查（从 pending 状态触发）
async function startReview() {
  try {
    await api.post(`/contracts/${id.value}/review/start`)
    await queryClient.invalidateQueries({ queryKey: ['contracts', id.value] })
    await queryClient.invalidateQueries({ queryKey: ['contracts', id.value, 'review-status'] })
  } catch (e) {
    console.error('Failed to start review:', e)
    const error = e as { response?: { data?: { detail?: string } }; message?: string }
    toast({
      title: '启动审查失败',
      description: error.response?.data?.detail || error.message || '请稍后重试',
      variant: 'destructive',
    })
  }
}

// 重新审查合同（已审查过的合同重新审查）
async function reReviewContract() {
  try {
    await api.post(`/contracts/${id.value}/rerun-review`)
    await queryClient.invalidateQueries({ queryKey: ['contracts', id.value] })
    await queryClient.invalidateQueries({ queryKey: ['contracts', id.value, 'review-status'] })
  } catch (e) {
    console.error('Failed to re-review contract:', e)
  }
}

async function resumeReview() {
  try {
    await api.post(`/contracts/${id.value}/review/resume`)
    await queryClient.invalidateQueries({ queryKey: ['contracts', id.value] })
    await queryClient.invalidateQueries({ queryKey: ['contracts', id.value, 'review-status'] })
  } catch (e) {
    console.error('Failed to resume review:', e)
  }
}

// 打开配置对话框
function openConfigDialog() {
  loadReviewConfig()
  showConfigDialog.value = true
}

// 打开导出对话框
function openExportDialog() {
  showExportDialog.value = true
}

async function openEmailDraftDialog() {
  if (!contract.value) return
  showEmailDraftDialog.value = true
  loadingEmailDraft.value = true
  try {
    const preview = await previewEmailDraft(contract.value.id)
    emailDraft.value.from_email = preview.from
    emailDraft.value.subject = preview.subject
    emailDraft.value.body = preview.body_text
    emailDraftAttachments.value = preview.attachments
  } catch (error: any) {
    toast({ title: '邮件草稿生成失败', description: error?.message || '请检查审查结果或后端服务', variant: 'destructive' })
  } finally {
    loadingEmailDraft.value = false
  }
}

async function submitEmailDraft() {
  if (!contract.value) return
  const recipients = emailDraft.value.to.split(',').map(item => item.trim()).filter(Boolean)
  if (!recipients.length) {
    toast({ title: '无法保存草稿', description: '请至少填写一个收件人', variant: 'destructive' })
    return
  }
  savingEmailDraft.value = true
  try {
    const result = await saveEmailDraft(contract.value.id, { ...emailDraft.value, to: recipients, body_text: emailDraft.value.body })
    if (result.sync_status === 'sync_failed') {
      toast({ title: 'QQ 邮箱草稿同步失败', description: result.last_error || '已保存在本地，可配置 QQ 邮箱授权码后重试', variant: 'destructive' })
      return
    }
    showEmailDraftDialog.value = false
  } catch (error: any) {
    toast({ title: '邮件草稿保存失败', description: error?.message || '请检查后端服务是否正常运行', variant: 'destructive' })
  } finally {
    savingEmailDraft.value = false
  }
}

async function downloadOpinion() {
  if (contract.value) await exportOpinion(contract.value.id, contract.value.file_name)
}

async function downloadOpinionDocx() {
  if (contract.value) await exportOpinionDocx(contract.value.id, contract.value.file_name)
}

// 确认导出
async function confirmExport() {
  if (!contract.value) return
  showExportDialog.value = false
  const options = {
    ...exportOptions.value,
    export_type: exportType.value,
  }
  // 生成文件名
  let filename: string | undefined
  if (exportType.value === 'original_with_comments') {
    filename = `批注版_${contract.value.file_name}`
  }
  await exportReviewReport(contract.value.id, options, filename)
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

      <!-- 流程步骤指示器 -->
      <div class="flex items-center gap-2">
        <!-- 步骤1: 上传合同 -->
        <div class="flex items-center gap-1.5">
          <div :class="[
            'w-6 h-6 rounded-full flex items-center justify-center text-xs font-medium',
            stepStatus.upload === 'completed' ? 'bg-green-500 text-white' : 'bg-muted text-muted-foreground'
          ]">
            <Check v-if="stepStatus.upload === 'completed'" class="w-3.5 h-3.5" />
            <span v-else>1</span>
          </div>
          <span :class="['text-xs', stepStatus.upload === 'completed' ? 'text-green-600' : 'text-muted-foreground']">
            上传合同
          </span>
        </div>

        <div class="w-6 h-px bg-border" />

        <!-- 步骤2: 开始审查 -->
        <div class="flex items-center gap-1.5">
          <div :class="[
            'w-6 h-6 rounded-full flex items-center justify-center text-xs font-medium',
            stepStatus.review === 'completed' ? 'bg-green-500 text-white' :
            stepStatus.review === 'active' ? 'bg-primary text-primary-foreground animate-pulse' :
            'bg-muted text-muted-foreground'
          ]">
            <Check v-if="stepStatus.review === 'completed'" class="w-3.5 h-3.5" />
            <Loader2 v-else-if="stepStatus.review === 'active'" class="w-3.5 h-3.5 animate-spin" />
            <span v-else>2</span>
          </div>
          <span :class="['text-xs', stepStatus.review === 'completed' ? 'text-green-600' :
            stepStatus.review === 'active' ? 'text-primary font-medium' : 'text-muted-foreground']">
            开始审查
          </span>
        </div>

        <div class="w-6 h-px bg-border" />

        <!-- 步骤3: 生成报告 -->
        <div class="flex items-center gap-1.5">
          <div :class="[
            'w-6 h-6 rounded-full flex items-center justify-center text-xs font-medium',
            stepStatus.report === 'completed' ? 'bg-green-500 text-white' :
            stepStatus.report === 'active' ? 'bg-primary text-primary-foreground animate-pulse' :
            'bg-muted text-muted-foreground'
          ]">
            <Check v-if="stepStatus.report === 'completed'" class="w-3.5 h-3.5" />
            <Loader2 v-else-if="stepStatus.report === 'active'" class="w-3.5 h-3.5 animate-spin" />
            <span v-else>3</span>
          </div>
          <span :class="['text-xs', stepStatus.report === 'completed' ? 'text-green-600' :
            stepStatus.report === 'active' ? 'text-primary font-medium' : 'text-muted-foreground']">
            生成报告
          </span>
        </div>
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
        <!-- 审查立场配置按钮 -->
        <UiButton variant="outline" size="sm" @click="openConfigDialog">
          <Shield class="w-3.5 h-3.5 mr-1" />
          审查立场
        </UiButton>
        <UiButton variant="outline" size="sm" :disabled="currentPhase !== 'report'" @click="downloadOpinion">
          导出意见
        </UiButton>
        <UiButton variant="outline" size="sm" :disabled="currentPhase !== 'report'" @click="downloadOpinionDocx">
          导出 Word
        </UiButton>
        <UiButton variant="outline" size="sm" :disabled="currentPhase !== 'report'" @click="openEmailDraftDialog">
          存邮件草稿
        </UiButton>
      </div>
    </div>
    <div v-if="ingestionStatus?.status === 'failed' || ingestionStatus?.warnings?.length" class="px-6 py-2 text-xs bg-amber-50 text-amber-800 border-b border-amber-200">
      文档解析存在降级或警告；部分证据可能仅支持页级定位。
    </div>
    <div v-if="review?.retrieval_diagnostics" class="px-6 py-2 text-xs bg-blue-50 text-blue-800 border-b border-blue-200">
      RAG：{{ review.retrieval_diagnostics.modes?.join(' + ') }} · 候选 {{ review.retrieval_diagnostics.candidate_count }} 条 · 已执行 Rerank
    </div>

    <!-- Loading -->
    <div v-if="contractLoading" class="flex-1 flex items-center justify-center">
      <div class="text-center">
        <Loader2 class="w-8 h-8 animate-spin mx-auto mb-4 text-primary-600" />
        <p class="text-muted-foreground">加载中...</p>
      </div>
    </div>

    <!-- Review In Progress -->
    <div v-else-if="effectiveReviewStatus === 'processing'" class="flex-1 flex items-center justify-center">
      <UiCard class="w-full max-w-lg">
        <UiCardContent class="py-10 text-center">
          <div class="w-16 h-16 bg-primary-50 rounded-full flex items-center justify-center mx-auto mb-4">
            <Loader2 class="w-8 h-8 text-primary-600 animate-spin" />
          </div>
          <h2 class="text-lg font-semibold mb-2">正在审查合同</h2>
          <p class="text-sm text-muted-foreground mb-2">AI 正在{{ statusText }}，状态会自动保存，可在中断后继续。</p>
          <p v-if="reviewStatus?.last_heartbeat_at" class="text-xs text-muted-foreground mb-6">
            最近心跳：{{ formatDateShort(reviewStatus.last_heartbeat_at) }} · 已运行 {{ Math.floor((reviewStatus.elapsed_seconds || 0) / 60) }} 分钟
          </p>
          <p v-else class="text-xs text-muted-foreground mb-6">任务正在等待审查 Worker 接管...</p>
          <UiProgress :modelValue="progress" class="mb-3" />
          <p class="text-xs text-muted-foreground">{{ Math.round(progress) }}% · 第 {{ reviewStatus?.attempt || 0 }} 次任务尝试</p>

          <!-- 进度子步骤 -->
          <div class="mt-6 pt-6 border-t border-border">
            <div class="grid grid-cols-2 gap-3 text-xs text-muted-foreground text-left">
              <div v-for="step in (reviewStatus?.steps || [])" :key="step.stage" class="flex items-center gap-2">
                <div :class="[
                  'w-2.5 h-2.5 rounded-full',
                  step.status === 'completed' ? 'bg-green-500' : step.status === 'running' ? 'bg-primary animate-pulse' : step.status === 'failed' ? 'bg-danger-500' : 'bg-muted'
                ]" />
                <span>{{ step.stage_label || step.stage }}</span>
                <span v-if="step.attempt > 1" class="text-[10px]">×{{ step.attempt }}</span>
              </div>
            </div>
            <div v-if="isStalled || reviewStatus?.status === 'failed'" class="mt-5 pt-4 border-t border-border text-left">
              <p class="text-sm text-danger-600 mb-3">{{ reviewStatus?.last_error || '任务可能已中断' }}</p>
              <UiButton @click="resumeReview" size="sm">从断点继续</UiButton>
            </div>
          </div>
        </UiCardContent>
      </UiCard>
    </div>

    <!-- Pending: Waiting for Review -->
    <div v-else-if="effectiveReviewStatus === 'pending'" class="flex-1 flex items-center justify-center">
      <UiCard class="w-full max-w-lg">
        <UiCardContent class="py-10 text-center">
          <!-- 完成步骤回顾 -->
          <div class="flex justify-center gap-8 mb-6 pb-6 border-b border-border">
            <div class="flex flex-col items-center gap-1.5">
              <div class="w-10 h-10 rounded-full bg-green-500 text-white flex items-center justify-center">
                <Check class="w-5 h-5" />
              </div>
              <span class="text-xs text-green-600 font-medium">上传合同</span>
            </div>
            <div class="flex flex-col items-center gap-1.5">
              <div class="w-10 h-10 rounded-full bg-primary text-primary-foreground flex items-center justify-center">
                <FileSearch class="w-5 h-5" />
              </div>
              <span class="text-xs text-primary font-medium">开始审查</span>
            </div>
            <div class="flex flex-col items-center gap-1.5">
              <div class="w-10 h-10 rounded-full bg-muted text-muted-foreground flex items-center justify-center">
                <FileOutput class="w-5 h-5" />
              </div>
              <span class="text-xs text-muted-foreground">生成报告</span>
            </div>
          </div>

          <h2 class="text-lg font-semibold mb-2">
            {{ reviewStatus?.status === 'queued' ? '审查任务已排队' : '合同已存档，正在等待审查' }}
          </h2>
          <p class="text-sm text-muted-foreground mb-6">
            配置的审查立场：{{ reviewConfig.party_position === 'party_a' ? '甲方' : '乙方' }} ·
            {{ reviewConfig.risk_preference === 'low' ? '低风险' : reviewConfig.risk_preference === 'medium' ? '中风险' : '高风险' }}偏好
          </p>
          <p v-if="reviewStatus?.status === 'queued'" class="text-sm text-primary mb-5">Worker 接管后会自动开始，页面会持续显示真实阶段。</p>
          <UiButton v-if="reviewStatus?.status !== 'queued'" @click="startReview" size="lg" class="px-8">
            <Sparkles class="w-4 h-4 mr-2" />
            开始 AI 审查
          </UiButton>
        </UiCardContent>
      </UiCard>
    </div>

    <!-- Error -->
    <div v-else-if="reviewError || effectiveReviewStatus === 'failed'" class="flex-1 flex items-center justify-center">
      <UiCard class="w-full max-w-md">
        <UiCardContent class="py-12 text-center">
          <div class="w-16 h-16 bg-danger-50 rounded-full flex items-center justify-center mx-auto mb-4">
            <AlertTriangle class="w-8 h-8 text-danger-500" />
          </div>
          <h2 class="text-lg font-semibold mb-2">审查失败</h2>
          <p class="text-sm text-muted-foreground mb-6">{{ reviewStatus?.last_error || contract?.review_error || '审查过程中出现错误' }}</p>
          <div class="flex justify-center gap-3">
            <UiButton @click="resumeReview">从断点继续</UiButton>
            <UiButton variant="outline" @click="router.push('/workspace/contracts')">返回合同列表</UiButton>
          </div>
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
          </UiTabsList>
        </div>

        <!-- Tab: Review -->
        <UiTabsContent v-if="activeTab === 'review'" value="review" class="flex-1 overflow-hidden flex flex-col">
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
              <!-- 规则判定结果 -->
              <RuleJudgment
                v-if="review"
                :rule-judgments="review.rule_judgments"
                :approval-flow="review.approval_flow"
                :approval-flow-description="review.approval_flow_description"
                :overall-risk-level="review.overall_risk_level"
              />

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
                <div class="space-y-3">
                  <div
                    v-for="(clause, idx) in review.risk_clauses"
                    :key="idx"
                    class="p-3 rounded-md border-l-[3px] bg-muted/30 cursor-pointer hover:bg-muted/50 transition-all"
                    :style="{ borderLeftColor: RISK_LEVEL_MAP[clause.risk_level || 'medium']?.color }"
                    @click="highlightPdfClause(clause)"
                  >
                    <div class="flex items-start justify-between gap-2 mb-2">
                      <span class="text-sm font-medium text-muted-foreground">{{ `风险条款 ${idx + 1}` }}</span>
                      <UiBadge :variant="getRiskVariant(clause.risk_level)" class="flex-shrink-0">
                        {{ RISK_LEVEL_MAP[clause.risk_level || 'medium']?.label }}
                      </UiBadge>
                    </div>
                    <!-- 风险说明 - 突出显示 -->
                    <div v-if="clause.risk_description" class="mb-2">
                      <span class="text-xs font-semibold text-danger-500">【风险说明】</span>
                      <p class="text-sm text-foreground mt-1 leading-relaxed">{{ clause.risk_description }}</p>
                    </div>
                    <!-- 修改建议 - 突出显示 -->
                    <div v-if="clause.suggestion" class="bg-primary-500/5 p-2 rounded border border-primary-500/20">
                      <span class="text-xs font-semibold text-primary-500">【修改建议】</span>
                      <p class="text-sm text-foreground mt-1 leading-relaxed">{{ clause.suggestion }}</p>
                    </div>
                  </div>
                </div>
              </div>

              <!-- Missing Clauses -->
              <div v-if="review?.missing_clauses?.length" id="missing-section" class="bg-card rounded-lg p-4 border border-border">
                <h4 class="text-sm font-semibold flex items-center gap-2 mb-3">
                  <AlertTriangle class="w-4 h-4 text-warning-500" />
                  缺失条款
                </h4>
                <div class="space-y-3">
                  <div v-for="(clause, idx) in review.missing_clauses" :key="idx" class="p-3 rounded-md border-l-[3px] border-l-warning-500 bg-muted/30">
                    <div class="flex items-start justify-between gap-2 mb-2">
                      <span class="text-sm font-medium text-muted-foreground">{{ `缺失条款 ${idx + 1}` }}</span>
                      <UiBadge variant="warning" class="flex-shrink-0">缺失</UiBadge>
                    </div>
                    <!-- 缺失说明 - 突出显示 -->
                    <div v-if="clause.description" class="mb-2">
                      <span class="text-xs font-semibold text-warning-500">【缺失说明】</span>
                      <p class="text-sm text-foreground mt-1 leading-relaxed">{{ clause.description }}</p>
                    </div>
                    <!-- 修改建议 - 突出显示 -->
                    <div v-if="clause.suggestion" class="bg-primary-500/5 p-2 rounded border border-primary-500/20">
                      <span class="text-xs font-semibold text-primary-500">【修改建议】</span>
                      <p class="text-sm text-foreground mt-1 leading-relaxed">{{ clause.suggestion }}</p>
                    </div>
                  </div>
                </div>
              </div>

              <!-- Policy References -->
              <div v-if="review?.policy_references?.length" class="bg-card rounded-lg p-4 border border-border">
                <h4 class="text-sm font-semibold flex items-center gap-2 mb-3">
                  <BookOpen class="w-4 h-4 text-primary-500" />
                  适用公司政策
                </h4>
                <div class="space-y-2">
                  <div
                    v-for="(policy, idx) in review.policy_references"
                    :key="idx"
                    class="p-3 rounded-md border-l-[3px] border-l-primary-500 bg-muted/50"
                  >
                    <p class="text-sm font-medium">{{ policy.policy_name }}</p>
                    <p v-if="policy.section" class="text-xs text-muted-foreground">{{ policy.section }}</p>
                    <p v-if="policy.content" class="text-xs mt-1">{{ policy.content }}</p>
                  </div>
                </div>
              </div>

              <!-- Suggestions -->
              <div v-if="review?.suggestions?.length" class="bg-card rounded-lg p-4 border border-border">
                <h4 class="text-sm font-semibold flex items-center gap-2 mb-3">
                  <Edit class="w-4 h-4 text-purple-500" />
                  修改建议
                </h4>
                <div class="space-y-3">
                  <div v-for="(s, idx) in review.suggestions" :key="idx" class="p-3 rounded-md border-l-[3px] border-l-purple-500 bg-muted/30 cursor-pointer hover:bg-muted/50" @click="highlightSuggestion(s)">
                    <div class="flex items-start justify-between gap-2 mb-2">
                      <span class="text-sm font-medium text-muted-foreground">{{ `建议 ${idx + 1}` }}</span>
                    </div>
                    <div v-if="s.content" class="bg-primary-500/5 p-2 rounded border border-primary-500/20">
                      <p class="text-sm text-foreground leading-relaxed">{{ s.content }}</p>
                    </div>
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
              <!-- 规则判定结果 -->
              <RuleJudgment
                v-if="review"
                :rule-judgments="review.rule_judgments"
                :approval-flow="review.approval_flow"
                :approval-flow-description="review.approval_flow_description"
                :overall-risk-level="review.overall_risk_level"
              />

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
                <div class="space-y-3">
                  <div
                    v-for="(clause, idx) in review.risk_clauses"
                    :key="idx"
                    class="p-3 rounded-md border-l-[3px] bg-muted/30 cursor-pointer hover:bg-muted/50 transition-all"
                    :style="{ borderLeftColor: RISK_LEVEL_MAP[clause.risk_level || 'medium']?.color }"
                    @click="highlightClause(clause)"
                  >
                    <div class="flex items-start justify-between gap-2 mb-2">
                      <span class="text-sm font-medium text-muted-foreground">{{ `风险条款 ${idx + 1}` }}</span>
                      <UiBadge :variant="getRiskVariant(clause.risk_level)" class="flex-shrink-0">
                        {{ RISK_LEVEL_MAP[clause.risk_level || 'medium']?.label }}
                      </UiBadge>
                    </div>
                    <!-- 风险说明 - 突出显示 -->
                    <div v-if="clause.risk_description" class="mb-2">
                      <span class="text-xs font-semibold text-danger-500">【风险说明】</span>
                      <p class="text-sm text-foreground mt-1 leading-relaxed">{{ clause.risk_description }}</p>
                    </div>
                    <!-- 修改建议 - 突出显示 -->
                    <div v-if="clause.suggestion" class="bg-primary-500/5 p-2 rounded border border-primary-500/20">
                      <span class="text-xs font-semibold text-primary-500">【修改建议】</span>
                      <p class="text-sm text-foreground mt-1 leading-relaxed">{{ clause.suggestion }}</p>
                    </div>
                  </div>
                </div>
              </div>

              <!-- Missing Clauses -->
              <div v-if="review?.missing_clauses?.length" id="missing-section" class="bg-card rounded-lg p-4 border border-border">
                <h4 class="text-sm font-semibold flex items-center gap-2 mb-3">
                  <AlertTriangle class="w-4 h-4 text-warning-500" />
                  缺失条款
                </h4>
                <div class="space-y-3">
                  <div v-for="(clause, idx) in review.missing_clauses" :key="idx" class="p-3 rounded-md border-l-[3px] border-l-warning-500 bg-muted/30">
                    <div class="flex items-start justify-between gap-2 mb-2">
                      <span class="text-sm font-medium text-muted-foreground">{{ `缺失条款 ${idx + 1}` }}</span>
                      <UiBadge variant="warning" class="flex-shrink-0">缺失</UiBadge>
                    </div>
                    <!-- 缺失说明 - 突出显示 -->
                    <div v-if="clause.description" class="mb-2">
                      <span class="text-xs font-semibold text-warning-500">【缺失说明】</span>
                      <p class="text-sm text-foreground mt-1 leading-relaxed">{{ clause.description }}</p>
                    </div>
                    <!-- 修改建议 - 突出显示 -->
                    <div v-if="clause.suggestion" class="bg-primary-500/5 p-2 rounded border border-primary-500/20">
                      <span class="text-xs font-semibold text-primary-500">【修改建议】</span>
                      <p class="text-sm text-foreground mt-1 leading-relaxed">{{ clause.suggestion }}</p>
                    </div>
                  </div>
                </div>
              </div>

              <!-- Policy References -->
              <div v-if="review?.policy_references?.length" class="bg-card rounded-lg p-4 border border-border">
                <h4 class="text-sm font-semibold flex items-center gap-2 mb-3">
                  <BookOpen class="w-4 h-4 text-primary-500" />
                  适用公司政策
                </h4>
                <div class="space-y-2">
                  <div
                    v-for="(policy, idx) in review.policy_references"
                    :key="idx"
                    class="p-3 rounded-md border-l-[3px] border-l-primary-500 bg-muted/50"
                  >
                    <p class="text-sm font-medium">{{ policy.policy_name }}</p>
                    <p v-if="policy.section" class="text-xs text-muted-foreground">{{ policy.section }}</p>
                    <p v-if="policy.content" class="text-xs mt-1">{{ policy.content }}</p>
                  </div>
                </div>
              </div>

              <!-- Suggestions -->
              <div v-if="review?.suggestions?.length" class="bg-card rounded-lg p-4 border border-border">
                <h4 class="text-sm font-semibold flex items-center gap-2 mb-3">
                  <Edit class="w-4 h-4 text-purple-500" />
                  修改建议
                </h4>
                <div class="space-y-3">
                  <div v-for="(s, idx) in review.suggestions" :key="idx" class="p-3 rounded-md border-l-[3px] border-l-purple-500 bg-muted/30 cursor-pointer hover:bg-muted/50" @click="highlightSuggestion(s)">
                    <div class="flex items-start justify-between gap-2 mb-2">
                      <span class="text-sm font-medium text-muted-foreground">{{ `建议 ${idx + 1}` }}</span>
                    </div>
                    <div v-if="s.content" class="bg-primary-500/5 p-2 rounded border border-primary-500/20">
                      <p class="text-sm text-foreground leading-relaxed">{{ s.content }}</p>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </UiTabsContent>

        <!-- Tab: Understanding -->
        <UiTabsContent v-if="activeTab === 'understanding'" value="understanding" class="flex-1 overflow-y-auto">
          <ContractUnderstanding :contract-id="id" />
        </UiTabsContent>
      </UiTabs>
    </div>

    <!-- 审查立场配置对话框 -->
    <div
      v-if="showConfigDialog"
      class="fixed inset-0 bg-black/50 flex items-center justify-center z-50"
      @click.self="showConfigDialog = false"
    >
      <div class="w-full max-w-md mx-4">
        <ReviewConfig
          v-model="reviewConfig"
          :show-description="true"
          @save="saveReviewConfig"
        />
        <UiButton
          variant="ghost"
          size="sm"
          class="mt-3 w-full"
          @click="showConfigDialog = false"
        >
          取消
        </UiButton>
      </div>
    </div>

    <!-- 邮件草稿对话框 -->
    <div v-if="showEmailDraftDialog" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50" @click.self="showEmailDraftDialog = false">
      <div class="bg-card rounded-lg shadow-lg w-full max-w-lg mx-4">
        <div class="p-6 border-b border-border"><h3 class="text-lg font-semibold">保存邮件草稿</h3><p class="text-sm text-muted-foreground mt-1">仅保存草稿，不会发送邮件</p></div>
        <div class="p-6 space-y-4">
          <label class="block text-sm font-medium">发件人</label>
          <input :value="emailDraft.from_email" readonly class="w-full rounded-md border border-border bg-muted px-3 py-2 text-sm" />
          <p class="text-xs text-muted-foreground">已连接 QQ 邮箱，仅保存为草稿，不会自动发送邮件。</p>
          <label class="block text-sm font-medium">收件人</label>
          <input v-model="emailDraft.to" class="w-full rounded-md border border-border bg-background px-3 py-2 text-sm" />
          <label class="block text-sm font-medium">主题</label>
          <input v-model="emailDraft.subject" class="w-full rounded-md border border-border bg-background px-3 py-2 text-sm" />
          <label class="block text-sm font-medium">正文</label>
          <textarea v-if="!loadingEmailDraft" v-model="emailDraft.body" rows="8" class="w-full rounded-md border border-border bg-background px-3 py-2 text-sm" />
          <div v-else class="rounded-md border border-border bg-muted px-3 py-6 text-sm text-muted-foreground">正在由公司法务 Agent 草拟邮件…</div>
          <div v-if="emailDraftAttachments.length" class="rounded-md border border-border bg-muted/50 px-3 py-2 text-sm">
            附件：{{ emailDraftAttachments.map(item => item.filename).join('、') }}
          </div>
        </div>
        <div class="p-6 border-t border-border flex justify-end gap-3"><UiButton variant="outline" @click="showEmailDraftDialog = false">取消</UiButton><UiButton :disabled="savingEmailDraft || loadingEmailDraft" @click="submitEmailDraft">{{ loadingEmailDraft ? '草拟中…' : savingEmailDraft ? '保存中…' : '保存草稿' }}</UiButton></div>
      </div>
    </div>

    <!-- 导出报告对话框 -->
    <div
      v-if="showExportDialog"
      class="fixed inset-0 bg-black/50 flex items-center justify-center z-50"
      @click.self="showExportDialog = false"
    >
      <div class="bg-card rounded-lg shadow-lg w-full max-w-md mx-4">
        <div class="p-6 border-b border-border">
          <h3 class="text-lg font-semibold">导出审查报告</h3>
          <p class="text-sm text-muted-foreground mt-1">选择导出方式</p>
        </div>
        <div class="p-6 space-y-4">
          <!-- 导出类型选择 -->
          <div class="space-y-2">
            <label class="text-sm font-medium">导出方式</label>
            <UiSelect v-model="exportType">
              <UiSelectItem value="review_report">审查报告（结构化报告文档）</UiSelectItem>
              <UiSelectItem value="original_with_comments" :disabled="isPdfContract">
                原文+审批批注
                <span v-if="isPdfContract">（仅支持Word文件）</span>
              </UiSelectItem>
            </UiSelect>
            <p v-if="exportType === 'original_with_comments' && !isPdfContract" class="text-xs text-muted-foreground">
              将在原始Word文档的对应条款处添加AI审查批注，方便直接在原文上修改。
            </p>
            <p v-if="isPdfContract && exportType === 'review_report'" class="text-xs text-muted-foreground">
              提示：PDF文件不支持添加批注，已自动切换为审查报告模式。
            </p>
          </div>

          <!-- 审查报告选项（仅当选择审查报告时显示） -->
          <div v-if="exportType === 'review_report'" class="space-y-3 pt-3 border-t">
            <label class="text-sm font-medium">报告内容</label>
            <div class="flex items-center space-x-2">
              <UiCheckbox id="export-risk" v-model="exportOptions.include_risk_clauses" />
              <label for="export-risk" class="text-sm">风险条款 ({{ review?.risk_clauses?.length || 0 }})</label>
            </div>
            <div class="flex items-center space-x-2">
              <UiCheckbox id="export-missing" v-model="exportOptions.include_missing_clauses" />
              <label for="export-missing" class="text-sm">缺失条款 ({{ review?.missing_clauses?.length || 0 }})</label>
            </div>
            <div class="flex items-center space-x-2">
              <UiCheckbox id="export-suggestions" v-model="exportOptions.include_suggestions" />
              <label for="export-suggestions" class="text-sm">修改建议 ({{ review?.suggestions?.length || 0 }})</label>
            </div>
            <div class="flex items-center space-x-2">
              <UiCheckbox id="export-judgments" v-model="exportOptions.include_rule_judgments" />
              <label for="export-judgments" class="text-sm">规则判定结果</label>
            </div>
            <div class="flex items-center space-x-2">
              <UiCheckbox id="export-policy" v-model="exportOptions.include_policy_references" />
              <label for="export-policy" class="text-sm">政策参考 ({{ review?.policy_references?.length || 0 }})</label>
            </div>
          </div>
        </div>
        <div class="p-6 border-t border-border flex justify-end gap-3">
          <UiButton variant="outline" @click="showExportDialog = false">取消</UiButton>
          <UiButton @click="confirmExport">
            <Download class="w-4 h-4 mr-2" />
            导出
          </UiButton>
        </div>
      </div>
    </div>
  </div>
</template>
