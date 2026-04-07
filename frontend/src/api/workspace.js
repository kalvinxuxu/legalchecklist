import request from './request'

export const workspaceApi = {
  /**
   * 获取工作区列表
   */
  getList: () =>
    request.get('/workspaces/'),

  /**
   * 创建工作区
   * @param {Object} data - 工作区信息
   * @param {string} data.name - 工作区名称
   */
  create: (data) =>
    request.post('/workspaces/', data),

  /**
   * 获取工作区详情
   * @param {string} id - 工作区 ID
   */
  getDetail: (id) =>
    request.get(`/workspaces/${id}`),

  /**
   * 更新工作区
   * @param {string} id - 工作区 ID
   * @param {Object} data - 更新信息
   */
  update: (id, data) =>
    request.put(`/workspaces/${id}`, data),

  /**
   * 删除工作区
   * @param {string} id - 工作区 ID
   */
  delete: (id) =>
    request.delete(`/workspaces/${id}`)
}
