<script setup lang="ts">
import { computed } from 'vue'
import { CheckCircle, AlertTriangle, XCircle, Shield, AlertCircle } from 'lucide-vue-next'
import { APPROVAL_FLOW_MAP, RULE_JUDGMENT_TYPE_MAP, RISK_LEVEL_MAP } from '@/lib/utils'
import { cn } from '@/lib/utils'
import UiBadge from '@/components/ui/badge.vue'
import UiCard from '@/components/ui/card.vue'
import UiCardContent from '@/components/ui/card-content.vue'

interface RuleJudgment {
  clause_type: string
  original_text: string
  extracted_value?: string
  policy_limit?: string
  policy_standard?: string
  threshold?: string
  judgment: string
  suggestion?: string
  risk_level?: 'high' | 'medium' | 'low'
}

interface RuleJudgments {
  violations: RuleJudgment[]
  approvals_needed: RuleJudgment[]
  compliant: RuleJudgment[]
}

interface Props {
  ruleJudgments?: RuleJudgments
  approvalFlow?: 'auto' | 'legal_review' | 'executive_approval'
  approvalFlowDescription?: string
  overallRiskLevel?: 'high' | 'medium' | 'low'
}

const props = defineProps<Props>()

const approvalInfo = computed(() => {
  return APPROVAL_FLOW_MAP[props.approvalFlow || 'auto']
})

const riskInfo = computed(() => {
  return RISK_LEVEL_MAP[props.overallRiskLevel || 'low']
})

const hasRuleJudgments = computed(() => {
  return props.ruleJudgments && (
    props.ruleJudgments.violations?.length > 0 ||
    props.ruleJudgments.approvals_needed?.length > 0 ||
    props.ruleJudgments.compliant?.length > 0
  )
})

function getIconForType(type: string) {
  switch (type) {
    case 'violations':
      return XCircle
    case 'approvals_needed':
      return AlertTriangle
    case 'compliant':
      return CheckCircle
    default:
      return AlertCircle
  }
}

function getTypeInfo(type: string) {
  return RULE_JUDGMENT_TYPE_MAP[type] || RULE_JUDGMENT_TYPE_MAP.compliant
}
</script>

