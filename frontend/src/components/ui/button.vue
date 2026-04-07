<script setup lang="ts">
import { computed } from 'vue'
import { cva, type VariantProps } from 'class-variance-authority'
import { Loader2 } from 'lucide-vue-next'
import { cn } from '@/lib/utils'

const buttonVariants = cva(
  'inline-flex items-center justify-center gap-2 whitespace-nowrap rounded-xl text-sm font-semibold transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-navy-800/20 disabled:pointer-events-none disabled:opacity-50 cursor-pointer',
  {
    variants: {
      variant: {
        default: 'bg-navy-800 text-white hover:bg-navy-900 shadow-sm hover:shadow-md hover:-translate-y-0.5',
        destructive: 'bg-danger-500 text-white hover:bg-danger-600 shadow-sm hover:-translate-y-0.5',
        outline: 'border border-ivory-300 bg-white text-navy-800 hover:bg-ivory-50 hover:-translate-y-0.5',
        secondary: 'bg-ivory-100 text-navy-800 hover:bg-ivory-200',
        ghost: 'hover:bg-ivory-100 text-navy-800',
        link: 'text-navy-700 underline-offset-4 hover:underline',
        success: 'bg-success-500 text-white hover:bg-success-600 shadow-sm hover:-translate-y-0.5',
        warning: 'bg-amber-500 text-white hover:bg-amber-600 shadow-sm hover:-translate-y-0.5',
      },
      size: {
        default: 'h-10 px-5 py-2',
        sm: 'h-8 px-3 text-xs rounded-lg',
        lg: 'h-12 px-8 text-base rounded-xl',
        icon: 'h-10 w-10',
      },
    },
    defaultVariants: {
      variant: 'default',
      size: 'default',
    },
  }
)

type ButtonVariant = VariantProps<typeof buttonVariants>

const props = withDefaults(defineProps<{
  variant?: ButtonVariant['variant']
  size?: ButtonVariant['size']
  loading?: boolean
  disabled?: boolean
  class?: string
  as?: string | object
}>(), {
  variant: 'default',
  size: 'default',
  as: 'button',
})

const variant = computed(() => props.variant)
const size = computed(() => props.size)
</script>

<template>
  <component
    :is="props.as"
    :class="cn(buttonVariants({ variant, size }), props.class)"
    :disabled="props.disabled || props.loading"
  >
    <Loader2 v-if="props.loading" class="h-4 w-4 animate-spin" />
    <slot />
  </component>
</template>
