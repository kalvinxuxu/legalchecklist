<script setup lang="ts">
import { computed } from 'vue'
import { useRouter, useRoute, RouterView, RouterLink } from 'vue-router'
import { LayoutDashboard, FileText, Upload, LogOut, Settings, ChevronRight, BookOpen } from 'lucide-vue-next'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()

const navItems = [
  { key: 'dashboard', label: '工作台', icon: LayoutDashboard, to: '/workspace' },
  { key: 'contracts', label: '合同列表', icon: FileText, to: '/workspace/contracts' },
  { key: 'upload', label: '上传合同', icon: Upload, to: '/workspace/upload' },
  { key: 'policies', label: '公司政策库', icon: BookOpen, to: '/workspace/policies' },
]

function isActive(to: string) {
  if (to === '/workspace') return route.path === '/workspace' || route.path === '/workspace/'
  return route.path.startsWith(to)
}

function handleLogout() {
  authStore.logout()
  router.push('/login')
}
</script>

<template>
  <div class="flex h-screen bg-ivory-50 overflow-hidden">
    <!-- Sidebar -->
    <aside class="w-60 flex-shrink-0 bg-white border-r border-ivory-200 flex flex-col h-full">
      <!-- Logo -->
      <div class="h-16 flex items-center px-5 border-b border-ivory-200">
        <div class="flex items-center gap-2.5">
          <div class="w-8 h-8 rounded-lg bg-navy-800 flex items-center justify-center flex-shrink-0">
            <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
              <path d="M3 2L8 6.5L3 11" stroke="white" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
              <path d="M10 2L15 6.5L10 11" stroke="white" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" opacity="0.5"/>
            </svg>
          </div>
          <span class="text-base font-semibold text-navy-800 tracking-tight">法务 AI</span>
        </div>
      </div>

      <!-- User info -->
      <div class="px-4 py-4 border-b border-ivory-200">
        <div class="flex items-center gap-3 p-3 bg-ivory-50 rounded-xl">
          <div class="w-9 h-9 rounded-lg bg-navy-800 flex items-center justify-center text-white text-sm font-semibold flex-shrink-0">
            {{ authStore.user?.email?.charAt(0)?.toUpperCase() || 'U' }}
          </div>
          <div class="flex-1 min-w-0">
            <p class="text-sm font-medium text-navy-800 truncate">{{ authStore.user?.company_name || '用户' }}</p>
            <p class="text-xs text-warm-gray truncate">{{ authStore.user?.email }}</p>
          </div>
        </div>
      </div>

      <!-- Nav -->
      <nav class="flex-1 py-3 px-3 space-y-0.5 overflow-y-auto">
        <RouterLink
          v-for="item in navItems"
          :key="item.key"
          :to="item.to"
          class="flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-all group"
          :class="isActive(item.to)
            ? 'bg-navy-800 text-white shadow-sm'
            : 'text-warm-gray hover:text-navy-800 hover:bg-ivory-100'"
        >
          <component
            :is="item.icon"
            class="w-4.5 h-4.5 flex-shrink-0"
            :class="isActive(item.to) ? 'text-white/90' : 'text-warm-gray group-hover:text-navy-800'"
          />
          {{ item.label }}
          <ChevronRight
            v-if="isActive(item.to)"
            class="w-3.5 h-3.5 ml-auto text-white/50"
          />
        </RouterLink>
      </nav>

      <!-- Bottom -->
      <div class="p-3 border-t border-ivory-200 space-y-0.5">
        <button
          @click="handleLogout"
          class="flex items-center gap-3 w-full px-3 py-2.5 rounded-xl text-sm font-medium text-warm-gray hover:text-danger-500 hover:bg-danger-50 transition-all"
        >
          <LogOut class="w-4.5 h-4.5 flex-shrink-0" />
          退出登录
        </button>
      </div>
    </aside>

    <!-- Main -->
    <main class="flex-1 flex flex-col overflow-hidden">
      <RouterView />
    </main>
  </div>
</template>
