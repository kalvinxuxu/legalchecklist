import axios from 'axios'
import { ElMessage } from 'element-plus'
import router from '@/router'

// 创建 Axios 实例
const request = axios.create({
  baseURL: '/api/v1',
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
