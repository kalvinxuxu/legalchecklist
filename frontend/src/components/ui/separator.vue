<script setup lang="ts">
import { computed } from 'vue'
import { cn } from '@/lib/utils'

const props = defineProps<{
  class?: string
}>()

const className = computed(() => cn('shrink-0 bg-border', props.class))
</script>

<template>
  <div :class="className" style="height: 1px; width: 100%;" />
</template>
