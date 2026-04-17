<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ShieldCheck, Zap, TrendingUp, BookOpen, FileSearch, CheckCircle2, ArrowRight } from 'lucide-vue-next'

const router = useRouter()
const mounted = ref(false)

onMounted(() => {
  setTimeout(() => mounted.value = true, 100)
})

const features = [
  {
    icon: Zap,
    title: '2-3 分钟深度审查',
    description: 'AI 深度分析每一条条款，精准识别风险点与机会点，比人工审查更全面',
  },
  {
    icon: ShieldCheck,
    title: 'RAG 引用溯源',
    description: '每条建议均附带法条依据，来源可查，结论可信',
  },
  {
    icon: BookOpen,
    title: '法律知识库',
    description: '基于海量法律文书训练的 AI 模型，覆盖 20+ 合同类型',
  },
  {
    icon: FileSearch,
    title: '条款定位',
    description: '自然语言提问，AI 精确定位合同条款并给出解读',
  },
  {
    icon: CheckCircle2,
    title: '一键导出报告',
    description: '审查完成后生成专业报告，支持 Word 格式导出，即刻分享给团队',
  },
  {
    icon: TrendingUp,
    title: '越用越懂你公司',
    description: 'AI 学习你的审查偏好与业务场景，每次审查都比上一次更懂你的需求',
  },
]

