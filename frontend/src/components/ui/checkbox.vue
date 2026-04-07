<script setup lang="ts">
import { computed } from 'vue'
import { CheckboxRoot, CheckboxIndicator } from 'radix-vue'
import { Check } from 'lucide-vue-next'
import { cn } from '@/lib/utils'

const props = withDefaults(defineProps<{
  class?: string
  modelValue?: boolean
  disabled?: boolean
  defaultChecked?: boolean
}>(), {
  modelValue: false,
})

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
}>()

const className = computed(() => cn(
  'peer h-4 w-4 shrink-0 rounded-sm border border-primary-600 shadow focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring disabled:cursor-not-allowed disabled:opacity-50 data-[state=checked]:bg-primary-600 data-[state=checked]:text-white',
  props.class
))
</script>

<template>
  <CheckboxRoot
    v-bind="$attrs"
    :class="className"
    :checked="props.modelValue"
    :disabled="props.disabled"
    @update:checked="emit('update:modelValue', $event)"
  >
    <CheckboxIndicator class="flex items-center justify-center text-current">
      <Check class="h-3 w-3" />
    </CheckboxIndicator>
  </CheckboxRoot>
</template>
