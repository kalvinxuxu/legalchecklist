<script setup lang="ts">
import { computed } from 'vue'
import { cn } from '@/lib/utils'

const props = defineProps<{
  class?: string
}>()

const className = computed(() => cn('p-5 pt-0', props.class))
</script>

<template>
  <div :class="className">
    <slot />
  </div>
</template>
