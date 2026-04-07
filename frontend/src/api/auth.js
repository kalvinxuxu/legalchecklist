import request from './request'

export const authApi = {
  /**
   * 用户登录
   * @param {string} email - 邮箱
   * @param {string} password - 密码
   */
  login: (email, password) =>
    request.post('/auth/login', { email, password }),

  /**
   * 用户注册
   * @param {Object} data - 注册信息
   * @param {string} data.email - 邮箱
   * @param {string} data.password - 密码
   * @param {string} data.company_name - 公司名称
   */
  register: (data) =>
    request.post('/auth/register', data),

  /**
   * 获取当前用户信息
   */
  getCurrentUser: () =>
    request.get('/auth/me')
}
