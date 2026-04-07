<script setup lang="ts">
import { computed } from 'vue'
import { TabsTrigger } from 'radix-vue'
import { cn } from '@/lib/utils'

const props = defineProps<{
  class?: string
}>()

const className = computed(() => cn(
  'inline-flex items-center justify-center gap-2 px-4 py-2.5 text-sm font-medium text-muted-foreground border-b-2 border-transparent transition-colors hover:text-foreground focus-visible:outline-none disabled:pointer-events-none',
  'data-[state=active]:text-primary-600 data-[state=active]:border-primary-600',
  props.class
))
</script>

<template>
  <TabsTrigger :class="className" v-bind="$attrs">
    <slot />
  </TabsTrigger>
</template>
