import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export interface Tenant {
  id: string
  name: string
  plan: string
  contract_quota: number
  created_at: string
}

export interface AuthUser {
  id: string
  email: string
  name?: string
  role: string
  tenant_id: string
  tenant?: Tenant
}

export const useAuthStore = defineStore('auth', () => {
  const token = ref<string | null>(localStorage.getItem('token') || null)
  const user = ref<AuthUser | null>(
    (() => { try { return JSON.parse(localStorage.getItem('user') || 'null') } catch { return null } })()
  )

  const isAuthenticated = computed(() => !!token.value)

  // 获取用户显示名称：优先 name，其次 tenant.name，最后 "用户"
  const displayName = computed(() => user.value?.name || user.value?.tenant?.name || '用户')

  function login(newToken: string, newUser: AuthUser) {
    token.value = newToken
    user.value = newUser
    localStorage.setItem('token', newToken)
    localStorage.setItem('user', JSON.stringify(newUser))
  }

  function logout() {
    token.value = null
    user.value = null
    localStorage.removeItem('token')
    localStorage.removeItem('user')
  }

  return { token, user, isAuthenticated, displayName, login, logout }
})
