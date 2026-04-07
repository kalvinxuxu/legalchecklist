<script setup lang="ts">
import { computed } from 'vue'
import { cn } from '@/lib/utils'

const props = defineProps<{
  class?: string
}>()

const className = computed(() => cn(
  'rounded-xl border border-ivory-200 bg-white shadow-sm',
  props.class
))
</script>

<template>
  <div :class="className">
    <slot />
  </div>
</template>
