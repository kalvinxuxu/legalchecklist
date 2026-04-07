<script setup lang="ts">
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useContracts } from '@/composables/useContracts'
import { Upload, FileText, AlertTriangle, Clock, ArrowRight, TrendingUp, ShieldCheck, Sparkles } from 'lucide-vue-next'
import { formatDateShort, CONTRACT_TYPE_MAP, REVIEW_STATUS_MAP } from '@/lib/utils'

const router = useRouter()
const { data: contracts = ref([]), isLoading } = useContracts()

const contractsList = computed(() => contracts.value || [])

const stats = computed(() => ({
  contractCount: contractsList.value.length,
  highRiskCount: contractsList.value.filter((c) => c.risk_level === 'high').length,
  pendingCount: contractsList.value.filter((c) => c.review_status === 'pending' || c.review_status === 'processing').length,
}))

const recentContracts = computed(() => contractsList.value.slice(0, 5))

function getTypeVariant(type: string) {
  const variants: Record<string, string> = {
    NDA: 'warning',
    Service: 'primary',
    Labor: 'danger',
    Sales: 'success',
  }
  return (variants[type] || 'secondary') as 'primary' | 'success' | 'warning' | 'danger' | 'info' | 'secondary' | 'outline' | 'ghost' | 'default'
}

function getStatusVariant(status: string) {
  const variants: Record<string, string> = {
    completed: 'success',
    pending: 'warning',
    processing: 'primary',
    failed: 'danger',
  }
  return (variants[status] || 'secondary') as 'primary' | 'success' | 'warning' | 'danger' | 'info' | 'secondary' | 'outline' | 'ghost' | 'default'
}

function formatDate(dateStr: string) {
  if (!dateStr) return '-'
  const date = new Date(dateStr)
  return date.toLocaleDateString('zh-CN', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })
}
</script>