const stats = [
  { value: '10,000+', label: '审查合同数' },
  { value: '99.2%', label: '风险识别准确率' },
  { value: '2-3min', label: '深度审查时间' },
  { value: '20+', label: '支持合同类型' },
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
              <path d="M3 2L8 6.5L3 11" stroke="white" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
              <path d="M10 2L15 6.5L10 11" stroke="white" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" opacity="0.5"/>
            </svg>
          </div>
          <span class="text-sm font-semibold tracking-tight text-gray-900">法务AI Box</span>
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
    <section class="pt-32 pb-24 px-8">
      <div class="max-w-3xl mx-auto text-center">
        <p class="text-sm font-medium text-gray-400 tracking-wide uppercase mb-6 animate-fade-up">
          AI 驱动的智能合同审查平台
        </p>
        <h1
          class="text-5xl md:text-6xl font-bold text-gray-900 leading-[1.1] mb-6 animate-fade-up stagger-1"
          style="font-family: Georgia, 'Noto Serif SC', 'Times New Roman', serif;"
        >
          让合同审查<br class="hidden md:block" />精准高效
        </h1>
        <p
          class="text-xl text-gray-500 leading-relaxed mb-10 max-w-xl mx-auto animate-fade-up stagger-2"
        >
          基于 RAG 检索增强生成技术，2-3 分钟完成深度合同分析。
          每一条审查建议都附带法条依据，让法律服务触手可及。
          <strong class="text-gray-700">越用越懂你公司的法务 AI。</strong>
        </p>
        <div class="flex flex-wrap gap-3 justify-center animate-fade-up stagger-3">
          <button
            @click="router.push('/register')"
            class="px-7 py-3.5 bg-gray-900 text-white text-sm font-semibold rounded-full hover:bg-gray-800 transition-all hover:shadow-lg flex items-center gap-2"
          >
            立即开始
            <ArrowRight class="w-4 h-4" />
          </button>
          <button
            @click="router.push('/demo')"
            class="px-7 py-3.5 bg-white text-gray-700 text-sm font-semibold rounded-full border border-gray-200 hover:bg-gray-50 hover:border-gray-300 transition-all"
          >
            观看演示
          </button>
        </div>
      </div>
    </section>

    <!-- Stats -->
    <section class="border-y border-gray-100 py-12 px-8 bg-gray-50/50">
      <div class="max-w-4xl mx-auto">
        <div class="grid grid-cols-2 md:grid-cols-4 gap-8">
          <div
            v-for="(stat, i) in stats"
            :key="stat.label"
            class="text-center animate-fade-up"
            :style="{ animationDelay: `${i * 0.1}s` }"
          >
            <div
              class="text-3xl font-bold text-gray-900 mb-1"
              style="font-family: Georgia, serif;"
            >
              {{ stat.value }}
            </div>
            <div class="text-sm text-gray-500">{{ stat.label }}</div>
          </div>
        </div>
      </div>
    </section>

    <!-- Features -->
    <section class="py-24 px-8">
      <div class="max-w-4xl mx-auto">
        <div class="text-center mb-16">
          <h2
            class="text-3xl md:text-4xl font-bold text-gray-900 mb-4 animate-fade-up"
            style="font-family: Georgia, 'Noto Serif SC', serif;"
          >
            为什么选择法务AI Box
          </h2>
          <p class="text-gray-500 text-lg max-w-lg mx-auto animate-fade-up stagger-1">
            一套完整的智能合同审查系统，全程 AI 驱动
          </p>
        </div>

        <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div
            v-for="(feature, i) in features"
            :key="feature.title"
            class="p-8 bg-white rounded-2xl border border-gray-100 hover:border-gray-200 hover:shadow-lg transition-all animate-fade-up"
            :style="{ animationDelay: `${i * 0.08}s` }"
          >
            <div class="flex items-start gap-5">
              <div class="w-10 h-10 rounded-xl bg-gray-100 flex items-center justify-center flex-shrink-0">
                <component :is="feature.icon" class="w-5 h-5 text-gray-700" />
              </div>
              <div>
                <h3 class="text-base font-semibold text-gray-900 mb-2">{{ feature.title }}</h3>
                <p class="text-sm text-gray-500 leading-relaxed">{{ feature.description }}</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- How it works -->
    <section class="py-24 px-8 bg-gray-50/50">
      <div class="max-w-3xl mx-auto">
        <div class="text-center mb-16">
          <h2
            class="text-3xl md:text-4xl font-bold text-gray-900 mb-4 animate-fade-up"
            style="font-family: Georgia, 'Noto Serif SC', serif;"
          >
            三步完成合同审查
          </h2>
        </div>

        <div class="space-y-8">
          <div
            v-for="(step, i) in [
              { n: '1', title: '上传合同', desc: '支持 PDF、Word 格式，点击上传或拖拽文件' },
              { n: '2', title: 'AI 分析', desc: '2-3 分钟内完成深度条款解析，识别风险并给出建议' },
              { n: '3', title: '查看报告', desc: '生成可视化报告，支持导出 Word 文档' },
            ]"
            :key="step.n"
            class="flex items-start gap-6 animate-fade-up"
            :style="{ animationDelay: `${i * 0.15}s` }"
          >
            <div
              class="w-12 h-12 rounded-full bg-gray-900 text-white flex items-center justify-center text-lg font-bold flex-shrink-0"
              style="font-family: Georgia, serif;"
            >
              {{ step.n }}
            </div>
            <div class="pt-2">
              <h3 class="text-lg font-semibold text-gray-900 mb-1">{{ step.title }}</h3>
              <p class="text-gray-500">{{ step.desc }}</p>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- CTA -->
    <section class="py-24 px-8">
      <div class="max-w-2xl mx-auto text-center">
        <h2
          class="text-3xl md:text-4xl font-bold text-gray-900 mb-4 animate-fade-up"
          style="font-family: Georgia, 'Noto Serif SC', serif;"
        >
          立即体验智能审查
        </h2>
        <p class="text-gray-500 text-lg mb-8 animate-fade-up stagger-1">
          首次注册即送 10 次免费审查额度
        </p>
        <button
          @click="router.push('/register')"
          class="px-8 py-4 bg-gray-900 text-white text-sm font-semibold rounded-full hover:bg-gray-800 transition-all hover:shadow-lg animate-fade-up stagger-2"
        >
          免费注册
        </button>
      </div>
    </section>

    <!-- Footer -->
    <footer class="border-t border-gray-100 py-8 px-8">
      <div class="max-w-5xl mx-auto flex items-center justify-between">
        <div class="flex items-center gap-2">
          <div class="w-6 h-6 rounded bg-black flex items-center justify-center">
            <svg width="12" height="12" viewBox="0 0 16 16" fill="none">
              <path d="M3 2L8 6.5L3 11" stroke="white" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
              <path d="M10 2L15 6.5L10 11" stroke="white" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" opacity="0.5"/>
            </svg>
          </div>
          <span class="text-xs font-medium text-gray-500">法务AI Box</span>
        </div>
        <p class="text-xs text-gray-400">
          © 2024 法务AI Box. 智能合同审查服务
        </p>
      </div>
    </footer>
  </div>
</template>
