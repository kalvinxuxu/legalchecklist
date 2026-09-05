import axios from 'axios'
import { ElMessage } from 'element-plus'
import router from '@/router'

// 生产环境通过 Vercel 环境变量指向 Railway；本地开发继续走 Vite 代理。
const apiBaseUrl = (import.meta.env.VITE_API_BASE_URL || '').replace(/\/$/, '')

// 创建 Axios 实例
const request = axios.create({
  baseURL: `${apiBaseUrl}/api/v1`,
  timeout: 30000
})

// 请求拦截器
request.interceptors.request.use(
  config => {
    const token = localStorage.getItem('token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  error => {
    return Promise.reject(error)
  }
)

// 响应拦截器
request.interceptors.response.use(
  response => response.data,
  error => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token')
      router.push('/login')
    }

    const message = error.response?.data?.detail || '请求失败'
    ElMessage.error(message)

    return Promise.reject(error)
  }
)

export default request