<template>
  <!-- 审批流程概览 -->
  <div
    v-if="approvalFlow"
    :class="cn(
      'rounded-lg p-4 border mb-4',
      approvalFlow === 'auto' ? 'bg-[#E8F5E9] border-[#2E7D32]' :
      approvalFlow === 'legal_review' ? 'bg-[#FFF3E0] border-[#E65100]' :
      'bg-[#FFEBEE] border-[#C62828]'
    )"
  >
    <div class="flex items-center gap-3">
      <div
        :class="cn(
          'w-10 h-10 rounded-full flex items-center justify-center',
          approvalFlow === 'auto' ? 'bg-[#2E7D32]' :
          approvalFlow === 'legal_review' ? 'bg-[#E65100]' :
          'bg-[#C62828]'
        )"
      >
        <CheckCircle v-if="approvalFlow === 'auto'" class="w-5 h-5 text-white" />
        <Shield v-else-if="approvalFlow === 'legal_review'" class="w-5 h-5 text-white" />
        <AlertTriangle v-else class="w-5 h-5 text-white" />
      </div>
      <div class="flex-1">
        <div class="flex items-center gap-2">
          <span
            :class="cn(
              'text-sm font-semibold',
              approvalFlow === 'auto' ? 'text-[#2E7D32]' :
              approvalFlow === 'legal_review' ? 'text-[#E65100]' :
              'text-[#C62828]'
            )"
          >
            {{ approvalInfo.label }}
          </span>
          <UiBadge
            v-if="overallRiskLevel"
            :variant="riskInfo.variant as any"
            class="text-xs"
          >
            {{ riskInfo.label }}
          </UiBadge>
        </div>
        <p class="text-xs text-muted-foreground mt-0.5">
          {{ approvalFlowDescription || approvalInfo.label }}
        </p>
      </div>
    </div>
  </div>

  <!-- 规则判定详情 -->
  <div v-if="hasRuleJudgments" class="space-y-4">
    <!-- Violations (违反政策 - ❌) -->
    <div v-if="ruleJudgments?.violations?.length" class="bg-[#FFEBEE] rounded-lg p-3 border border-[#FFCDD2]">
      <div class="flex items-center gap-2 mb-3">
        <XCircle class="w-4 h-4 text-[#C62828]" />
        <span class="text-sm font-semibold text-[#C62828]">违反公司政策（必须修改）</span>
        <UiBadge variant="destructive" class="text-xs">{{ ruleJudgments.violations.length }} 项</UiBadge>
      </div>
      <div class="space-y-2">
        <div
          v-for="(item, idx) in ruleJudgments.violations"
          :key="idx"
          class="bg-white rounded-md p-3 border-l-[3px] border-l-[#C62828]"
        >
          <div class="flex items-start justify-between gap-2 mb-1">
            <span class="text-sm font-medium text-[#C62828]">{{ item.clause_type }}</span>
            <UiBadge variant="destructive" class="text-xs flex-shrink-0">❌ 违反</UiBadge>
          </div>
          <p v-if="item.extracted_value" class="text-xs text-muted-foreground mb-1">
            合同规定：<span class="font-medium text-foreground">{{ item.extracted_value }}</span>
          </p>
          <p v-if="item.policy_limit" class="text-xs text-[#C62828] mb-1">
            政策要求：{{ item.policy_limit }}
          </p>
          <p v-if="item.judgment" class="text-xs mb-1">{{ item.judgment }}</p>
          <p v-if="item.suggestion" class="text-xs text-primary">
            修改建议：{{ item.suggestion }}
          </p>
        </div>
      </div>
    </div>

    <!-- Approvals Needed (需要审批 - ⚠️) -->
    <div v-if="ruleJudgments?.approvals_needed?.length" class="bg-[#FFF3E0] rounded-lg p-3 border border-[#FFE0B2]">
      <div class="flex items-center gap-2 mb-3">
        <AlertTriangle class="w-4 h-4 text-[#E65100]" />
        <span class="text-sm font-semibold text-[#E65100]">需要审批</span>
        <UiBadge variant="warning" class="text-xs">{{ ruleJudgments.approvals_needed.length }} 项</UiBadge>
      </div>
      <div class="space-y-2">
        <div
          v-for="(item, idx) in ruleJudgments.approvals_needed"
          :key="idx"
          class="bg-white rounded-md p-3 border-l-[3px] border-l-[#E65100]"
        >
          <div class="flex items-start justify-between gap-2 mb-1">
            <span class="text-sm font-medium text-[#E65100]">{{ item.clause_type }}</span>
            <UiBadge variant="warning" class="text-xs flex-shrink-0">⚠️ 审批</UiBadge>
          </div>
          <p v-if="item.extracted_value" class="text-xs text-muted-foreground mb-1">
            合同规定：<span class="font-medium text-foreground">{{ item.extracted_value }}</span>
          </p>
          <p v-if="item.threshold" class="text-xs text-[#E65100] mb-1">
            审批阈值：{{ item.threshold }}
          </p>
          <p v-if="item.judgment" class="text-xs mb-1">{{ item.judgment }}</p>
          <p v-if="item.suggestion" class="text-xs text-primary">
            建议：{{ item.suggestion }}
          </p>
        </div>
      </div>
    </div>

    <!-- Compliant (合规 - ✅) -->
    <div v-if="ruleJudgments?.compliant?.length" class="bg-[#E8F5E9] rounded-lg p-3 border border-[#C8E6C9]">
      <div class="flex items-center gap-2 mb-3">
        <CheckCircle class="w-4 h-4 text-[#2E7D32]" />
        <span class="text-sm font-semibold text-[#2E7D32]">符合政策</span>
        <UiBadge variant="success" class="text-xs">{{ ruleJudgments.compliant.length }} 项</UiBadge>
      </div>
      <div class="space-y-2">
        <div
          v-for="(item, idx) in ruleJudgments.compliant"
          :key="idx"
          class="bg-white rounded-md p-3 border-l-[3px] border-l-[#2E7D32]"
        >
          <div class="flex items-start justify-between gap-2 mb-1">
            <span class="text-sm font-medium text-[#2E7D32]">{{ item.clause_type }}</span>
            <UiBadge variant="success" class="text-xs flex-shrink-0">✅ 合规</UiBadge>
          </div>
          <p v-if="item.extracted_value" class="text-xs text-muted-foreground mb-1">
            合同规定：<span class="font-medium text-foreground">{{ item.extracted_value }}</span>
          </p>
          <p v-if="item.policy_standard" class="text-xs text-[#2E7D32] mb-1">
            政策标准：{{ item.policy_standard }}
          </p>
          <p v-if="item.judgment" class="text-xs">{{ item.judgment }}</p>
        </div>
      </div>
    </div>
  </div>

  <!-- 无规则判定结果时的备用提示 -->
  <div v-else-if="!approvalFlow" class="text-center py-4 text-sm text-muted-foreground">
    正在进行规则判定...
  </div>
</template>
