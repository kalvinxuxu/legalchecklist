<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useRegister } from '@/composables/useAuth'

const router = useRouter()
const register = useRegister()

const form = ref({ email: '', password: '', company_name: '' })

async function handleSubmit() {
  try {
    await register.mutateAsync(form.value)
  } catch {}
}
</script>

<template>
  <div class="min-h-screen bg-white flex">
    <!-- Left brand panel -->
    <div class="hidden lg:flex lg:w-1/2 bg-gray-900 flex-col justify-between p-12 relative overflow-hidden">
      <!-- Subtle grid pattern -->
      <div class="absolute inset-0 opacity-5">
        <div class="absolute inset-0" style="background-image: linear-gradient(rgba(255,255,255,.1) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,.1) 1px, transparent 1px); background-size: 48px 48px;"></div>
      </div>

      <div class="relative z-10">
        <div class="flex items-center gap-2.5 mb-16">
          <div class="w-8 h-8 rounded bg-white flex items-center justify-center">
            <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
              <path d="M3 2L8 6.5L3 11" stroke="#1A1A2E" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
              <path d="M10 2L15 6.5L10 11" stroke="#1A1A2E" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" opacity="0.5"/>
            </svg>
          </div>
          <span class="text-base font-semibold text-white tracking-tight">法务 AI</span>
        </div>

        <h1
          class="text-4xl font-bold text-white mb-6 leading-tight"
          style="font-family: Georgia, 'Noto Serif SC', serif;"
        >
          开始您的<br />智能审查之旅
        </h1>
        <p class="text-gray-400 text-base leading-relaxed max-w-sm">
          首次注册即赠送 10 次免费审查额度，体验 AI 驱动的精准合同分析。
        </p>

        <div class="mt-10 grid grid-cols-3 gap-4">
          <div
            v-for="stat in [{v:'10+',l:'免费额度'}, {v:'30s',l:'审查速度'}, {v:'99%',l:'识别准确率'}]"
            :key="stat.l"
            class="p-4 bg-white/5 border border-white/10 rounded-xl text-center"
          >
            <div class="text-2xl font-bold text-white mb-1" style="font-family: Georgia, serif;">
              {{ stat.v }}
            </div>
            <div class="text-xs text-gray-400">{{ stat.l }}</div>
          </div>
        </div>
      </div>

      <div class="relative z-10 text-gray-500 text-sm">
        已有账号？
        <button @click="router.push('/login')" class="text-white hover:text-gray-300 ml-1 transition-colors">
          立即登录
        </button>
      </div>
    </div>

    <!-- Right form panel -->
    <div class="flex-1 flex items-center justify-center p-8">
      <div class="w-full max-w-sm">
        <!-- Mobile logo -->
        <div class="lg:hidden flex items-center gap-2 mb-10">
          <div class="w-7 h-7 rounded bg-gray-900 flex items-center justify-center">
            <svg width="14" height="14" viewBox="0 0 16 16" fill="none">
              <path d="M3 2L8 6.5L3 11" stroke="white" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
              <path d="M10 2L15 6.5L10 11" stroke="white" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" opacity="0.5"/>
            </svg>
          </div>
          <span class="text-sm font-semibold text-gray-900">法务 AI</span>
        </div>

        <h2
          class="text-3xl font-bold text-gray-900 mb-2 animate-fade-up"
          style="font-family: Georgia, 'Noto Serif SC', serif;"
        >
          创建账户
        </h2>
        <p class="text-gray-500 text-sm mb-8 animate-fade-up stagger-1">填写以下信息完成注册</p>

        <form @submit.prevent="handleSubmit" class="space-y-5">
          <div class="space-y-1.5">
            <label class="text-sm font-medium text-gray-700" for="company">公司名称</label>
            <input
              id="company"
              v-model="form.company_name"
              type="text"
              required
              placeholder="示例：北京科技有限公司"
              class="w-full h-11 px-4 rounded-lg border border-gray-200 bg-white text-sm text-gray-900 placeholder:text-gray-400 focus:outline-none focus:ring-2 focus:ring-gray-900/10 focus:border-gray-300 transition-all"
            />
          </div>

          <div class="space-y-1.5">
            <label class="text-sm font-medium text-gray-700" for="email">邮箱地址</label>
            <input
              id="email"
              v-model="form.email"
              type="email"
              required
              placeholder="name@company.com"
              class="w-full h-11 px-4 rounded-lg border border-gray-200 bg-white text-sm text-gray-900 placeholder:text-gray-400 focus:outline-none focus:ring-2 focus:ring-gray-900/10 focus:border-gray-300 transition-all"
            />
          </div>

          <div class="space-y-1.5">
            <label class="text-sm font-medium text-gray-700" for="password">设置密码</label>
            <input
              id="password"
              v-model="form.password"
              type="password"
              required
              placeholder="至少 8 位，包含字母和数字"
              minlength="8"
              class="w-full h-11 px-4 rounded-lg border border-gray-200 bg-white text-sm text-gray-900 placeholder:text-gray-400 focus:outline-none focus:ring-2 focus:ring-gray-900/10 focus:border-gray-300 transition-all"
            />
          </div>

          <p class="text-xs text-gray-500 text-center leading-relaxed">
            注册即表示同意
            <button class="font-medium text-gray-900 hover:underline">服务条款</button>
            和
            <button class="font-medium text-gray-900 hover:underline">隐私政策</button>
          </p>

          <button
            type="submit"
            :disabled="register.isPending.value"
            class="w-full h-11 bg-gray-900 text-white text-sm font-semibold rounded-lg hover:bg-gray-800 transition-all disabled:opacity-60 disabled:cursor-not-allowed flex items-center justify-center gap-2"
          >
            <svg v-if="register.isPending.value" class="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/>
            </svg>
            {{ register.isPending.value ? '注册中...' : '创建账户' }}
          </button>
        </form>

        <div class="mt-6 text-center">
          <p class="text-sm text-gray-500">
            已有账号？
            <button
              @click="router.push('/login')"
              class="font-medium text-gray-900 hover:underline"
            >
              立即登录
            </button>
          </p>
        </div>
      </div>
    </div>
  </div>
</template>
