import { useQuery, useMutation, useQueryClient } from '@tanstack/vue-query'
import { computed, isRef, type Ref } from 'vue'
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
    legal_reference?: string
    policy_reference?: string
    evidence_id?: string
    evidence_locations?: Array<{ page: number; bbox?: { x0: number; y0: number; x1: number; y1: number } }>
    evidence_resolution_status?: 'resolved' | 'fuzzy_fallback' | 'page_only' | 'unresolved'
  }>
  missing_clauses: Array<{
    title?: string
    description?: string
    suggestion?: string
    legal_reference?: string
    policy_reference?: string
  }>
  suggestions: Array<{ title?: string; content?: string }>
  legal_references?: string[]
  policy_references?: Array<{
    policy_name?: string
    section?: string
    content?: string
  }>
  retrieval_diagnostics?: {
    modes?: string[]
    candidate_count?: number
    contract_chunks?: number
    contract_top_candidates?: Array<{ chunk_id?: string; document_version_id?: string; page_start?: number; page_end?: number; bm25_rank?: number; vector_rank?: number; fused_score?: number; rerank_score?: number; retrieval_mode?: string; reranker_provider?: string; fallback_reason?: string }>
    top_candidates?: Array<{ id?: string; bm25_rank?: number; vector_rank?: number; fused_score?: number; rerank_score?: number }>
  }
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

export interface ReviewStepStatus {
  stage: string
  stage_label?: string
  status: 'waiting' | 'running' | 'completed' | 'failed' | 'skipped'
  attempt: number
  started_at?: string | null
  completed_at?: string | null
  error?: string | null
}

export interface ReviewStatus {
  run_id?: string
  status: 'queued' | 'running' | 'completed' | 'failed' | 'stalled' | string
  review_status: 'pending' | 'processing' | 'completed' | 'failed'
  current_stage?: string | null
  stage_label?: string | null
  progress: number
  attempt: number
  last_heartbeat_at?: string | null
  elapsed_seconds: number
  last_error?: string | null
  resumable_from?: string | null
  steps: ReviewStepStatus[]
}

export interface ClauseLocation {
  clause_title?: string
  clause_text?: string
  page: number
  bbox?: { x0: number; y0: number; x1: number; y1: number }
  risk_level?: 'high' | 'medium' | 'low'
  evidence_id?: string
  document_id?: string
  version_id?: string
  coord_system?: 'pdf_top_left'
  locations?: Array<{ page: number; bbox?: { x0: number; y0: number; x1: number; y1: number }; span_id?: string }>
  match_type?: 'id_exact' | 'offset_exact' | 'fuzzy_legacy' | 'page_only'
  resolution_status?: 'resolved' | 'fuzzy_fallback' | 'page_only' | 'unresolved'
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

export function useReviewStatus(id: string) {
  return useQuery({
    queryKey: ['contracts', id, 'review-status'],
    queryFn: () => api.get(`/contracts/${id}/review-status`) as Promise<ReviewStatus>,
    enabled: !!id,
    refetchInterval: (query) => {
      const status = query.state.data?.status
      return status === 'completed' || status === 'failed' || status === 'stalled' ? 5000 : 2000
    },
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

export function useClauseLocations(id: string, enabled: boolean | Ref<boolean> = true) {
  return useQuery({
    queryKey: ['contracts', id, 'clause-locations'],
    queryFn: () => api.get(`/contracts/${id}/clause-locations`) as Promise<ClauseLocation[]>,
    // 由调用方控制是否启用查询
    enabled: computed(() => !!id && (isRef(enabled) ? enabled.value : enabled)),
  })
}

// ========== Mutations ==========

export function useUploadContract() {
  const queryClient = useQueryClient()
  const { toast } = useToast()

  return useMutation({
    mutationFn: ({ file, workspaceId, contractType, partyPosition, contractAmount, riskPreference }: {
      file: File
      workspaceId: string
      contractType: string
      partyPosition?: string | null
      contractAmount?: number | null
      riskPreference?: string | null
    }) => {
      const formData = new FormData()
      formData.append('file', file)
      formData.append('workspace_id', workspaceId)
      formData.append('contract_type', contractType)
      // 传递审查立场配置
      if (partyPosition) formData.append('party_position', partyPosition)
      if (contractAmount) formData.append('contract_amount', contractAmount.toString())
      if (riskPreference) formData.append('risk_preference', riskPreference)
      // 不自动触发审查，用户手动在详情页点击"开始审查"
      // 后端字段名为 auto_review_str；关闭同步审查，避免上传阶段触发解析/模型调用
      formData.append('auto_review_str', 'false')
      // 让浏览器/Axios 自动生成 multipart boundary，手动设置会导致文件 POST 被浏览器拦截。
      return api.post('/contracts/upload', formData) as Promise<{ id: string }>
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
