import { defineStore } from 'pinia'
import { authApi } from '@/api/auth'

export const useAuthStore = defineStore('auth', {
  state: () => ({
    token: localStorage.getItem('token') || null,
    user: JSON.parse(localStorage.getItem('user') || 'null')
  }),

  getters: {
    isAuthenticated: (state) => !!state.token,
    userEmail: (state) => state.user?.email,
    userName: (state) => state.user?.name
  },

  actions: {
    async login(email, password) {
      const response = await authApi.login(email, password)
      this.token = response.access_token
      this.user = response.user || { email }

      localStorage.setItem('token', response.access_token)
      localStorage.setItem('user', JSON.stringify(this.user))

      return response
    },

    async register(email, password, companyName) {
      const response = await authApi.register({
        email,
        password,
        company_name: companyName
      })

      // 注册成功后自动登录
      if (response.access_token) {
        this.token = response.access_token
        this.user = response.user || { email }

        localStorage.setItem('token', response.access_token)
        localStorage.setItem('user', JSON.stringify(this.user))
      }

      return response
    },

    logout() {
      this.token = null
      this.user = null
      localStorage.removeItem('token')
      localStorage.removeItem('user')
    },

    // 同步本地存储的状态（用于应用初始化时）
    syncFromStorage() {
      const token = localStorage.getItem('token')
      const userStr = localStorage.getItem('user')

      if (token) {
        this.token = token
        this.user = userStr ? JSON.parse(userStr) : null
      }
    }
  }
})
