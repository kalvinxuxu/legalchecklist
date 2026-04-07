<script setup lang="ts">
import { computed } from 'vue'
import { SelectRoot, SelectTrigger, SelectValue, SelectContent, SelectItem, SelectItemText, SelectPortal, SelectViewport } from 'radix-vue'
import { ChevronDown } from 'lucide-vue-next'
import { cn } from '@/lib/utils'

const props = withDefaults(defineProps<{
  class?: string
  modelValue?: string
}>(), {
  modelValue: '',
})

const emit = defineEmits<{
  'update:modelValue': [value: string]
}>()

const triggerClass = computed(() => cn(
  'flex h-9 w-full items-center justify-between whitespace-nowrap rounded-md border border-input bg-transparent px-3 py-2 text-sm shadow-sm ring-offset-background placeholder:text-muted-foreground focus:outline-none focus:ring-1 focus:ring-ring disabled:cursor-not-allowed disabled:opacity-50',
  props.class
))
</script>

<template>
  <SelectRoot
    v-bind="$attrs"
    :model-value="props.modelValue"
    @update:model-value="emit('update:modelValue', $event as string)"
  >
    <SelectTrigger :class="triggerClass">
      <SelectValue :placeholder="($attrs.placeholder as string) || '请选择'" />
      <ChevronDown class="h-4 w-4 opacity-50" />
    </SelectTrigger>
    <SelectPortal>
      <SelectContent class="relative z-50 min-w-[8rem] overflow-hidden rounded-md border border-border bg-popover text-popover-foreground shadow-md data-[state=open]:animate-in data-[state=closed]:animate-out">
        <SelectViewport class="p-1">
          <slot />
        </SelectViewport>
      </SelectContent>
    </SelectPortal>
  </SelectRoot>
</template>
