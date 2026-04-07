<script setup lang="ts">
import { computed } from 'vue'
import { ToastRoot, ToastTitle, ToastDescription, ToastClose } from 'radix-vue'
import { cva } from 'class-variance-authority'
import { X } from 'lucide-vue-next'
import { cn } from '@/lib/utils'

const toastVariants = cva(
  'group pointer-events-auto relative flex w-full items-center justify-between space-x-2 overflow-hidden rounded-md border p-4 shadow-lg transition-all data-[swipe=cancel]:translate-x-0 data-[swipe=end]:translate-x-[var(--radix-toast-swipe-end-x)] data-[swipe=move]:translate-x-[var(--radix-toast-swipe-move-x)] data-[swipe=move]:transition-none data-[state=open]:animate-in data-[state=closed]:animate-out data-[swipe=end]:animate-out data-[state=closed]:fade-out-80 data-[state=closed]:slide-out-to-right-full data-[state=open]:slide-in-from-top-full',
  {
    variants: {
      variant: {
        default: 'border-border bg-background text-foreground',
        success: 'border-success-500/30 bg-success-50 text-success-500',
        destructive: 'border-danger-500/30 bg-danger-50 text-danger-500',
      },
    },
    defaultVariants: {
      variant: 'default',
    },
  }
)

const props = withDefaults(defineProps<{
  class?: string
  variant?: 'default' | 'success' | 'destructive'
  title?: string
  description?: string
}>(), {
  variant: 'default',
})

const className = computed(() => cn(toastVariants({ variant: props.variant }), props.class))
</script>

<template>
  <ToastRoot :class="className" v-bind="$attrs">
    <div class="grid gap-1">
      <ToastTitle v-if="title" class="text-sm font-semibold [&+div]:text-xs">
        {{ title }}
      </ToastTitle>
      <ToastDescription v-if="description" class="text-sm opacity-90">
        {{ description }}
      </ToastDescription>
    </div>
    <ToastClose class="absolute right-1 top-1 rounded-sm p-1 opacity-0 group-hover:opacity-100 transition-opacity cursor-pointer">
      <X class="h-4 w-4" />
    </ToastClose>
  </ToastRoot>
</template>
