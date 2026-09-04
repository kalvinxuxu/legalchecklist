import { useMutation } from '@tanstack/vue-query'
import { useRouter } from 'vue-router'
import api from '@/lib/api'
import { useAuthStore } from '@/stores/auth'
import { useToast } from '@/composables/useToast'

interface AuthUser {
  id: string
  email: string
  name?: string
  role: string
  tenant_id: string
  tenant?: {
    id: string
    name: string
    plan: string
    contract_quota: number
    created_at: string
  }
}

interface AuthResponse {
  access_token: string
  token_type: string
  user: AuthUser
}

export function useLogin() {
  const router = useRouter()
  const { login } = useAuthStore()
  const { toast } = useToast()

  return useMutation({
    mutationFn: (data: { email: string; password: string }) =>
      api.post('/auth/login', data) as Promise<AuthResponse>,
    onSuccess: (data) => {
      login(data.access_token, data.user)
      toast({ title: '登录成功', variant: 'success' })
      router.push('/workspace')
    },
    onError: (error: { response?: { data?: { detail?: string } } }) => {
      toast({ title: '登录失败', description: error.response?.data?.detail || '请检查邮箱和密码', variant: 'destructive' })
    },
  })
}

export function useRegister() {
  const router = useRouter()
  const { login } = useAuthStore()
  const { toast } = useToast()

  return useMutation({
    mutationFn: (data: { email: string; password: string; name?: string; company_name?: string }) =>
      api.post('/auth/register', data) as Promise<AuthResponse>,
    onSuccess: (data) => {
      if (data.access_token) {
        login(data.access_token, data.user)
        router.push('/workspace')
      }
    },
    onError: (error: { response?: { data?: { detail?: string } } }) => {
      toast({ title: '注册失败', description: error.response?.data?.detail, variant: 'destructive' })
    },
  })
}
