<script setup lang="ts">
import { computed } from 'vue'
import { cn } from '@/lib/utils'

const props = defineProps<{
  class?: string
}>()

const className = computed(() => cn('flex flex-col space-y-1.5 p-4', props.class))
</script>

<template>
  <div :class="className">
    <slot />
  </div>
</template>
