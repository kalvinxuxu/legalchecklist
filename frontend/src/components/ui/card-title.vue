<script setup lang="ts">
import { computed } from 'vue'
import { cn } from '@/lib/utils'

const props = defineProps<{
  class?: string
}>()

const className = computed(() => cn('text-base font-medium leading-none tracking-tight', props.class))
</script>

<template>
  <h3 :class="className">
    <slot />
  </h3>
</template>
