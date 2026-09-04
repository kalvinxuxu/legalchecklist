import { useQuery, useMutation, useQueryClient } from '@tanstack/vue-query'
import api from '@/lib/api'
import type { IngestionStatus } from '@/types/document'

export function useDocumentIngestion(id: string) {
  return useQuery({
    queryKey: ['documents', id, 'ingestion'],
    queryFn: () => api.get(`/documents/${id}/ingestion`) as Promise<IngestionStatus>,
    enabled: !!id,
    refetchInterval: (query) => query.state.data?.status === 'completed' || query.state.data?.status === 'failed' ? false : 3000,
  })
}

export function useStartDocumentIngestion() {
  const client = useQueryClient()
  return useMutation({
    mutationFn: (id: string) => api.post(`/documents/${id}/ingest`) as Promise<IngestionStatus>,
    onSuccess: (_data, id) => client.invalidateQueries({ queryKey: ['documents', id, 'ingestion'] }),
  })
}
