import { useQuery, useMutation, useQueryClient } from '@tanstack/vue-query'
import api from '@/lib/api'
import { useAuthStore } from '@/stores/auth'
import { useToast } from '@/composables/useToast'

// ========== Contract Types ==========
export interface Contract {
  id: string
  file_name: string
  file_path?: string
  contract_type: string
  review_status: 'pending' | 'processing' | 'completed' | 'failed'
  risk_level?: 'high' | 'medium' | 'low'
  review_error?: string
  content_text?: string
  created_at: string
}

export interface ReviewResult {
  status: string
  confidence_score?: number
  risk_clauses: Array<{
    title?: string
    original_text?: string
    risk_description?: string
    risk_level?: 'high' | 'medium' | 'low'
    suggestion?: string
  }>
  missing_clauses: Array<{
    title?: string
    description?: string
    suggestion?: string
  }>
  suggestions: Array<{ title?: string; content?: string }>
  legal_references?: string[]
}

export interface ContractUnderstanding {
  quick_cards?: {
    contract_purpose?: string
    key_dates?: string[]
    payment_summary?: string
    breach_summary?: string
    core_obligations?: string[]
  }
  structure?: {
    structure_summary?: string
    sections: Array<{ title: string; content: string }>
  }
  summary?: {
    key_clauses?: Array<{
      title?: string
      summary?: string
      risk_benefit?: 'risk' | 'benefit' | 'neutral'
    }>
    payment_terms?: { amount?: string; payment_method?: string }
    breach_liability?: { compensation_range?: string }
  }
}

export interface ClauseLocation {
  clause_title?: string
  clause_text?: string
  page: number
  bbox?: { x0: number; y0: number; x1: number; y1: number }
  risk_level?: 'high' | 'medium' | 'low'
}

// ========== Hooks ==========

export function useContracts() {
  return useQuery({
    queryKey: ['contracts'],
    queryFn: () => api.get('/contracts/') as Promise<Contract[]>,
    staleTime: 30_000,
  })
}

export function useContract(id: string) {
  return useQuery({
    queryKey: ['contracts', id],
    queryFn: () => api.get(`/contracts/${id}`) as Promise<Contract>,
    enabled: !!id,
  })
}

export function useReviewResult(id: string) {
  return useQuery({
    queryKey: ['contracts', id, 'review'],
    queryFn: async () => {
      // First check status via review-status endpoint
      const statusData = await api.get(`/contracts/${id}/review-status`) as {
        review_status: string
      }

      if (statusData.review_status !== 'completed') {
        throw new Error(`Review not ready: ${statusData.review_status}`)
      }

      return api.get(`/contracts/${id}/review`) as Promise<ReviewResult>
    },
    enabled: !!id,
    refetchInterval: (query) => {
      if (query.state.error) {
        const err = query.state.error as { message?: string }
        // If error indicates review is still processing, keep polling
        if (err.message?.includes('Review not ready')) return 3000
      }
      return false
    },
    retry: (failureCount, error) => {
      // Don't retry if review is still processing (400 error)
      const err = error as { response?: { status?: number } }
      if (err.response?.status === 400) return false
      return failureCount < 3
    },
  })
}

export function useContractUnderstanding(id: string) {
  return useQuery({
    queryKey: ['contracts', id, 'understanding'],
    queryFn: () => api.get(`/contracts/${id}/understanding`) as Promise<ContractUnderstanding>,
    enabled: !!id,
    retry: false,
  })
}

export function useClauseLocations(id: string) {
  return useQuery({
    queryKey: ['contracts', id, 'clause-locations'],
    queryFn: () => api.get(`/contracts/${id}/clause-locations`) as Promise<ClauseLocation[]>,
    enabled: !!id,
  })
}

// ========== Mutations ==========

export function useUploadContract() {
  const queryClient = useQueryClient()
  const { toast } = useToast()

  return useMutation({
    mutationFn: ({ file, workspaceId, contractType }: { file: File; workspaceId: string; contractType: string }) => {
      const formData = new FormData()
      formData.append('file', file)
      formData.append('workspace_id', workspaceId)
      formData.append('contract_type', contractType)
      return api.post('/contracts/upload', formData, { headers: { 'Content-Type': 'multipart/form-data' } }) as Promise<{ id: string }>
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['contracts'] })
    },
    onError: (error: { response?: { data?: { detail?: string } } }) => {
      toast({ title: '上传失败', description: error.response?.data?.detail, variant: 'destructive' })
    },
  })
}

export function useDeleteContract() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (id: string) => api.delete(`/contracts/${id}`) as Promise<void>,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['contracts'] })
    },
  })
}

export function useUpdateContractType() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ id, contractType }: { id: string; contractType: string }) =>
      api.patch(`/contracts/${id}/type`, null, { params: { contract_type: contractType } }) as Promise<void>,
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: ['contracts', id] })
    },
  })
}
