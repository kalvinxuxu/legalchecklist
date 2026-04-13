<script setup lang="ts">
import { computed } from 'vue'
import { Upload, FileSearch, FileText } from 'lucide-vue-next'

interface Step {
  number: string
  title: string
  description: string
  icon: 'upload' | 'search' | 'report'
}

const props = defineProps<{
  step: Step
  isLast?: boolean
}>()

const isLast = computed(() => props.isLast ?? false)

const iconComponent = computed(() => {
  const icons = {
    upload: Upload,
    search: FileSearch,
    report: FileText,
  }
  return icons[props.step.icon] || Upload
})
</script>

<template>
  <div class="flex items-start gap-6">
    <div class="relative flex-shrink-0">
      <div
        class="w-14 h-14 rounded-full bg-gray-900 text-white flex items-center justify-center"
        style="font-family: Georgia, serif;"
      >
        <component :is="iconComponent" class="w-6 h-6" />
      </div>
      <!-- 连接线 -->
      <div
        v-if="!isLast"
        class="absolute top-14 left-1/2 w-0.5 h-12 bg-gray-200 -translate-x-1/2"
      />
    </div>
    <div class="flex-1 pt-2">
      <h3 class="text-xl font-semibold text-gray-900 mb-2">{{ step.title }}</h3>
      <p class="text-gray-500">{{ step.description }}</p>
    </div>
  </div>
</template>
