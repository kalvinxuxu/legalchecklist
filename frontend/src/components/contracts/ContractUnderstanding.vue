<script setup lang="ts">
import { useContractUnderstanding } from '@/composables/useContracts'
import { FileText, Calendar, CreditCard, AlertTriangle, List, FolderOpen, BookOpen } from 'lucide-vue-next'
import { RISK_LEVEL_MAP } from '@/lib/utils'

interface Props {
  contractId: string | { value: string }
}

const props = defineProps<Props>()
const id = typeof props.contractId === 'object' ? props.contractId.value : props.contractId

const { data, isLoading, isError, error } = useContractUnderstanding(id)

const SECTION_COLOR_MAP: Record<string, string> = {
  违约: '#C62828', 责任: '#C62828',
  保密: '#1565C0', 义务: '#1565C0',
  支付: '#2E7D32', 报酬: '#2E7D32',
  终止: '#E65100', 解除: '#E65100',
}

function getSectionColor(title: string): string {
  for (const [key, color] of Object.entries(SECTION_COLOR_MAP)) {
    if (title.toLowerCase().includes(key)) return color
  }
  return '#9E9E9E'
}

function getRiskBenefitVariant(b?: string) {
  if (b === 'risk') return 'destructive'
  if (b === 'benefit') return 'success'
  return 'info'
}
</script>

