import { ref } from 'vue'
import api from '@/lib/api'

// API 路径（api.ts 中 baseURL 已设置为 /api/v1）
const API_BASE = '/knowledge'

interface KnowledgeItem {
  id: string
  title: string
  content: string
  content_type: string
  tenant_id: string | null
  is_public: boolean
  metadata: Record<string, any>
  created_at: string
  updated_at: string
}

interface KnowledgeListResponse {
  total: number
  items: KnowledgeItem[]
}

interface ContentType {
  value: string
  label: string
  description: string
}

export function useKnowledge() {
  const isLoading = ref(false)
  const error = ref<Error | null>(null)

  const knowledgeList = ref<KnowledgeItem[]>([])
  const total = ref(0)

  // 获取知识列表
  async function fetchKnowledge(params?: {
    content_type?: string
    search?: string
    limit?: number
    offset?: number
  }) {
    isLoading.value = true
    error.value = null
    try {
      const data = await api.get<KnowledgeListResponse>(API_BASE, { params })
      knowledgeList.value = data?.items || []
      total.value = data?.total || 0
      return data
    } catch (e) {
      error.value = e as Error
      knowledgeList.value = []
      total.value = 0
      throw e
    } finally {
      isLoading.value = false
    }
  }

  // 获取知识详情
  async function getKnowledge(id: string) {
    return await api.get<KnowledgeItem>(`${API_BASE}/${id}`)
  }

  // 创建知识
  async function createKnowledge(data: {
    title: string
    content: string
    content_type: string
    metadata?: Record<string, any>
  }) {
    const formData = new FormData()
    formData.append('title', data.title)
    formData.append('content', data.content)
    formData.append('content_type', data.content_type)
    if (data.metadata) {
      formData.append('metadata', JSON.stringify(data.metadata))
    }
    return await api.post(API_BASE, formData)
  }

  // 上传知识文档
  async function uploadKnowledge(file: File, contentType: string, title?: string) {
    const formData = new FormData()
    formData.append('file', file)
    formData.append('content_type', contentType)
    if (title) {
      formData.append('title', title)
    }
    return await api.post(`${API_BASE}/upload`, formData)
  }

  // 更新知识
  async function updateKnowledge(id: string, data: {
    title: string
    content: string
    content_type: string
    metadata?: Record<string, any>
  }) {
    const formData = new FormData()
    formData.append('title', data.title)
    formData.append('content', data.content)
    formData.append('content_type', data.content_type)
    if (data.metadata) {
      formData.append('metadata', JSON.stringify(data.metadata))
    }
    return await api.put(`${API_BASE}/${id}`, formData)
  }

  // 删除知识
  async function deleteKnowledge(id: string) {
    return await api.delete(`${API_BASE}/${id}`)
  }

  // 获取内容类型
  async function getContentTypes() {
    const data = await api.get<{ types: ContentType[] }>(`${API_BASE}/types`)
    return data.types
  }

  return {
    knowledgeList,
    total,
    isLoading,
    fetchKnowledge,
    getKnowledge,
    createKnowledge,
    uploadKnowledge,
    updateKnowledge,
    deleteKnowledge,
    getContentTypes,
  }
}
