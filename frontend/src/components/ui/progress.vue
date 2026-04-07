<script setup lang="ts">
import { computed } from 'vue'
import { ProgressRoot, ProgressIndicator } from 'radix-vue'
import { cn } from '@/lib/utils'

const props = withDefaults(defineProps<{
  class?: string
  modelValue?: number
}>(), {
  modelValue: 0,
})

const className = computed(() => cn(
  'relative h-2 w-full overflow-hidden rounded-full bg-ivory-200',
  props.class
))
</script>

<template>
  <ProgressRoot :class="className" :value="props.modelValue">
    <ProgressIndicator
      class="h-full bg-navy-700 transition-all duration-300"
      :style="`width: ${props.modelValue}%`"
    />
  </ProgressRoot>
</template>
