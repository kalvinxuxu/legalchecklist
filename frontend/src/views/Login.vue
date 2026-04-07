<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useLogin } from '@/composables/useAuth'

const router = useRouter()
const login = useLogin()

const email = ref('')
const password = ref('')

async function handleSubmit() {
  try {
    await login.mutateAsync({ email: email.value, password: password.value })
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
          让法律服务<br />触手可及
        </h1>
        <p class="text-gray-400 text-base leading-relaxed max-w-sm">
          基于 RAG 检索增强生成技术，为您提供精准、可信的智能合同审查服务。
        </p>

        <div class="mt-10 space-y-3">
          <div
            v-for="item in ['30 秒完成合同审查', 'RAG 引用溯源，每条建议有法可依', '支持 20+ 合同类型']"
            :key="item"
            class="flex items-center gap-3 text-gray-300 text-sm"
          >
            <div class="w-5 h-5 rounded-full bg-gray-700 flex items-center justify-center flex-shrink-0">
              <svg class="w-3 h-3 text-gray-300" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/>
              </svg>
            </div>
            {{ item }}
          </div>
        </div>
      </div>

      <div class="relative z-10 text-gray-500 text-sm">
        首次注册赠送 10 次免费审查额度
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
          登录账户
        </h2>
        <p class="text-gray-500 text-sm mb-8 animate-fade-up stagger-1">欢迎回来</p>

        <form @submit.prevent="handleSubmit" class="space-y-5">
          <div class="space-y-1.5">
            <label class="text-sm font-medium text-gray-700" for="email">邮箱地址</label>
            <input
              id="email"
              v-model="email"
              type="email"
              required
              placeholder="name@company.com"
              class="w-full h-11 px-4 rounded-lg border border-gray-200 bg-white text-sm text-gray-900 placeholder:text-gray-400 focus:outline-none focus:ring-2 focus:ring-gray-900/10 focus:border-gray-300 transition-all"
            />
          </div>

          <div class="space-y-1.5">
            <label class="text-sm font-medium text-gray-700" for="password">密码</label>
            <input
              id="password"
              v-model="password"
              type="password"
              required
              placeholder="请输入密码"
              class="w-full h-11 px-4 rounded-lg border border-gray-200 bg-white text-sm text-gray-900 placeholder:text-gray-400 focus:outline-none focus:ring-2 focus:ring-gray-900/10 focus:border-gray-300 transition-all"
            />
          </div>

          <button
            type="submit"
            :disabled="login.isPending.value"
            class="w-full h-11 bg-gray-900 text-white text-sm font-semibold rounded-lg hover:bg-gray-800 transition-all disabled:opacity-60 disabled:cursor-not-allowed flex items-center justify-center gap-2"
          >
            <svg v-if="login.isPending.value" class="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/>
            </svg>
            {{ login.isPending.value ? '登录中...' : '登录' }}
          </button>
        </form>

        <div class="mt-6 text-center">
          <p class="text-sm text-gray-500">
            还没有账号？
            <button
              @click="router.push('/register')"
              class="font-medium text-gray-900 hover:underline"
            >
              立即注册
            </button>
          </p>
        </div>
      </div>
    </div>
  </div>
</template>
