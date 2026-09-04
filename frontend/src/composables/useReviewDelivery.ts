import api from '@/lib/api'
import { useToast } from '@/composables/useToast'

const { toast } = useToast()

function downloadBlob(payload: unknown, filename: string, type: string) {
  const url = URL.createObjectURL(new Blob([payload as BlobPart], { type }))
  const link = document.createElement('a')
  link.href = url
  link.download = filename
  link.click()
  URL.revokeObjectURL(url)
}

export function useReviewDelivery() {
  async function exportOpinion(contractId: string, contractName: string) {
    const payload = await api.post(`/contracts/${contractId}/export-opinion`, { format: 'html' }, { responseType: 'blob' })
    downloadBlob(payload, `审查意见_${contractName.replace(/\.[^.]+$/, '')}.html`, 'text/html;charset=utf-8')
    toast({ title: '导出成功', description: '审查意见已下载' })
  }

  async function exportOpinionDocx(contractId: string, contractName: string) {
    const payload = await api.post(`/contracts/${contractId}/export-opinion-docx`, {}, { responseType: 'blob' })
    downloadBlob(payload, `审查意见_${contractName.replace(/\.[^.]+$/, '')}.docx`, 'application/vnd.openxmlformats-officedocument.wordprocessingml.document')
    toast({ title: '导出成功', description: 'Word 审查意见已下载' })
  }

  async function saveEmailDraft(contractId: string, draft: { from_email?: string; to: string[]; subject: string; body_text: string; idempotency_key: string }) {
    const result = await api.post(`/contracts/${contractId}/email-drafts`, draft)
    toast({
      title: result.sync_status === 'sync_failed' ? '草稿已保存，但邮箱同步失败' : '草稿已保存',
      description: result.sync_status === 'synced' ? '已同步到邮箱草稿箱' : (result.last_error || '已保存，等待邮箱同步'),
      variant: result.sync_status === 'sync_failed' ? 'destructive' : undefined,
    })
    return result
  }

  async function previewEmailDraft(contractId: string) {
    return await api.post(`/contracts/${contractId}/email-draft-preview`, {}) as {
      from: string; subject: string; body_text: string; attachments: Array<{ filename: string; content_type: string }>
    }
  }

  return { exportOpinion, exportOpinionDocx, saveEmailDraft, previewEmailDraft }
}
