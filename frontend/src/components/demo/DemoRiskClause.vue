<script setup lang="ts">
import type { DemoRiskClause } from '@/data/demo-samples'
import { RISK_LEVEL_MAP } from '@/lib/utils'

defineProps<{
  clause: DemoRiskClause
}>()

function truncateText(text: string, maxLen: number): string {
  return text.length > maxLen ? text.slice(0, maxLen) + '...' : text
}
</script>

<template>
  <div
    class="p-4 rounded-md bg-gray-50 border-l-[3px]"
    :style="{ borderLeftColor: RISK_LEVEL_MAP[clause.risk_level]?.color }"
  >
    <div class="flex items-start justify-between gap-3 mb-2">
      <span class="font-medium text-gray-900">{{ clause.title }}</span>
      <span
        class="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium flex-shrink-0"
        :class="RISK_LEVEL_MAP[clause.risk_level]?.variant === 'destructive' ? 'bg-red-100 text-red-700' :
               RISK_LEVEL_MAP[clause.risk_level]?.variant === 'warning' ? 'bg-amber-100 text-amber-700' :
               'bg-green-100 text-green-700'"
      >
        {{ RISK_LEVEL_MAP[clause.risk_level]?.label }}
      </span>
    </div>
    <p class="text-sm text-gray-500 italic mb-2">
      "{{ truncateText(clause.original_text, 100) }}"
    </p>
    <p v-if="clause.risk_description" class="text-sm text-gray-700 mb-1">
      {{ clause.risk_description }}
    </p>
    <p v-if="clause.suggestion" class="text-sm text-gray-500">
      <span class="font-medium">建议:</span> {{ clause.suggestion }}
    </p>
  </div>
</template>
