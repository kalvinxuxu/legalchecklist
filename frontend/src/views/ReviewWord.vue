<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useContract, useReviewResult } from '@/composables/useContracts'
import { useToast } from '@/composables/useToast'
import {
  ArrowLeft,
  Search,
  Check,
  X,
  Edit2,
  Download,
  AlertTriangle,
  Loader2,
} from 'lucide-vue-next'
import { CONTRACT_TYPE_MAP, RISK_LEVEL_MAP, formatDateShort } from '@/lib/utils'
import { cn } from '@/lib/utils'
import api from '@/lib/api'

const route = useRoute()
const router = useRouter()
const id = computed(() => route.params.id as string)

const { data: contract, isLoading: contractLoading } = useContract(id.value)
const { data: review, isLoading: reviewLoading } = useReviewResult(id.value)
const { toast } = useToast()

const paragraphs = ref<Array<{ index: number; text: string }>>([])
const acceptedClauses = ref(new Set<number>())
const rejectedClauses = ref(new Set<number>())
const customSuggestions = ref<Record<number, string>>({})
const searchText = ref('')
const currentRiskParagraph = ref(-1)
const editDialog = ref<{ original_text?: string; newText: string } | null>(null)
const isEditDialogOpen = computed({
  get: () => editDialog.value !== null,
  set: (v) => { if (!v) editDialog.value = null }
})
const blockRefs = ref<Record<number, HTMLElement | null>>({})
const downloading = ref(false)

// Load paragraphs
async function loadParagraphs() {
  try {
    const data = await api.get(`/contracts/${id.value}/word-paragraphs`) as { paragraphs: Array<{ index: number; text: string }> }
    paragraphs.value = data.paragraphs || []
  } catch {}
}

contract.value && loadParagraphs()

const searchMatches = computed(() => {
  if (!searchText.value.trim()) return []
  const search = searchText.value.toLowerCase()
  return paragraphs.value
    .map((p, i) => ({ text: p.text.toLowerCase(), i }))
    .filter(({ text }) => text.includes(search))
    .map(({ i }) => i)
})

const riskClauses = computed(() => {
  if (!review.value?.risk_clauses) return []
  return review.value.risk_clauses.map((clause, idx) => {
    const matched = findParagraphIndex(clause.original_text || '')
    return { ...clause, paragraph_index: matched !== -1 ? matched : null, _original_index: idx }
  })
})

function findParagraphIndex(text: string): number {
  if (!text || !paragraphs.value.length) return -1
  const search = text.trim().toLowerCase()
  for (let i = 0; i < paragraphs.value.length; i++) {
    const p = paragraphs.value[i].text.trim().toLowerCase()
    if (p.includes(search) || search.includes(p)) return i
  }
  return -1
}

function hasRiskInParagraph(idx: number) {
  return riskClauses.value.some((c) => c.paragraph_index === idx)
}

function getRiskLevelForParagraph(idx: number) {
  const clause = riskClauses.value.find((c) => c.paragraph_index === idx)
  return clause?.risk_level || null
}

function getSuggestionForClause(clause: (typeof riskClauses.value)[0]) {
  const idx = clause._original_index!
  if (customSuggestions.value[idx]) return customSuggestions.value[idx]
  return clause.suggestion || review.value?.suggestions?.find((s) => s.title === clause.title)?.content || ''
}

function handleAccept(clause: (typeof riskClauses.value)[0]) {
  const idx = clause._original_index!
  acceptedClauses.value.add(idx)
  rejectedClauses.value.delete(idx)
  toast({ title: '已采纳建议', variant: 'success' })
}

function handleReject(clause: (typeof riskClauses.value)[0]) {
  const idx = clause._original_index!
  rejectedClauses.value.add(idx)
  acceptedClauses.value.delete(idx)
  toast({ title: '已拒绝建议', variant: 'default' })
}

function handleEdit(clause: (typeof riskClauses.value)[0]) {
  editDialog.value = {
    original_text: clause.original_text,
    newText: getSuggestionForClause(clause),
  }
}

function confirmEdit() {
  if (!editDialog.value) return
  const idx = riskClauses.value.find((c) => c.original_text === editDialog.value!.original_text)?._original_index!
  if (idx !== undefined) {
    customSuggestions.value[idx] = editDialog.value.newText
    acceptedClauses.value.add(idx)
    rejectedClauses.value.delete(idx)
    toast({ title: '已更新建议', variant: 'success' })
  }
  editDialog.value = null
}

function acceptAll() {
  riskClauses.value.forEach((c) => {
    acceptedClauses.value.add(c._original_index!)
    rejectedClauses.value.delete(c._original_index!)
  })
  toast({ title: '已采纳全部建议', variant: 'success' })
}

