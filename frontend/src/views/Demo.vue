<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { ArrowRight, CheckCircle2, Sparkles, FileText } from 'lucide-vue-next'
import { demoSamples } from '@/data/demo-samples'
import DemoStepCard from '@/components/demo/DemoStepCard.vue'
import DemoReportCard from '@/components/demo/DemoReportCard.vue'

const router = useRouter()

// 当前选中的合同类型 Tab
const activeTab = ref<string>('NDA')

// 步骤数据
const steps = [
  {
    number: '1',
    title: '上传合同',
    description: '支持 PDF、Word 格式，点击上传或拖拽文件到上传区',
    icon: 'upload' as const,
  },
  {
    number: '2',
    title: 'AI 智能审查',
    description: '30 秒内完成条款解析，识别风险点并给出修改建议',
    icon: 'search' as const,
  },
  {
    number: '3',
    title: '查看报告',
    description: '生成可视化报告，支持一键导出 Word 文档',
    icon: 'report' as const,
  },
]

// Tab 选项
const tabs = [
  { value: 'NDA', label: 'NDA 保密协议' },
  { value: '劳动合同', label: '劳动合同' },
  { value: '采购合同', label: '采购合同' },
]

// 获取当前显示的示例
const currentSample = computed(() => {
  return demoSamples.find((s) => s.contract_type === activeTab.value) || demoSamples[0]
})

// 功能亮点
const highlights = [
  {
    icon: Sparkles,
    title: '30 秒智能审查',
    description: 'AI 驱动的条款解析，快速识别风险点',
    color: 'bg-blue-50',
    iconColor: 'text-blue-600',
  },
  {
    icon: CheckCircle2,
    title: 'RAG 引用溯源',
    description: '每条建议附带法条依据，结论可信',
    color: 'bg-green-50',
    iconColor: 'text-green-600',
  },
  {
    icon: FileText,
    title: '一键导出',
    description: '生成专业报告，支持 Word 格式',
    color: 'bg-amber-50',
    iconColor: 'text-amber-600',
  },
]
</script>

