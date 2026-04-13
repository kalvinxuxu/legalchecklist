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
  <div class="p-6">
    <!-- Loading -->
    <div v-if="isLoading" class="space-y-3">
      <div class="h-20 bg-muted rounded-lg animate-pulse" />
      <div class="h-28 bg-muted rounded-lg animate-pulse" />
    </div>

    <!-- Error -->
    <div v-else-if="isError" class="py-12 text-center">
      <AlertTriangle class="w-8 h-8 text-danger-500 mx-auto mb-3" />
      <h3 class="text-sm font-medium mb-1">理解分析失败</h3>
      <p class="text-xs text-muted-foreground">{{ (error as Error)?.message || '暂无法加载理解分析' }}</p>
    </div>

    <!-- Empty -->
    <div v-else-if="!data" class="py-12 text-center">
      <FileText class="w-8 h-8 text-muted-foreground/30 mx-auto mb-3" />
      <h3 class="text-sm font-medium mb-1">暂无理解分析结果</h3>
    </div>

    <!-- Content -->
    <template v-else>
      <!-- Quick Cards -->
      <div v-if="data.quick_cards">
        <h3 class="text-sm font-semibold mb-3 flex items-center gap-2 text-muted-foreground">
          <FileText class="w-4 h-4" />
          快速理解
        </h3>
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
          <div v-if="data.quick_cards.contract_purpose" class="p-3 rounded-lg bg-blue-50 border border-blue-200">
            <p class="text-xs text-blue-600 mb-1">合同用途</p>
            <p class="text-sm text-foreground">{{ data.quick_cards.contract_purpose }}</p>
          </div>

          <div v-if="data.quick_cards.key_dates?.length" class="p-3 rounded-lg bg-orange-50 border border-orange-200">
            <p class="text-xs text-orange-600 mb-1">关键日期</p>
            <ul class="text-xs space-y-0.5 list-disc list-inside">
              <li v-for="(d, i) in data.quick_cards.key_dates" :key="i">{{ d }}</li>
            </ul>
          </div>

          <div v-if="data.quick_cards.payment_summary" class="p-3 rounded-lg bg-green-50 border border-green-200">
            <p class="text-xs text-green-600 mb-1">支付条款</p>
            <p class="text-sm text-foreground">{{ data.quick_cards.payment_summary }}</p>
            <div v-if="data.summary?.payment_terms" class="mt-1.5 pt-1.5 border-t border-green-200">
              <p v-if="data.summary.payment_terms.amount" class="text-xs text-muted-foreground">金额: {{ data.summary.payment_terms.amount }}</p>
              <p v-if="data.summary.payment_terms.payment_method" class="text-xs text-muted-foreground">方式: {{ data.summary.payment_terms.payment_method }}</p>
            </div>
          </div>

          <div v-if="data.quick_cards.breach_summary" class="p-3 rounded-lg bg-red-50 border border-red-200">
            <p class="text-xs text-red-600 mb-1">违约责任</p>
            <p class="text-sm text-foreground">{{ data.quick_cards.breach_summary }}</p>
            <p v-if="data.summary?.breach_liability?.compensation_range" class="text-xs text-muted-foreground mt-1.5 pt-1.5 border-t border-red-200">
              赔偿范围: {{ data.summary.breach_liability.compensation_range }}
            </p>
          </div>

          <div v-if="data.quick_cards.core_obligations?.length" class="p-3 rounded-lg bg-purple-50 border border-purple-200">
            <p class="text-xs text-purple-600 mb-1">双方核心义务</p>
            <ul class="text-xs space-y-0.5 list-disc list-inside">
              <li v-for="(ob, i) in data.quick_cards.core_obligations" :key="i">{{ ob }}</li>
            </ul>
          </div>
        </div>
      </div>

      <!-- Structure -->
      <div v-if="data.structure?.sections?.length" class="mt-5">
        <h3 class="text-sm font-semibold mb-3 flex items-center gap-2 text-muted-foreground">
          <FolderOpen class="w-4 h-4" />
          合同结构
        </h3>
        <div v-if="data.structure.structure_summary" class="bg-muted/50 rounded-md px-3 py-2 text-xs text-muted-foreground mb-3">
          {{ data.structure.structure_summary }}
        </div>
        <div class="flex flex-wrap gap-2">
          <div
            v-for="(section, idx) in data.structure.sections"
            :key="idx"
            class="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-card border border-border text-xs"
          >
            <div
              class="w-2 h-2 rounded-full"
              :style="{ backgroundColor: getSectionColor(section.title) }"
            />
            <span class="font-medium">{{ section.title }}</span>
            <span v-if="section.content" class="text-muted-foreground truncate max-w-[120px]">{{ section.content }}</span>
          </div>
        </div>
      </div>

      <!-- Key Clauses -->
      <div v-if="data.summary?.key_clauses?.length" class="mt-5">
        <h3 class="text-sm font-semibold mb-3 flex items-center gap-2 text-muted-foreground">
          <BookOpen class="w-4 h-4" />
          重要条款摘要
        </h3>
        <div class="space-y-2">
          <div
            v-for="(clause, idx) in data.summary.key_clauses"
            :key="idx"
            class="flex items-start gap-3 p-3 rounded-lg bg-card border border-l-3"
            :class="[
              clause.risk_benefit === 'risk' ? 'border-l-danger-500' :
              clause.risk_benefit === 'benefit' ? 'border-l-success-500' :
              'border-l-muted-foreground',
            ]"
          >
            <div class="flex-1 min-w-0">
              <div class="flex items-center gap-2 mb-1">
                <span class="text-sm font-medium">{{ clause.title }}</span>
                <UiBadge :variant="getRiskBenefitVariant(clause.risk_benefit)" class="text-xs px-1.5 py-0">
                  {{ clause.risk_benefit === 'risk' ? '风险' : clause.risk_benefit === 'benefit' ? '利好' : '中性' }}
                </UiBadge>
              </div>
              <p v-if="clause.summary" class="text-xs text-muted-foreground">{{ clause.summary }}</p>
            </div>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>
