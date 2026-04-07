<script setup lang="ts">
import { computed } from 'vue'
import { TabsRoot } from 'radix-vue'
import { cn } from '@/lib/utils'

const props = defineProps<{
  class?: string
}>()

const className = computed(() => cn('flex flex-col h-full', props.class))
</script>

<template>
  <TabsRoot :class="className" v-bind="$attrs">
    <slot />
  </TabsRoot>
</template>
