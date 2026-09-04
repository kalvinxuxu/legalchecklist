<script setup lang="ts">
import { computed } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { User, Mail, Building2, CreditCard, FileText, Calendar, Shield, Crown, Zap } from 'lucide-vue-next'

const authStore = useAuthStore()

const user = computed(() => authStore.user)
const tenant = computed(() => user.value?.tenant)

// 套餐计划显示映射
const planLabels: Record<string, { label: string; description: string; color: string }> = {
  free: { label: '免费版', description: '基础功能', color: 'bg-gray-100 text-gray-700' },
  basic: { label: '基础版', description: '适合小团队', color: 'bg-blue-100 text-blue-700' },
  pro: { label: '专业版', description: '适合企业', color: 'bg-purple-100 text-purple-700' },
  enterprise: { label: '企业版', description: '无限额度', color: 'bg-amber-100 text-amber-700' },
}

const currentPlan = computed(() => {
  const plan = tenant.value?.plan || 'free'
  return planLabels[plan] || planLabels.free
})

const formatDate = (dateStr?: string) => {
  if (!dateStr) return '-'
  return new Date(dateStr).toLocaleDateString('zh-CN', {
    year: 'numeric',
    month: 'long',
    day: 'numeric'
  })
}
</script>

<template>
  <div class="flex flex-col h-full bg-ivory-50">
    <!-- Header -->
    <div class="px-6 py-5 bg-white border-b border-ivory-200">
      <div>
        <h1 class="text-xl font-bold text-navy-900" style="font-family: 'Noto Serif SC', Georgia, serif;">
          账户信息
        </h1>
        <p class="text-sm text-warm-gray mt-0.5">管理您的个人信息和账户设置</p>
      </div>
    </div>

    <div class="flex-1 overflow-auto p-6">
      <div class="max-w-2xl mx-auto space-y-6">
        <!-- Profile Card -->
        <div class="bg-white rounded-xl border border-ivory-200 p-6 shadow-sm">
          <h2 class="text-base font-semibold text-navy-900 mb-5 flex items-center gap-2">
            <User class="w-5 h-5 text-navy-700" />
            个人信息
          </h2>
          <div class="space-y-4">
            <div class="flex items-center gap-4">
              <div class="w-14 h-14 rounded-xl bg-navy-800 flex items-center justify-center text-white text-xl font-semibold">
                {{ authStore.displayName?.charAt(0)?.toUpperCase() || 'U' }}
              </div>
              <div>
                <p class="text-lg font-semibold text-navy-900">{{ authStore.displayName }}</p>
                <p class="text-sm text-warm-gray">{{ user?.role === 'admin' ? '管理员' : '成员' }}</p>
              </div>
            </div>

            <div class="grid grid-cols-1 md:grid-cols-2 gap-4 pt-4 border-t border-ivory-100">
              <div class="flex items-center gap-3">
                <div class="w-10 h-10 rounded-lg bg-ivory-100 flex items-center justify-center">
                  <Mail class="w-5 h-5 text-warm-gray" />
                </div>
                <div>
                  <p class="text-xs text-warm-gray">邮箱</p>
                  <p class="text-sm font-medium text-navy-800">{{ user?.email || '-' }}</p>
                </div>
              </div>

              <div class="flex items-center gap-3">
                <div class="w-10 h-10 rounded-lg bg-ivory-100 flex items-center justify-center">
                  <Calendar class="w-5 h-5 text-warm-gray" />
                </div>
                <div>
                  <p class="text-xs text-warm-gray">注册时间</p>
                  <p class="text-sm font-medium text-navy-800">{{ formatDate(tenant?.created_at) }}</p>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Company Card -->
        <div class="bg-white rounded-xl border border-ivory-200 p-6 shadow-sm">
          <h2 class="text-base font-semibold text-navy-900 mb-5 flex items-center gap-2">
            <Building2 class="w-5 h-5 text-navy-700" />
            企业信息
          </h2>
          <div class="space-y-4">
            <div class="flex items-center gap-3">
              <div class="w-10 h-10 rounded-lg bg-ivory-100 flex items-center justify-center">
                <Building2 class="w-5 h-5 text-warm-gray" />
              </div>
              <div>
                <p class="text-xs text-warm-gray">企业名称</p>
                <p class="text-sm font-medium text-navy-800">{{ tenant?.name || '-' }}</p>
              </div>
            </div>
          </div>
        </div>

        <!-- Account Card -->
        <div class="bg-white rounded-xl border border-ivory-200 p-6 shadow-sm">
          <h2 class="text-base font-semibold text-navy-900 mb-5 flex items-center gap-2">
            <CreditCard class="w-5 h-5 text-navy-700" />
            账户套餐
          </h2>

          <!-- Current Plan -->
          <div class="p-4 rounded-xl border border-ivory-200 bg-ivory-50/50 mb-5">
            <div class="flex items-center justify-between">
              <div class="flex items-center gap-3">
                <div class="w-12 h-12 rounded-xl bg-navy-800 flex items-center justify-center">
                  <Crown class="w-6 h-6 text-white" />
                </div>
                <div>
                  <p class="text-sm font-medium text-navy-900">{{ currentPlan.label }}</p>
                  <p class="text-xs text-warm-gray">{{ currentPlan.description }}</p>
                </div>
              </div>
              <span :class="['px-3 py-1.5 rounded-lg text-xs font-semibold', currentPlan.color]">
                {{ currentPlan.label }}
              </span>
            </div>
          </div>

          <!-- Quota Info -->
          <div class="space-y-4">
            <div class="flex items-center gap-3">
              <div class="w-10 h-10 rounded-lg bg-ivory-100 flex items-center justify-center">
                <FileText class="w-5 h-5 text-warm-gray" />
              </div>
              <div class="flex-1">
                <div class="flex items-center justify-between mb-1">
                  <p class="text-xs text-warm-gray">合同审查额度</p>
                  <p class="text-xs font-medium text-navy-800">
                    已用 {{ user?.tenant?.contract_quota || 0 }} 次
                  </p>
                </div>
                <div class="h-2 bg-ivory-100 rounded-full overflow-hidden">
                  <div
                    class="h-full bg-navy-800 rounded-full transition-all"
                    :style="{ width: '30%' }"
                  ></div>
                </div>
              </div>
            </div>

            <!-- Plan Features -->
            <div class="pt-4 border-t border-ivory-100">
              <p class="text-xs text-warm-gray mb-3">套餐包含</p>
              <div class="flex flex-wrap gap-2">
                <span
                  v-if="tenant?.plan === 'free'"
                  class="px-3 py-1 bg-ivory-100 text-navy-700 rounded-lg text-xs"
                >
                  10 次审查额度
                </span>
                <span
                  v-else
                  class="px-3 py-1 bg-ivory-100 text-navy-700 rounded-lg text-xs"
                >
                  无限审查额度
                </span>
                <span class="px-3 py-1 bg-ivory-100 text-navy-700 rounded-lg text-xs">
                  PDF/Word 支持
                </span>
                <span class="px-3 py-1 bg-ivory-100 text-navy-700 rounded-lg text-xs">
                  一键导出报告
                </span>
                <span class="px-3 py-1 bg-ivory-100 text-navy-700 rounded-lg text-xs">
                  越用越懂你
                </span>
              </div>
            </div>
          </div>
        </div>

        <!-- Upgrade CTA (for free plan) -->
        <div
          v-if="tenant?.plan === 'free'"
          class="bg-gradient-to-r from-navy-800 to-navy-900 rounded-xl p-6 shadow-sm"
        >
          <div class="flex items-center justify-between">
            <div class="flex items-center gap-4">
              <div class="w-14 h-14 rounded-xl bg-white/10 flex items-center justify-center">
                <Zap class="w-7 h-7 text-white" />
              </div>
              <div>
                <h3 class="text-white font-semibold mb-1">升级到专业版</h3>
                <p class="text-navy-300 text-sm">解锁无限审查额度，更多高级功能</p>
              </div>
            </div>
            <button
              class="px-6 py-3 bg-amber-500 text-white rounded-xl text-sm font-semibold hover:bg-amber-600 transition-all hover:-translate-y-0.5 shadow-md"
            >
              立即升级
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
