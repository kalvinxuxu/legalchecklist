import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { h, defineComponent } from 'vue'
import { VueQueryPlugin, QueryClient, useQuery } from '@tanstack/vue-query'
import { useContract, useReviewResult, useContracts } from '../useContracts'

// Mock api
vi.mock('@/lib/api', () => ({
  default: {
    get: vi.fn(),
    post: vi.fn(),
    delete: vi.fn(),
    patch: vi.fn(),
  },
}))

import api from '@/lib/api'

const mockApi = api as any

// Create a fresh QueryClient for each test
const createQueryClient = () => new QueryClient({
  defaultOptions: {
    queries: { retry: false },
  },
})

// Helper to mount component with Vue Query
const mountWithQuery = (component: any, options: any = {}) => {
  const queryClient = createQueryClient()
  return mount(component, {
    ...options,
    global: {
      plugins: [[VueQueryPlugin, { queryClient }]],
      ...options.global,
    },
  })
}

// Test wrapper component that uses a composable
const createTestWrapper = (composableFn: () => any) => {
  return defineComponent({
    setup() {
      const result = composableFn()
      return () => h('div', { 'data-testid': 'test' }, JSON.stringify(result.data?.value))
    },
  })
}

describe('useContracts composables', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    // Reset vue-query cache
    const queryClient = createQueryClient()
    queryClient.clear()
  })

  describe('useContracts', () => {
    it('should call api.get with correct endpoint', async () => {
      const mockContracts = [
        { id: '1', file_name: 'test.pdf', contract_type: 'NDA', review_status: 'completed' },
      ]
      mockApi.get.mockResolvedValue(mockContracts)

      const wrapper = mountWithQuery(createTestWrapper(useContracts))
      await new Promise(resolve => setTimeout(resolve, 50))

      expect(mockApi.get).toHaveBeenCalledWith('/contracts/')
    })
  })

  describe('useContract', () => {
    it('should call api.get with correct endpoint for specific id', async () => {
      const mockContract = {
        id: 'contract-123',
        file_name: 'test.pdf',
        contract_type: 'NDA',
        review_status: 'completed',
        content_text: 'Test content',
      }
      mockApi.get.mockResolvedValue(mockContract)

      const wrapper = mountWithQuery(createTestWrapper(() => useContract('contract-123')))
      await new Promise(resolve => setTimeout(resolve, 50))

      expect(mockApi.get).toHaveBeenCalledWith('/contracts/contract-123')
    })

    it('should not call api when id is empty string', () => {
      mockApi.get.mockResolvedValue(undefined)

      mountWithQuery(createTestWrapper(() => useContract('')))

      // Empty string is falsy, so the query should not execute (enabled: !!id)
      // The useContract checks enabled: !!id which is false for empty string
      // But since we mount synchronously, let's verify get was not called with empty id
      expect(mockApi.get).not.toHaveBeenCalledWith(expect.stringContaining('/contracts/'))
    })
  })

  describe('useReviewResult', () => {
    it('should call api.get with correct review endpoint', async () => {
      const mockReview = {
        status: 'completed',
        confidence_score: 0.95,
        risk_clauses: [
          { title: '保密条款', risk_level: 'high', risk_description: '过于严格' },
        ],
        missing_clauses: [],
        suggestions: [],
      }
      mockApi.get.mockResolvedValue(mockReview)

      const wrapper = mountWithQuery(createTestWrapper(() => useReviewResult('contract-123')))
      await new Promise(resolve => setTimeout(resolve, 50))

      expect(mockApi.get).toHaveBeenCalledWith('/contracts/contract-123/review')
    })
  })
})