async function downloadRevised() {
  const suggestions = riskClauses.value
    .filter((c) => acceptedClauses.value.has(c._original_index!))
    .map((c) => ({
      paragraph_index: c.paragraph_index || 0,
      original_text: c.original_text,
      new_text: customSuggestions.value[c._original_index!] || c.original_text,
      risk_description: c.risk_description,
      accepted: true,
    }))

  downloading.value = true
  try {
    const response = await api.post(`/contracts/${id.value}/apply-suggestions`, suggestions, { responseType: 'blob' })
    const blob = new Blob([response as Blob], { type: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = '修订版_合同.docx'
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
    toast({ title: '修订文档已生成并下载', variant: 'success' })
  } catch {
    toast({ title: '生成修订文档失败', variant: 'destructive' })
  } finally {
    downloading.value = false
  }
}

function getTypeVariant(type: string) {
  return (CONTRACT_TYPE_MAP[type]?.variant || 'secondary') as 'primary' | 'success' | 'warning' | 'destructive' | 'info' | 'secondary' | 'outline' | 'ghost' | 'default'
}
</script>

<template>
  <div class="flex flex-col h-full">
    <!-- Header -->
    <div class="flex items-center justify-between px-6 py-4 bg-card border-b border-border">
      <div class="flex items-center gap-3">
        <UiButton variant="ghost" size="icon" @click="router.push('/workspace/contracts')">
          <ArrowLeft class="w-4 h-4" />
        </UiButton>
        <h1 class="text-lg font-semibold">Word 审查</h1>
      </div>
      <div class="flex items-center gap-2">
        <UiButton variant="success" size="sm" :disabled="acceptedClauses.size === 0" @click="acceptAll">
          <Check class="w-4 h-4" />
          采纳全部
        </UiButton>
        <UiButton size="sm" :disabled="acceptedClauses.size === 0" :loading="downloading" @click="downloadRevised">
          <Download class="w-4 h-4" />
          下载修订文档
        </UiButton>
      </div>
    </div>

    <!-- Loading -->
    <div v-if="contractLoading || reviewLoading" class="flex-1 flex items-center justify-center">
      <Loader2 class="w-8 h-8 animate-spin text-primary-600" />
    </div>

    <!-- Not Ready -->
    <div v-else-if="!contract || contract.review_status !== 'completed'" class="flex-1 flex items-center justify-center">
      <UiCard class="w-full max-w-md">
        <UiCardContent class="py-12 text-center">
          <p class="text-muted-foreground">合同尚未完成审查</p>
        </UiCardContent>
      </UiCard>
    </div>

    <!-- Main Content -->
    <div v-else class="flex-1 flex overflow-hidden">
      <!-- Contract Info -->
      <div class="px-6 py-3 bg-card border-b border-border flex items-center gap-4 w-full">
        <h2 class="text-base font-medium">{{ contract.file_name }}</h2>
        <UiBadge :variant="getTypeVariant(contract.contract_type)">
          {{ CONTRACT_TYPE_MAP[contract.contract_type]?.label || contract.contract_type }}
        </UiBadge>
        <span class="text-sm text-muted-foreground">{{ formatDateShort(contract.created_at) }}</span>
        <span class="text-sm text-muted-foreground">{{ paragraphs.length }} 段落</span>
      </div>

      <!-- Body -->
      <div class="flex-1 flex overflow-hidden">
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
              v-for="(para, idx) in paragraphs"
              :key="para.index"
              :ref="(el) => { if (el) blockRefs[idx] = el as HTMLElement }"
              @click="currentRiskParagraph = idx"
              :class="cn(
                'flex gap-3 p-3 rounded-md cursor-pointer transition-all border-l-[3px]',
                hasRiskInParagraph(idx) ? 'bg-danger-50 border-l-danger-500' : '',
                searchMatches.includes(idx) && !hasRiskInParagraph(idx) ? 'bg-warning-50 border-l-warning-500' : '',
                currentRiskParagraph === idx && !hasRiskInParagraph(idx) ? 'bg-accent border-l-muted-foreground' : '',
                'border-l-transparent hover:bg-accent',
              )"
            >
              <span class="flex-shrink-0 w-7 h-7 bg-muted rounded-full flex items-center justify-center text-xs font-medium text-muted-foreground">
                {{ idx + 1 }}
              </span>
              <div class="flex-1">
                <p class="text-sm whitespace-pre-wrap leading-relaxed">{{ para.text }}</p>
                <div v-if="hasRiskInParagraph(idx)" class="mt-1">
                  <UiBadge
                    :variant="(RISK_LEVEL_MAP[getRiskLevelForParagraph(idx) || 'medium']?.variant || 'secondary') as 'primary' | 'success' | 'warning' | 'destructive' | 'info' | 'secondary' | 'outline' | 'ghost' | 'default'"
                    class="text-xs"
                  >
                    {{ RISK_LEVEL_MAP[getRiskLevelForParagraph(idx) || 'medium']?.label }}
                  </UiBadge>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Right: Suggestions -->
        <div class="w-[480px] flex-shrink-0 overflow-y-auto p-4 bg-muted/50 space-y-4">
          <!-- Stats -->
          <div class="grid grid-cols-2 gap-3">
            <UiCard>
              <UiCardContent class="pt-4">
                <div class="flex items-center gap-3">
                  <div class="w-10 h-10 bg-danger-50 rounded-lg flex items-center justify-center">
                    <AlertTriangle class="w-5 h-5 text-danger-500" />
                  </div>
                  <div>
                    <p class="text-xl font-bold">{{ riskClauses.length }}</p>
                    <p class="text-xs text-muted-foreground">风险条款</p>
                  </div>
                </div>
              </UiCardContent>
            </UiCard>
            <UiCard>
              <UiCardContent class="pt-4">
                <div class="flex items-center gap-3">
                  <div class="w-10 h-10 bg-success-50 rounded-lg flex items-center justify-center">
                    <Check class="w-5 h-5 text-success-500" />
                  </div>
                  <div>
                    <p class="text-xl font-bold">{{ acceptedClauses.size }}</p>
                    <p class="text-xs text-muted-foreground">已采纳</p>
                  </div>
                </div>
              </UiCardContent>
            </UiCard>
          </div>

          <!-- Suggestions -->
          <UiCard>
            <UiCardContent class="pt-4">
              <h4 class="text-sm font-semibold flex items-center gap-2 mb-4">
                <Edit2 class="w-4 h-4" />
                风险建议
              </h4>
              <div v-if="riskClauses.length === 0" class="text-center py-8 text-muted-foreground">
                暂未发现风险条款
              </div>
              <div v-else class="space-y-3">
                <div
                  v-for="clause in riskClauses"
                  :key="clause._original_index"
                  :class="cn(
                    'p-4 rounded-lg border transition-all',
                    acceptedClauses.has(clause._original_index!) ? 'border-success-500 bg-success-50' :
                    rejectedClauses.has(clause._original_index!) ? 'border-border bg-muted/50 opacity-60' :
                    'border-border bg-card',
                  )"
                >
                  <div class="flex items-start justify-between gap-2 mb-2">
                    <div class="flex items-center gap-2">
                      <UiBadge
                        :variant="(RISK_LEVEL_MAP[clause.risk_level || 'medium']?.variant || 'secondary') as 'primary' | 'success' | 'warning' | 'destructive' | 'info' | 'secondary' | 'outline' | 'ghost' | 'default'"
                      >
                        {{ RISK_LEVEL_MAP[clause.risk_level || 'medium']?.label }}
                      </UiBadge>
                      <UiBadge v-if="acceptedClauses.has(clause._original_index!)" variant="success">已采纳</UiBadge>
                      <UiBadge v-if="rejectedClauses.has(clause._original_index!)" variant="secondary">已拒绝</UiBadge>
                    </div>
                  </div>

                  <p v-if="clause.original_text" class="text-xs text-muted-foreground italic mb-2 p-2 bg-muted rounded">
                    "{{ clause.original_text.slice(0, 80) }}..."
                  </p>
                  <p v-if="clause.risk_description" class="text-sm mb-2">{{ clause.risk_description }}</p>

                  <div v-if="getSuggestionForClause(clause) && !rejectedClauses.has(clause._original_index!)" class="mt-2 p-2 bg-primary-50 rounded text-sm">
                    <strong class="text-primary-600">建议：</strong>
                    <span>{{ getSuggestionForClause(clause) }}</span>
                  </div>

                  <div v-if="!rejectedClauses.has(clause._original_index!)" class="flex items-center gap-2 mt-3">
                    <UiButton size="sm" variant="success" @click="handleAccept(clause)">
                      <Check class="w-3.5 h-3.5" />
                      采纳
                    </UiButton>
                    <UiButton size="sm" variant="outline" @click="handleReject(clause)">
                      <X class="w-3.5 h-3.5" />
                      拒绝
                    </UiButton>
                    <UiButton size="sm" variant="ghost" @click="handleEdit(clause)">
                      <Edit2 class="w-3.5 h-3.5" />
                      编辑
                    </UiButton>
                  </div>
                </div>
              </div>
            </UiCardContent>
          </UiCard>
        </div>
      </div>
    </div>

    <!-- Edit Dialog -->
    <UiDialog v-model="isEditDialogOpen">
      <div class="space-y-4">
        <h3 class="text-lg font-semibold">编辑建议</h3>
        <div v-if="editDialog">
          <div class="space-y-2">
            <p class="text-sm font-medium">原文：</p>
            <p class="text-sm text-muted-foreground p-3 bg-muted rounded-md italic">{{ editDialog.original_text }}</p>
          </div>
          <div class="space-y-2 mt-4">
            <p class="text-sm font-medium">修改后：</p>
            <textarea
              v-model="editDialog.newText"
              rows="4"
              class="w-full px-3 py-2 text-sm border border-input rounded-md focus:outline-none focus:ring-1 focus:ring-ring"
              placeholder="请输入修改后的文本"
            />
          </div>
          <div class="flex justify-end gap-2 mt-4">
            <UiButton variant="outline" @click="editDialog = null">取消</UiButton>
            <UiButton @click="confirmEdit">确认</UiButton>
          </div>
        </div>
      </div>
    </UiDialog>
  </div>
</template>
