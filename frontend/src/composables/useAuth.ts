import { useMutation } from '@tanstack/vue-query'
import { useRouter } from 'vue-router'
import api from '@/lib/api'
import { useAuthStore } from '@/stores/auth'
import { useToast } from '@/composables/useToast'

export function useLogin() {
  const router = useRouter()
  const { login } = useAuthStore()
  const { toast } = useToast()

  return useMutation({
    mutationFn: (data: { email: string; password: string }) =>
      api.post('/auth/login', data) as Promise<{ access_token: string; user: { id: string; email: string } }>,
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
    mutationFn: (data: { email: string; password: string; company_name: string }) =>
      api.post('/auth/register', data) as Promise<{ access_token: string; user: { id: string; email: string } }>,
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
