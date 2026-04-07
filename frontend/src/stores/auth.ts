import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export const useAuthStore = defineStore('auth', () => {
  const token = ref<string | null>(localStorage.getItem('token') || null)
  const user = ref<{ id: string; email: string; name?: string; company_name?: string } | null>(
    (() => { try { return JSON.parse(localStorage.getItem('user') || 'null') } catch { return null } })()
  )

  const isAuthenticated = computed(() => !!token.value)

  function login(newToken: string, newUser: typeof user.value) {
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

  return { token, user, isAuthenticated, login, logout }
})
