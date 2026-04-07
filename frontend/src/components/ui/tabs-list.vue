<script setup lang="ts">
import { computed } from 'vue'
import { TabsList } from 'radix-vue'
import { cn } from '@/lib/utils'

const props = defineProps<{
  class?: string
}>()

const className = computed(() => cn('inline-flex items-center justify-center border-b border-border', props.class))
</script>

<template>
  <TabsList :class="className" v-bind="$attrs">
    <slot />
  </TabsList>
</template>
