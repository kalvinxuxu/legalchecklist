<script setup lang="ts">
import { ref, computed } from 'vue'
import { FileText, AlertTriangle, Sparkles, FileCheck2 } from 'lucide-vue-next'
import type { DemoSample } from '@/data/demo-samples'
import { RISK_LEVEL_MAP } from '@/lib/utils'
import DemoRiskClause from './DemoRiskClause.vue'

const props = defineProps<{
  sample: DemoSample
}>()

const expanded = ref(false)

const riskStats = computed(() => ({
  high: props.sample.risk_clauses.filter((c) => c.risk_level === 'high').length,
  medium: props.sample.risk_clauses.filter((c) => c.risk_level === 'medium').length,
  low: props.sample.risk_clauses.filter((c) => c.risk_level === 'low').length,
}))

const displayedClauses = computed(() => {
  return expanded.value
    ? props.sample.risk_clauses
    : props.sample.risk_clauses.slice(0, 2)
})

const riskBadgeClass = computed(() => {
  return props.sample.risk_level === 'high'
    ? 'bg-red-100 text-red-700'
    : props.sample.risk_level === 'medium'
      ? 'bg-amber-100 text-amber-700'
      : 'bg-green-100 text-green-700'
})
</script>

<template>
  <div class="bg-white rounded-2xl border border-gray-200 overflow-hidden shadow-sm">
    <!-- 报告头部 -->
    <div class="px-6 py-5 border-b border-gray-100">
      <div class="flex items-center justify-between">
        <div class="flex items-center gap-3">
          <div class="w-11 h-11 rounded-xl bg-gray-100 flex items-center justify-center">
            <FileText class="w-5 h-5 text-gray-600" />
          </div>
          <div>
            <h3 class="font-semibold text-gray-900">{{ sample.file_name }}</h3>
            <p class="text-sm text-gray-500">{{ sample.contract_type }}</p>
          </div>
        </div>
        <span
          class="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium"
          :class="riskBadgeClass"
        >
          {{ RISK_LEVEL_MAP[sample.risk_level]?.label }}风险
        </span>
      </div>
    </div>

    <!-- 统计概览 -->
    <div class="px-6 py-4 bg-gray-50/50 border-b border-gray-100">
      <div class="grid grid-cols-3 gap-4 text-center">
        <div>
          <p class="text-2xl font-bold text-red-600">{{ riskStats.high }}</p>
          <p class="text-xs text-gray-500">高风险</p>
        </div>
        <div>
          <p class="text-2xl font-bold text-amber-600">{{ riskStats.medium }}</p>
          <p class="text-xs text-gray-500">中风险</p>
        </div>
        <div>
          <p class="text-2xl font-bold text-green-600">{{ riskStats.low }}</p>
          <p class="text-xs text-gray-500">低风险</p>
        </div>
      </div>
      <div class="mt-3 text-center">
        <span class="text-xs text-gray-400">
          置信度 {{ (sample.confidence_score * 100).toFixed(0) }}%
        </span>
      </div>
    </div>

    <!-- 风险条款列表 -->
    <div class="px-6 py-5 space-y-3">
      <h4 class="text-sm font-semibold text-gray-700 flex items-center gap-2">
        <AlertTriangle class="w-4 h-4 text-amber-500" />
        风险条款
      </h4>
      <DemoRiskClause
        v-for="(clause, idx) in displayedClauses"
        :key="idx"
        :clause="clause"
      />

      <button
        v-if="sample.risk_clauses.length > 2"
        @click="expanded = !expanded"
        class="w-full py-2.5 text-sm text-blue-600 hover:text-blue-700 font-medium transition-colors"
      >
        {{ expanded ? '收起' : `展开全部 ${sample.risk_clauses.length} 条风险条款` }}
      </button>
    </div>

    <!-- 快速理解摘要 -->
    <div class="px-6 py-5 border-t border-gray-100 bg-gray-50/30">
      <h4 class="text-sm font-semibold text-gray-700 flex items-center gap-2 mb-4">
        <Sparkles class="w-4 h-4 text-blue-500" />
        快速理解
      </h4>
      <div class="grid grid-cols-1 md:grid-cols-2 gap-3">
        <div
          v-if="sample.quick_cards.contract_purpose"
          class="p-3 bg-white rounded-lg border border-gray-100"
        >
          <p class="text-xs text-gray-400 mb-1">合同用途</p>
          <p class="text-sm text-gray-700">{{ sample.quick_cards.contract_purpose }}</p>
        </div>
        <div
          v-if="sample.quick_cards.payment_summary"
          class="p-3 bg-white rounded-lg border border-gray-100"
        >
          <p class="text-xs text-gray-400 mb-1">支付条款</p>
          <p class="text-sm text-gray-700">{{ sample.quick_cards.payment_summary }}</p>
        </div>
        <div
          v-if="sample.quick_cards.breach_summary"
          class="p-3 bg-white rounded-lg border border-gray-100"
        >
          <p class="text-xs text-gray-400 mb-1">违约责任</p>
          <p class="text-sm text-gray-700">{{ sample.quick_cards.breach_summary }}</p>
        </div>
        <div
          v-if="sample.missing_clauses.length > 0"
          class="p-3 bg-white rounded-lg border border-gray-100"
        >
          <p class="text-xs text-gray-400 mb-1">缺失条款</p>
          <p class="text-sm text-gray-700">{{ sample.missing_clauses[0].title }}</p>
        </div>
      </div>
    </div>

    <!-- 核心义务 -->
    <div
      v-if="sample.quick_cards.core_obligations?.length"
      class="px-6 py-4 border-t border-gray-100"
    >
      <h4 class="text-sm font-semibold text-gray-700 flex items-center gap-2 mb-3">
        <FileCheck2 class="w-4 h-4 text-green-500" />
        核心义务
      </h4>
      <div class="space-y-2">
        <div
          v-for="(obligation, idx) in sample.quick_cards.core_obligations"
          :key="idx"
          class="flex items-start gap-2"
        >
          <span class="text-gray-400 mt-0.5">•</span>
          <span class="text-sm text-gray-600">{{ obligation }}</span>
        </div>
      </div>
    </div>
  </div>
</template>