<template>
  <div class="flex flex-col h-full bg-ivory-50">
    <!-- Header -->
    <div class="px-6 py-5 bg-white border-b border-ivory-200">
      <div class="flex items-center justify-between">
        <div>
          <h1 class="text-xl font-bold text-navy-900" style="font-family: 'Noto Serif SC', Georgia, serif;">
            工作台
          </h1>
          <p class="text-sm text-warm-gray mt-0.5">欢迎回来，查看您的合同审查概览</p>
        </div>
        <button
          @click="router.push('/workspace/upload')"
          class="inline-flex items-center gap-2 px-4 py-2 bg-navy-800 text-white rounded-xl text-sm font-semibold hover:bg-navy-900 transition-all hover:-translate-y-0.5 shadow-sm hover:shadow-md"
        >
          <Upload class="w-4 h-4" />
          上传合同
        </button>
      </div>
    </div>

    <div class="flex-1 overflow-auto p-6">
      <!-- Stats cards -->
      <div class="grid grid-cols-1 md:grid-cols-3 gap-5 mb-6">
        <!-- Total contracts -->
        <div class="bg-white rounded-xl border border-ivory-200 p-5 shadow-sm card-hover animate-fade-up">
          <div class="flex items-start justify-between">
            <div>
              <p class="text-sm text-warm-gray mb-1">已审查合同</p>
              <p class="text-3xl font-bold text-navy-900" style="font-family: 'Noto Serif SC', serif;">
                {{ stats.contractCount }}
              </p>
            </div>
            <div class="w-11 h-11 rounded-xl bg-navy-50 border border-navy-100 flex items-center justify-center">
              <FileText class="w-5 h-5 text-navy-700" />
            </div>
          </div>
          <div class="mt-3 flex items-center gap-1.5 text-xs text-warm-gray">
            <TrendingUp class="w-3.5 h-3.5 text-success-500" />
            <span>较上月增长 12%</span>
          </div>
        </div>

        <!-- High risk -->
        <div class="bg-white rounded-xl border border-ivory-200 p-5 shadow-sm card-hover animate-fade-up stagger-1">
          <div class="flex items-start justify-between">
            <div>
              <p class="text-sm text-warm-gray mb-1">高风险条款</p>
              <p class="text-3xl font-bold text-navy-900" style="font-family: 'Noto Serif SC', serif;">
                {{ stats.highRiskCount }}
              </p>
            </div>
            <div class="w-11 h-11 rounded-xl bg-danger-50 border border-danger-100 flex items-center justify-center">
              <AlertTriangle class="w-5 h-5 text-danger-500" />
            </div>
          </div>
          <div class="mt-3 flex items-center gap-1.5 text-xs text-warm-gray">
            <ShieldCheck class="w-3.5 h-3.5 text-danger-500" />
            <span>需重点关注</span>
          </div>
        </div>

        <!-- Pending -->
        <div class="bg-white rounded-xl border border-ivory-200 p-5 shadow-sm card-hover animate-fade-up stagger-2">
          <div class="flex items-start justify-between">
            <div>
              <p class="text-sm text-warm-gray mb-1">审查中</p>
              <p class="text-3xl font-bold text-navy-900" style="font-family: 'Noto Serif SC', serif;">
                {{ stats.pendingCount }}
              </p>
            </div>
            <div class="w-11 h-11 rounded-xl bg-amber-50 border border-amber-100 flex items-center justify-center">
              <Clock class="w-5 h-5 text-amber-600" />
            </div>
          </div>
          <div class="mt-3 flex items-center gap-1.5 text-xs text-warm-gray">
            <Sparkles class="w-3.5 h-3.5 text-amber-500" />
            <span>AI 正在处理中</span>
          </div>
        </div>
      </div>

      <!-- Quick action banner -->
      <div class="bg-gradient-to-r from-navy-800 to-navy-900 rounded-xl p-5 mb-6 relative overflow-hidden animate-fade-up stagger-3">
        <div class="absolute top-0 right-0 w-64 h-64 bg-amber-500/10 rounded-full blur-3xl"></div>
        <div class="relative z-10 flex items-center justify-between">
          <div class="flex items-center gap-4">
            <div class="w-12 h-12 rounded-xl bg-white/10 backdrop-blur border border-white/10 flex items-center justify-center">
              <Upload class="w-6 h-6 text-white" />
            </div>
            <div>
              <h3 class="text-white font-semibold mb-0.5">上传新合同</h3>
              <p class="text-navy-300 text-sm">支持 PDF、Word 格式，30 秒完成审查</p>
            </div>
          </div>
          <button
            @click="router.push('/workspace/upload')"
            class="px-5 py-2.5 bg-amber-500 text-white rounded-xl text-sm font-semibold hover:bg-amber-600 transition-all hover:-translate-y-0.5 shadow-md flex items-center gap-2"
          >
            开始上传
            <ArrowRight class="w-4 h-4" />
          </button>
        </div>
      </div>

      <!-- Recent contracts -->
      <div class="bg-white rounded-xl border border-ivory-200 shadow-sm overflow-hidden animate-fade-up stagger-4">
        <div class="px-5 py-4 border-b border-ivory-100 flex items-center justify-between">
          <div>
            <h2 class="text-base font-semibold text-navy-900">最近审查</h2>
            <p class="text-xs text-warm-gray mt-0.5">您最近的合同审查记录</p>
          </div>
          <button
            @click="router.push('/workspace/contracts')"
            class="text-sm font-medium text-navy-700 hover:text-navy-900 transition-colors flex items-center gap-1"
          >
            查看全部
            <ArrowRight class="w-3.5 h-3.5" />
          </button>
        </div>

        <!-- Loading -->
        <div v-if="isLoading" class="p-5 space-y-3">
          <div v-for="i in 3" :key="i" class="h-16 skeleton rounded-xl"></div>
        </div>

        <!-- Empty -->
        <div v-else-if="recentContracts.length === 0" class="p-12 text-center">
          <div class="w-16 h-16 rounded-2xl bg-ivory-100 flex items-center justify-center mx-auto mb-4">
            <FileText class="w-8 h-8 text-warm-gray" />
          </div>
          <h3 class="text-base font-medium text-navy-800 mb-1">暂无审查记录</h3>
          <p class="text-sm text-warm-gray mb-5">上传您的第一份合同，开始智能审查</p>
          <button
            @click="router.push('/workspace/upload')"
            class="inline-flex items-center gap-2 px-5 py-2.5 bg-navy-800 text-white rounded-xl text-sm font-semibold hover:bg-navy-900 transition-all"
          >
            <Upload class="w-4 h-4" />
            上传合同
          </button>
        </div>

        <!-- List -->
        <div v-else class="divide-y divide-ivory-100">
          <div
            v-for="contract in recentContracts"
            :key="contract.id"
            class="px-5 py-4 hover:bg-ivory-50/80 transition-colors cursor-pointer"
            @click="router.push(`/workspace/review/${contract.id}`)"
          >
            <div class="flex items-center justify-between gap-4">
              <div class="flex-1 min-w-0">
                <div class="flex items-center gap-2 mb-1.5">
                  <span class="text-sm font-medium text-navy-900 truncate">{{ contract.file_name }}</span>
                  <span
                    class="px-2 py-0.5 rounded-md text-xs font-medium"
                    :class="{
                      'bg-success-50 text-success-600': contract.review_status === 'completed',
                      'bg-amber-50 text-amber-600': contract.review_status === 'pending',
                      'bg-navy-50 text-navy-700': contract.review_status === 'processing',
                      'bg-danger-50 text-danger-600': contract.review_status === 'failed',
                    }"
                  >
                    {{ REVIEW_STATUS_MAP[contract.review_status]?.label || contract.review_status }}
                  </span>
                </div>
                <div class="flex items-center gap-3 text-xs text-warm-gray">
                  <span class="px-2 py-0.5 bg-ivory-100 rounded text-navy-700 font-medium">
                    {{ CONTRACT_TYPE_MAP[contract.contract_type]?.label || contract.contract_type || '通用合同' }}
                  </span>
                  <span>{{ formatDate(contract.created_at) }}</span>
                </div>
              </div>
              <div class="flex items-center gap-2 flex-shrink-0">
                <button
                  v-if="contract.review_status === 'completed'"
                  @click.stop="router.push(`/workspace/review/${contract.id}`)"
                  class="px-3 py-1.5 bg-navy-800 text-white rounded-lg text-xs font-medium hover:bg-navy-900 transition-colors"
                >
                  查看报告
                </button>
                <button
                  v-else
                  @click.stop="router.push(`/workspace/review/${contract.id}`)"
                  class="px-3 py-1.5 border border-ivory-300 text-navy-700 rounded-lg text-xs font-medium hover:bg-ivory-50 transition-colors"
                >
                  查看进度
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
