/**
 * 审查报告导出功能
 */
import api from '@/lib/api'
import { useToast } from '@/composables/useToast'

const { toast } = useToast()

export type ExportType = 'review_report' | 'original_with_comments'

export interface ExportOptions {
  export_type?: ExportType
  include_risk_clauses: boolean
  include_missing_clauses: boolean
  include_suggestions: boolean
  include_rule_judgments: boolean
  include_policy_references: boolean
  comment_format?: 'standard' | 'compact'
}

export function useExportReport() {
  /**
   * 导出审查报告为 Word 文档
   */
  async function exportReviewReport(
    contractId: string,
    options: ExportOptions,
    filename?: string
  ) {
    try {
      const response = await api.post(
        `/contracts/${contractId}/export-review-report`,
        options,
        { responseType: 'blob' }
      )

      // 创建下载链接
      const url = window.URL.createObjectURL(new Blob([response], {
        type: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
      }))
      const link = document.createElement('a')
      link.href = url

      // 使用传入的文件名或根据导出类型生成
      link.download = filename || `审查报告_${contractId.slice(0, 8)}.docx`

      document.body.appendChild(link)
      link.click()
      link.remove()
      window.URL.revokeObjectURL(url)

      const exportType = options.export_type === 'original_with_comments' ? '批注版文档' : '审查报告'
      toast({
        title: '导出成功',
        description: `${exportType}已下载`
      })
    } catch (error) {
      console.error('Failed to export review report:', error)
      toast({
        title: '导出失败',
        description: '无法生成审查报告，请稍后重试',
        variant: 'destructive'
      })
      throw error
    }
  }

  return {
    exportReviewReport
  }
}
