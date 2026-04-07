<script setup lang="ts">
import { computed } from 'vue'
import { cva, type VariantProps } from 'class-variance-authority'
import { cn } from '@/lib/utils'

const badgeVariants = cva(
  'inline-flex items-center rounded-lg px-2.5 py-1 text-xs font-semibold',
  {
    variants: {
      variant: {
        default: 'bg-ivory-100 text-warm-gray',
        primary: 'bg-navy-100 text-navy-800',
        secondary: 'bg-ivory-200 text-navy-700',
        success: 'bg-success-50 text-success-600',
        warning: 'bg-amber-50 text-amber-700',
        destructive: 'bg-danger-50 text-danger-600',
        info: 'bg-sky-50 text-sky-600',
        outline: 'border border-ivory-300 text-navy-700 bg-transparent',
      },
    },
    defaultVariants: {
      variant: 'default',
    },
  }
)

type BadgeVariant = VariantProps<typeof badgeVariants>

const props = withDefaults(defineProps<{
  variant?: BadgeVariant['variant']
  class?: string
}>(), {
  variant: 'default',
})

const className = computed(() => cn(badgeVariants({ variant: props.variant }), props.class))
</script>

<template>
  <div :class="className">
    <slot />
  </div>
</template>
