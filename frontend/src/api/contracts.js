import request from './request'

export const contractsApi = {
  /**
   * 上传合同
   * @param {File} file - 合同文件
   * @param {string} workspaceId - 工作区 ID
   * @param {string} contractType - 合同类型
   */
  upload: (file, workspaceId, contractType) => {
    const formData = new FormData()
    formData.append('file', file)
    formData.append('workspace_id', workspaceId)
    formData.append('contract_type', contractType)

    return request.post('/contracts/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
  },

  /**
   * 获取合同列表
   */
  getList: () =>
    request.get('/contracts/'),

  /**
   * 获取合同详情
   * @param {string} id - 合同 ID
   */
  getDetail: (id) =>
    request.get(`/contracts/${id}`),

  /**
   * 获取审查结果
   * @param {string} id - 合同 ID
   */
  getReviewResult: (id) =>
    request.get(`/contracts/${id}/review`),

  /**
   * 获取合同理解分析结果
   * @param {string} id - 合同 ID
   */
  getUnderstanding: (id) =>
    request.get(`/contracts/${id}/understanding`),

  /**
   * 获取条款 PDF 定位信息
   * @param {string} id - 合同 ID
   */
  getClauseLocations: (id) =>
    request.get(`/contracts/${id}/clause-locations`),

  /**
   * 获取 PDF 文本位置信息
   * @param {string} id - 合同 ID
   */
  getPdfPositions: (id) =>
    request.get(`/contracts/${id}/pdf-positions`),

  /**
   * 删除合同
   * @param {string} id - 合同 ID
   */
  delete: (id) =>
    request.delete(`/contracts/${id}`),

  /**
   * 更新合同类型
   * @param {string} id - 合同 ID
   * @param {string} contractType - 合同类型
   */
  updateType: (id, contractType) =>
    request.patch(`/contracts/${id}/type`, null, { params: { contract_type: contractType } }),

  // ========== Word 辅助编辑 API ==========

  /**
   * 获取 Word 文档段落列表
   * @param {string} id - 合同 ID
   */
  getWordParagraphs: (id) =>
    request.get(`/contracts/${id}/word-paragraphs`),

  /**
   * 采纳建议并生成修订文档
   * @param {string} id - 合同 ID
   * @param {Array} suggestions - 采纳的建议列表
   */
  applyWordSuggestions: async (id, suggestions) => {
    const response = await request.post(`/contracts/${id}/apply-suggestions`, suggestions, {
      responseType: 'blob'
    })
    // response 是 Blob 对象，需要触发下载
    const blob = response
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    // 从 Content-Disposition 获取文件名
    link.download = `修订版_合同.docx`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(url)
    return { success: true }
  },

  /**
   * 下载修订后的 Word 文档
   * @param {string} id - 合同 ID
   */
  getRevisedWord: async (id) => {
    const response = await request.get(`/contracts/${id}/revised-word`, {
      responseType: 'blob'
    })
    const blob = response
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `修订版_合同.docx`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(url)
    return { success: true }
  }
}