<template>
  <div class="space-y-6 max-w-4xl">
    <!-- Loading -->
    <div v-if="isLoading" class="space-y-4">
      <div class="h-32 bg-muted rounded-lg animate-pulse" />
      <div class="h-48 bg-muted rounded-lg animate-pulse" />
    </div>

    <!-- Error -->
    <UiCard v-else-if="isError">
      <UiCardContent class="py-12 text-center">
        <AlertTriangle class="w-10 h-10 text-danger-500 mx-auto mb-4" />
        <h3 class="text-base font-medium mb-2">理解分析失败</h3>
        <p class="text-sm text-muted-foreground">{{ (error as Error)?.message || '暂无法加载理解分析' }}</p>
      </UiCardContent>
    </UiCard>

    <!-- Empty -->
    <UiCard v-else-if="!data">
      <UiCardContent class="py-12 text-center">
        <FileText class="w-10 h-10 text-muted-foreground/30 mx-auto mb-4" />
        <h3 class="text-base font-medium mb-2">暂无理解分析结果</h3>
      </UiCardContent>
    </UiCard>

    <!-- Content -->
    <template v-else>
      <!-- Quick Cards -->
      <div v-if="data.quick_cards">
        <h3 class="text-base font-semibold mb-3 flex items-center gap-2">
          <FileText class="w-4 h-4" />
          快速理解
        </h3>
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <UiCard v-if="data.quick_cards.contract_purpose">
            <UiCardHeader class="pb-2">
              <UiCardTitle class="text-sm flex items-center gap-2">
                <FileText class="w-3.5 h-3.5" />
                合同用途
              </UiCardTitle>
            </UiCardHeader>
            <UiCardContent>
              <p class="text-sm">{{ data.quick_cards.contract_purpose }}</p>
            </UiCardContent>
          </UiCard>

          <UiCard v-if="data.quick_cards.key_dates?.length">
            <UiCardHeader class="pb-2">
              <UiCardTitle class="text-sm flex items-center gap-2">
                <Calendar class="w-3.5 h-3.5" />
                关键日期
              </UiCardTitle>
            </UiCardHeader>
            <UiCardContent>
              <ul class="text-sm space-y-1 list-disc list-inside">
                <li v-for="(d, i) in data.quick_cards.key_dates" :key="i">{{ d }}</li>
              </ul>
            </UiCardContent>
          </UiCard>

          <UiCard v-if="data.quick_cards.payment_summary" class="border-l-4 border-l-success-500">
            <UiCardHeader class="pb-2">
              <UiCardTitle class="text-sm flex items-center gap-2">
                <CreditCard class="w-3.5 h-3.5" />
                支付条款
              </UiCardTitle>
            </UiCardHeader>
            <UiCardContent>
              <p class="text-sm">{{ data.quick_cards.payment_summary }}</p>
              <div v-if="data.summary?.payment_terms" class="mt-2 pt-2 border-t border-border text-xs text-muted-foreground space-y-1">
                <p v-if="data.summary.payment_terms.amount">金额: {{ data.summary.payment_terms.amount }}</p>
                <p v-if="data.summary.payment_terms.payment_method">方式: {{ data.summary.payment_terms.payment_method }}</p>
              </div>
            </UiCardContent>
          </UiCard>

          <UiCard v-if="data.quick_cards.breach_summary" class="border-l-4 border-l-danger-500">
            <UiCardHeader class="pb-2">
              <UiCardTitle class="text-sm flex items-center gap-2">
                <AlertTriangle class="w-3.5 h-3.5" />
                违约责任
              </UiCardTitle>
            </UiCardHeader>
            <UiCardContent>
              <p class="text-sm">{{ data.quick_cards.breach_summary }}</p>
              <p v-if="data.summary?.breach_liability?.compensation_range" class="mt-2 pt-2 border-t border-border text-xs text-muted-foreground">
                赔偿范围: {{ data.summary.breach_liability.compensation_range }}
              </p>
            </UiCardContent>
          </UiCard>

          <UiCard v-if="data.quick_cards.core_obligations?.length" class="border-l-4 border-l-primary-500">
            <UiCardHeader class="pb-2">
              <UiCardTitle class="text-sm flex items-center gap-2">
                <List class="w-3.5 h-3.5" />
                双方核心义务
              </UiCardTitle>
            </UiCardHeader>
            <UiCardContent>
              <ul class="text-sm space-y-1 list-disc list-inside">
                <li v-for="(ob, i) in data.quick_cards.core_obligations" :key="i">{{ ob }}</li>
              </ul>
            </UiCardContent>
          </UiCard>
        </div>
      </div>

      <!-- Structure -->
      <div v-if="data.structure?.sections?.length">
        <h3 class="text-base font-semibold mb-3 flex items-center gap-2">
          <FolderOpen class="w-4 h-4" />
          合同结构
        </h3>
        <div v-if="data.structure.structure_summary" class="bg-muted rounded-lg p-3 text-sm text-muted-foreground mb-3">
          {{ data.structure.structure_summary }}
        </div>
        <div class="relative border-l-2 border-border pl-6 space-y-4">
          <div v-for="(section, idx) in data.structure.sections" :key="idx" class="relative">
            <div
              class="absolute -left-[29px] w-4 h-4 rounded-full border-2 border-card"
              :style="{ backgroundColor: getSectionColor(section.title) }"
            />
            <div>
              <span class="text-sm font-medium">{{ section.title }}</span>
              <p v-if="section.content" class="text-xs text-muted-foreground mt-0.5">{{ section.content }}</p>
            </div>
          </div>
        </div>
      </div>

      <!-- Key Clauses -->
      <div v-if="data.summary?.key_clauses?.length">
        <h3 class="text-base font-semibold mb-3 flex items-center gap-2">
          <BookOpen class="w-4 h-4" />
          重要条款摘要
        </h3>
        <div class="space-y-3">
          <UiCard
            v-for="(clause, idx) in data.summary.key_clauses"
            :key="idx"
            :class="[
              'border-l-4',
              clause.risk_benefit === 'risk' ? 'border-l-danger-500' :
              clause.risk_benefit === 'benefit' ? 'border-l-success-500' :
              'border-l-muted-foreground',
            ]"
          >
            <UiCardContent class="pt-4">
              <div class="flex items-start justify-between gap-2 mb-1">
                <span class="text-sm font-medium">{{ clause.title }}</span>
                <UiBadge :variant="getRiskBenefitVariant(clause.risk_benefit)">
                  {{ clause.risk_benefit === 'risk' ? '风险' : clause.risk_benefit === 'benefit' ? '利好' : '中性' }}
                </UiBadge>
              </div>
              <p v-if="clause.summary" class="text-sm text-muted-foreground">{{ clause.summary }}</p>
            </UiCardContent>
          </UiCard>
        </div>
      </div>
    </template>
  </div>
</template>
