<script setup lang="ts">
import { computed } from 'vue'
import { SelectItem, SelectItemText, SelectItemIndicator } from 'radix-vue'
import { Check } from 'lucide-vue-next'
import { cn } from '@/lib/utils'

const props = defineProps<{
  class?: string
  value: string
}>()

const itemClass = computed(() => cn(
  'relative flex w-full cursor-pointer select-none items-center rounded-sm py-1.5 pl-2 pr-8 text-sm outline-none hover:bg-accent focus:bg-accent data-[disabled]:pointer-events-none data-[disabled]:opacity-50',
  props.class
))
</script>

<template>
  <SelectItem :class="itemClass" :value="value" v-bind="$attrs">
    <SelectItemIndicator class="absolute right-2 flex h-3.5 w-3.5 items-center justify-center">
      <Check class="h-4 w-4" />
    </SelectItemIndicator>
    <SelectItemText>
      <slot />
    </SelectItemText>
  </SelectItem>
</template>