<template>
  <div class="min-h-screen bg-white">
    <!-- Navigation -->
    <nav class="fixed top-0 inset-x-0 z-50 bg-white/90 backdrop-blur-md border-b border-gray-100">
      <div class="max-w-5xl mx-auto px-8 h-16 flex items-center justify-between">
        <div class="flex items-center gap-2">
          <div class="w-7 h-7 rounded bg-black flex items-center justify-center">
            <svg width="14" height="14" viewBox="0 0 16 16" fill="none">
              <path
                d="M3 2L8 6.5L3 11"
                stroke="white"
                stroke-width="1.5"
                stroke-linecap="round"
                stroke-linejoin="round"
              />
              <path
                d="M10 2L15 6.5L10 11"
                stroke="white"
                stroke-width="1.5"
                stroke-linecap="round"
                stroke-linejoin="round"
                opacity="0.5"
              />
            </svg>
          </div>
          <span class="text-sm font-semibold tracking-tight text-gray-900">法务 AI</span>
        </div>
        <div class="flex items-center gap-6">
          <button
            @click="router.push('/login')"
            class="text-sm font-medium text-gray-500 hover:text-gray-900 transition-colors"
          >
            登录
          </button>
          <button
            @click="router.push('/register')"
            class="px-5 py-2 text-sm font-semibold text-white bg-gray-900 rounded-full hover:bg-gray-800 transition-colors"
          >
            开始使用
          </button>
        </div>
      </div>
    </nav>

    <!-- Hero -->
    <section class="pt-32 pb-16 px-8">
      <div class="max-w-3xl mx-auto text-center">
        <p class="text-sm font-medium text-gray-400 tracking-wide uppercase mb-6">
          智能引导与成果展示
        </p>
        <h1
          class="text-4xl md:text-5xl font-bold text-gray-900 leading-[1.1] mb-6"
          style="font-family: Georgia, 'Noto Serif SC', serif;"
        >
          体验 AI 合同审查<br class="hidden md:block" />全流程
        </h1>
        <p class="text-lg text-gray-500 leading-relaxed max-w-xl mx-auto">
          了解如何通过法务 AI 平台完成合同审查，从上传到报告只需三步。
        </p>
      </div>
    </section>

    <!-- Steps Guide -->
    <section class="py-16 px-8 bg-gray-50/50">
      <div class="max-w-2xl mx-auto">
        <h2
          class="text-2xl md:text-3xl font-bold text-gray-900 mb-12 text-center"
          style="font-family: Georgia, 'Noto Serif SC', serif;"
        >
          三步完成合同审查
        </h2>
        <div class="space-y-10">
          <DemoStepCard
            v-for="(step, i) in steps"
            :key="step.number"
            :step="step"
            :is-last="i === steps.length - 1"
          />
        </div>
      </div>
    </section>

    <!-- Demo Report Showcase -->
    <section class="py-24 px-8">
      <div class="max-w-4xl mx-auto">
        <div class="text-center mb-12">
          <h2
            class="text-2xl md:text-3xl font-bold text-gray-900 mb-4"
            style="font-family: Georgia, 'Noto Serif SC', serif;"
          >
            示例审查报告
          </h2>
          <p class="text-gray-500 max-w-lg mx-auto">
            查看不同类型合同的 AI 审查结果，体验风险识别和条款分析能力
          </p>
        </div>

        <!-- Tabs -->
        <div class="flex justify-center gap-2 mb-8">
          <button
            v-for="tab in tabs"
            :key="tab.value"
            @click="activeTab = tab.value"
            :class="[
              'px-5 py-2.5 text-sm font-medium rounded-full transition-all',
              activeTab === tab.value
                ? 'bg-gray-900 text-white'
                : 'bg-white text-gray-600 border border-gray-200 hover:border-gray-300',
            ]"
          >
            {{ tab.label }}
          </button>
        </div>

        <!-- Report Card -->
        <Transition name="fade" mode="out-in">
          <DemoReportCard :key="currentSample.id" :sample="currentSample" />
        </Transition>
      </div>
    </section>

    <!-- Features Highlight -->
    <section class="py-16 px-8 bg-gray-50/50">
      <div class="max-w-4xl mx-auto">
        <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div
            v-for="item in highlights"
            :key="item.title"
            class="p-6 bg-white rounded-xl border border-gray-100 text-center"
          >
            <div
              :class="[item.color, 'w-12 h-12 rounded-xl flex items-center justify-center mx-auto mb-4']"
            >
              <component :is="item.icon" :class="['w-6 h-6', item.iconColor]" />
            </div>
            <h3 class="font-semibold text-gray-900 mb-2">{{ item.title }}</h3>
            <p class="text-sm text-gray-500">{{ item.description }}</p>
          </div>
        </div>
      </div>
    </section>

    <!-- CTA -->
    <section class="py-24 px-8">
      <div class="max-w-2xl mx-auto text-center">
        <h2
          class="text-3xl md:text-4xl font-bold text-gray-900 mb-4"
          style="font-family: Georgia, 'Noto Serif SC', serif;"
        >
          立即体验智能审查
        </h2>
        <p class="text-gray-500 text-lg mb-8">首次注册即送 10 次免费审查额度</p>
        <div class="flex flex-wrap gap-3 justify-center">
          <button
            @click="router.push('/register')"
            class="px-7 py-3.5 bg-gray-900 text-white text-sm font-semibold rounded-full hover:bg-gray-800 transition-all hover:shadow-lg flex items-center gap-2"
          >
            免费注册
            <ArrowRight class="w-4 h-4" />
          </button>
          <button
            @click="router.push('/login')"
            class="px-7 py-3.5 bg-white text-gray-700 text-sm font-semibold rounded-full border border-gray-200 hover:bg-gray-50 hover:border-gray-300 transition-all"
          >
            登录已有账号
          </button>
        </div>
      </div>
    </section>

    <!-- Footer -->
    <footer class="border-t border-gray-100 py-8 px-8">
      <div class="max-w-5xl mx-auto flex items-center justify-between">
        <div class="flex items-center gap-2">
          <div class="w-6 h-6 rounded bg-black flex items-center justify-center">
            <svg width="12" height="12" viewBox="0 0 16 16" fill="none">
              <path
                d="M3 2L8 6.5L3 11"
                stroke="white"
                stroke-width="1.5"
                stroke-linecap="round"
                stroke-linejoin="round"
              />
              <path
                d="M10 2L15 6.5L10 11"
                stroke="white"
                stroke-width="1.5"
                stroke-linecap="round"
                stroke-linejoin="round"
                opacity="0.5"
              />
            </svg>
          </div>
          <span class="text-xs font-medium text-gray-500">法务 AI</span>
        </div>
        <p class="text-xs text-gray-400">© 2024 法务 AI. 智能合同审查服务</p>
      </div>
    </footer>
  </div>
</template>

<style scoped>
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}
.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
