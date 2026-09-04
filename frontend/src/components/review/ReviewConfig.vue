<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { Shield, TrendingUp, AlertTriangle } from 'lucide-vue-next'
import UiButton from '@/components/ui/button.vue'
import UiCard from '@/components/ui/card.vue'
import UiCardContent from '@/components/ui/card-content.vue'
import UiLabel from '@/components/ui/label.vue'
import { cn } from '@/lib/utils'

interface Props {
  modelValue?: {
    party_position?: string | null
    contract_amount?: number | null
    risk_preference?: string | null
  }
  showDescription?: boolean
}

interface Emits {
  (e: 'update:modelValue', value: Props['modelValue']): void
  (e: 'save'): void
}

const props = withDefaults(defineProps<Props>(), {
  showDescription: true
})

const emit = defineEmits<Emits>()

const partyPosition = computed({
  get: () => props.modelValue?.party_position || null,
  set: (val) => emit('update:modelValue', { ...props.modelValue, party_position: val })
})

const contractAmount = computed({
  get: () => props.modelValue?.contract_amount || null,
  set: (val) => emit('update:modelValue', { ...props.modelValue, contract_amount: val ? parseFloat(val.toString()) : null })
})

const riskPreference = computed({
  get: () => props.modelValue?.risk_preference || null,
  set: (val) => emit('update:modelValue', { ...props.modelValue, risk_preference: val })
})

const POSITION_OPTIONS = [
  {
    value: 'party_a',
    label: '甲方',
    sublabel: '买方/发包方',
    description: '严格保护甲方利益，倾向于更严格的付款条件和更高的违约金保护',
    color: 'border-[#1565C0] bg-[#E3F2FD]/30'
  },
  {
    value: 'party_b',
    label: '乙方',
    sublabel: '卖方/承包方',
    description: '平衡乙方权益，倾向于更宽松的付款条件和更低的违约金压力',
    color: 'border-[#E65100] bg-[#FFF3E0]/30'
  }
]

const RISK_OPTIONS = [
  {
    value: 'low',
    label: '低风险',
    sublabel: '零容忍',
    description: '严格保护公司利益，宁可错过机会也不承担风险',
    color: 'border-[#2E7D32] bg-[#E8F5E9]/30'
  },
  {
    value: 'medium',
    label: '中风险',
    sublabel: '平衡策略',
    description: '在保护和机会之间寻求平衡',
    color: 'border-[#F57C00] bg-[#FFF3E0]/30'
  },
  {
    value: 'high',
    label: '高风险',
    sublabel: '开放策略',
    description: '可接受合理风险以换取商业机会',
    color: 'border-[#C62828] bg-[#FFEBEE]/30'
  }
]

function formatAmount(value: number | null): string {
  if (!value) return ''
  if (value >= 100000000) {
    return (value / 100000000).toFixed(2) + ' 亿'
  }
  if (value >= 1000000) {
    return (value / 1000000).toFixed(2) + ' 万'
  }
  return value.toString()
}

function getAmountHint(value: number | null): string {
  if (!value) return ''
  if (value >= 10000000) {
    return '特大额合同 - 需要最严格审查'
  }
  if (value >= 5000000) {
    return '重大合同 - 需要严格审查'
  }
  if (value >= 1000000) {
    return '大额合同 - 需要加强审查'
  }
  return '标准合同 - 使用标准审查'
}
</script>

<template>
  <UiCard>
    <UiCardContent class="p-4 space-y-6">
      <!-- 标题 -->
      <div class="flex items-center gap-2 pb-3 border-b">
        <Shield class="w-5 h-5 text-primary" />
        <h3 class="text-sm font-semibold">审查立场配置</h3>
      </div>

      <!-- 甲乙方立场 -->
      <div class="space-y-3">
        <UiLabel class="text-sm font-medium">我是</UiLabel>
        <div class="grid grid-cols-2 gap-3">
          <button
            v-for="opt in POSITION_OPTIONS"
            :key="opt.value"
            @click="partyPosition = opt.value"
            :class="[
              'relative flex flex-col items-start p-3 rounded-lg border-2 transition-all text-left',
              partyPosition === opt.value
                ? opt.color + ' ' + 'border-current shadow-sm'
                : 'border-border hover:border-muted-foreground/30 bg-card'
            ]"
          >
            <div class="flex items-center gap-2 mb-1">
              <span class="text-sm font-semibold">{{ opt.label }}</span>
              <span class="text-xs text-muted-foreground">{{ opt.sublabel }}</span>
            </div>
            <p v-if="showDescription" class="text-xs text-muted-foreground leading-relaxed">
              {{ opt.description }}
            </p>
            <div
              v-if="partyPosition === opt.value"
              class="absolute top-2 right-2 w-4 h-4 rounded-full bg-primary flex items-center justify-center"
            >
              <svg class="w-3 h-3 text-primary-foreground" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3">
                <polyline points="20 6 9 17 4 12" />
              </svg>
            </div>
          </button>
        </div>
      </div>

      <!-- 风险偏好 -->
      <div class="space-y-3">
        <UiLabel class="text-sm font-medium">风险偏好</UiLabel>
        <div class="grid grid-cols-3 gap-2">
          <button
            v-for="opt in RISK_OPTIONS"
            :key="opt.value"
            @click="riskPreference = opt.value"
            :class="[
              'relative flex flex-col items-center p-3 rounded-lg border-2 transition-all',
              riskPreference === opt.value
                ? opt.color + ' ' + 'border-current shadow-sm'
                : 'border-border hover:border-muted-foreground/30 bg-card'
            ]"
          >
            <div class="flex items-center gap-1 mb-1">
              <AlertTriangle
                :class="[
                  'w-4 h-4',
                  riskPreference === opt.value ? 'text-current' : 'text-muted-foreground'
                ]"
              />
              <span class="text-sm font-semibold">{{ opt.label }}</span>
            </div>
            <span class="text-xs text-muted-foreground">{{ opt.sublabel }}</span>
            <p v-if="showDescription" class="text-xs text-muted-foreground text-center mt-1 leading-relaxed">
              {{ opt.description }}
            </p>
          </button>
        </div>
      </div>

      <!-- 合同金额 -->
      <div class="space-y-3">
        <UiLabel class="text-sm font-medium">合同金额（元）</UiLabel>
        <div class="relative">
          <input
            v-model.number="contractAmount"
            type="number"
            placeholder="请输入合同金额"
            class="w-full px-3 py-2 text-sm border border-input rounded-md focus:outline-none focus:ring-2 focus:ring-ring"
          />
          <TrendingUp class="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
        </div>
        <p v-if="contractAmount" class="text-xs text-muted-foreground">
          约 {{ formatAmount(contractAmount) }} - {{ getAmountHint(contractAmount) }}
        </p>
      </div>

      <!-- 保存按钮 -->
      <UiButton
        @click="emit('save')"
        class="w-full"
        size="sm"
      >
        保存配置并重新审查
      </UiButton>
    </UiCardContent>
  </UiCard>
</template>
