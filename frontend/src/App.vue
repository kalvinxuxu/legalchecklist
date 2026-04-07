<script setup lang="ts">
import { RouterView } from 'vue-router'
import Toast from '@/components/ui/toast.vue'
import { useToast } from '@/composables/useToast'

const { toasts } = useToast()
</script>

<template>
  <ToastProvider>
    <RouterView />
    <div class="fixed top-0 right-0 z-[100] flex flex-col gap-2 p-4 max-w-[420px] w-full pointer-events-none">
      <Toast
        v-for="t in toasts"
        :key="t.id"
        :title="t.title"
        :description="t.description"
        :variant="t.variant"
        class="pointer-events-auto"
      />
    </div>
  </ToastProvider>
</template>
