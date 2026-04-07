<script setup lang="ts">
import { computed } from 'vue'
import { TabsContent } from 'radix-vue'
import { cn } from '@/lib/utils'

const props = defineProps<{
  class?: string
}>()

const className = computed(() => cn('mt-4 focus-visible:outline-none', props.class))
</script>

<template>
  <TabsContent :class="className" v-bind="$attrs">
    <slot />
  </TabsContent>
</template>
