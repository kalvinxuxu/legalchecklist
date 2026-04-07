# Phase 4: 前端开发 - 执行计划

**版本**: v1.0
**创建日期**: 2026-03-31
**完成日期**: 2026-03-31
**状态**: 已完成

---

## 完成情况

| 任务 | 状态 | 说明 |
|------|------|------|
| 4.1 配置全局样式和主题 | ✅ | 创建莫兰迪粉彩配色主题 |
| 4.2 实现用户认证 Store | ✅ | Pinia 状态管理 |
| 4.3 实现注册页面 | ✅ | 支持邮箱注册 + 表单验证 |
| 4.4 实现合同列表页 | ✅ | 表格展示 + 状态标签 + 操作 |
| 4.5 实现审查结果展示页 | ✅ | 核心页面，展示完整审查报告 |
| 4.6 实现 API 服务层封装 | ✅ | auth/contracts/workspace |
| 4.7 前端与后端联调 | ⏳ | 待后端启动后联调 |

---

## 新增文件清单

### 样式
```
frontend/src/styles/
└── theme.css              # 莫兰迪粉彩主题
```

### 状态管理
```
frontend/src/stores/
└── auth.js                # 用户认证 Store
```

### API 服务层
```
frontend/src/api/
├── auth.js                # 认证 API
├── contracts.js           # 合同 API
└── workspace.js           # 工作区 API
```

### 页面
```
frontend/src/views/
├── Register.vue           # 注册页面
├── Contracts.vue          # 合同列表页
└── Review.vue             # 审查结果展示页
```

---

## 修改文件清单

| 文件 | 修改内容 |
|------|---------|
| `frontend/src/main.js` | 添加全局样式引入 |
| `frontend/src/router/index.js` | 添加注册路由和子路由 |
| `frontend/src/views/Login.vue` | 使用 Auth Store，添加注册链接 |
| `frontend/src/views/Dashboard.vue` | 添加最近合同列表 |
| `frontend/src/views/Upload.vue` | 使用新的 API 服务层 |

---

## 构建验证

```bash
npm run build
# ✓ built in 4.79s
```

构建成功，无错误。

---

## 下一步

1. 启动后端服务进行联调
2. 测试注册/登录流程
3. 测试合同上传和审查流程
4. 修复可能的 Bug

---

**Phase 4 完成，准备进行前后端联调**

---

## 现状分析

### 已有基础

| 文件 | 状态 | 说明 |
|------|------|------|
| `frontend/src/main.js` | ✅ | Vue 3 + Pinia + Element Plus 已配置 |
| `frontend/src/router/index.js` | ✅ | 基础路由已配置 |
| `frontend/src/App.vue` | ✅ | 根组件 |
| `frontend/src/api/request.js` | ✅ | Axios 实例 + 拦截器 |
| `frontend/src/views/Login.vue` | ✅ | 登录页面（基础版） |
| `frontend/src/views/Landing.vue` | ✅ | 落地页（基础版） |
| `frontend/src/views/Workspace.vue` | ✅ | 工作台布局 |
| `frontend/src/views/Dashboard.vue` | ✅ | 仪表盘（占位） |
| `frontend/src/views/Upload.vue` | ✅ | 上传页面（基础版） |

### 缺失功能

- [ ] 用户认证 Store（Pinia）
- [ ] 注册页面
- [ ] 合同列表页
- [ ] 审查结果展示页（核心）
- [ ] API 服务层封装
- [ ] 全局样式和主题配置
- [ ] 前端与后端联调

---

## 任务分解

### 任务列表

| ID | 任务 | 优先级 | 预估工时 | 验收标准 |
|----|------|--------|---------|---------|
| 4.1 | 配置全局样式和主题 | P0 | 2h | 符合莫兰迪粉彩配色规范 |
| 4.2 | 实现用户认证 Store | P0 | 2h | 支持登录/登出/状态持久化 |
| 4.3 | 实现注册页面 | P1 | 3h | 支持邮箱注册 + 表单验证 |
| 4.4 | 实现合同列表页 | P0 | 4h | 展示合同列表 + 状态 + 操作 |
| 4.5 | 实现审查结果展示页 | P0 | 6h | 展示风险条款/缺失条款/法条引用 |
| 4.6 | 实现 API 服务层封装 | P0 | 3h | 统一的 API 调用接口 |
| 4.7 | 前端与后端联调 | P0 | 4h | 端到端流程打通 |

---

## 详细实现方案

### 4.1 全局样式和主题

**文件**: `frontend/src/styles/theme.css`

```css
:root {
  /* 莫兰迪粉彩系 - 蓝色 */
  --color-blue-bg: #E3F2FD;
  --color-blue-text: #1565C0;

  /* 莫兰迪粉彩系 - 绿色 */
  --color-green-bg: #E8F5E9;
  --color-green-text: #2E7D32;

  /* 莫兰迪粉彩系 - 橙色 */
  --color-orange-bg: #FFF3E0;
  --color-orange-text: #E65100;

  /* 莫兰迪粉彩系 - 红色 */
  --color-red-bg: #FFEBEE;
  --color-red-text: #C62828;

  /* 莫兰迪粉彩系 - 紫色 */
  --color-purple-bg: #F3E5F5;
  --color-purple-text: #6A1B9A;

  /* 中性色 */
  --color-text-primary: #212121;
  --color-text-secondary: #424242;
  --color-text-tertiary: #757575;
  --color-border: #E0E0E0;
  --color-bg: #F8F9FA;

  /* 圆角 */
  --radius-sm: 4px;
  --radius-md: 8px;
  --radius-lg: 12px;

  /* 阴影 */
  --shadow-sm: 0 2px 8px rgba(0,0,0,0.08);
}
```

---

### 4.2 用户认证 Store

**文件**: `frontend/src/stores/auth.js`

**功能**:
- 用户登录/登出
- Token 存储和验证
- 用户信息持久化

**伪代码**:
```javascript
import { defineStore } from 'pinia'
import { authApi } from '@/api/auth'

export const useAuthStore = defineStore('auth', {
  state: () => ({
    token: localStorage.getItem('token') || null,
    user: JSON.parse(localStorage.getItem('user') || 'null')
  }),

  getters: {
    isAuthenticated: (state) => !!state.token,
    userEmail: (state) => state.user?.email
  },

  actions: {
    async login(email, password) {
      const response = await authApi.login(email, password)
      this.token = response.access_token
      localStorage.setItem('token', response.access_token)
    },

    async register(email, password, companyName) {
      await authApi.register(email, password, companyName)
    },

    logout() {
      this.token = null
      this.user = null
      localStorage.removeItem('token')
      localStorage.removeItem('user')
    }
  }
})
```

---

### 4.3 注册页面

**文件**: `frontend/src/views/Register.vue`

**表单字段**:
- 公司名称（必填）
- 邮箱（必填，邮箱格式验证）
- 密码（必填，最少 6 位）
- 确认密码（必填，与密码一致）

**注册成功后**:
- 自动登录并跳转到工作台

---

### 4.4 合同列表页

**文件**: `frontend/src/views/Contracts.vue`

**功能**:
- 合同列表展示（表格）
- 合同状态标签（待审查/审查中/已完成）
- 合同类型标签（NDA/劳动合同/其他）
- 操作按钮（查看报告/删除）
- 上传按钮

**数据列**:
- 合同名称
- 合同类型
- 上传时间
- 状态
- 风险等级
- 操作

---

### 4.5 审查结果展示页（核心）

**文件**: `frontend/src/views/Review.vue`

**页面结构**:
```
┌────────────────────────────────────────────────────┐
│ 合同名称：XXX 采购合同                    [导出报告] │
├────────────────────────────────────────────────────┤
│ 审查状态：✅ 完成  |  审查时间：32 秒  |  置信度：87%  │
├────────────────────────────────────────────────────┤
│                                                     │
│  ┌─────────────┬─────────────┬─────────────┐       │
│  │ 风险条款 3  │ 缺失条款 2  │ 修改建议 5  │       │
│  │   (红色)    │   (橙色)    │   (蓝色)    │       │
│  └─────────────┴─────────────┴─────────────┘       │
│                                                     │
├────────────────────────────────────────────────────┤
│ 风险条款                                             │
│ ┌─────────────────────────────────────────────────┐ │
│ │ ⚠️ 高风险 | 违约责任不对等                       │ │
│ │ 原文：第 5 条第 2 款...                          │ │
│ │ 建议：建议修改为对等的违约责任条款...           │ │
│ │ 依据：《民法典》第 584 条...                      │ │
│ └─────────────────────────────────────────────────┘ │
│                                                     │
│ 缺失条款                                             │
│ ┌─────────────────────────────────────────────────┐ │
│ │ 📋 缺少争议解决条款                              │ │
│ │ 建议：建议添加争议解决条款，约定管辖法院...     │ │
│ │ 依据：《民法典》第 470 条...                      │ │
│ └─────────────────────────────────────────────────┘ │
└────────────────────────────────────────────────────┘
```

**设计要点**:
- 使用莫兰迪粉彩配色（风险=红色，缺失=橙色，建议=蓝色）
- 卡片式布局，圆角 8-12px
- 清晰的视觉层级（标题 20px，正文 14px）

---

### 4.6 API 服务层封装

**文件结构**:
```
frontend/src/api/
├── request.js       # Axios 实例（已有）
├── auth.js          # 认证相关 API
├── contracts.js     # 合同相关 API
└── workspace.js     # 工作区相关 API
```

**示例**:
```javascript
// auth.js
import request from './request'

export const authApi = {
  login: (email, password) =>
    request.post('/auth/login', { email, password }),

  register: (data) =>
    request.post('/auth/register', data),

  getCurrentUser: () =>
    request.get('/auth/me')
}

// contracts.js
import request from './request'

export const contractsApi = {
  upload: (file, workspaceId, contractType) => {
    const formData = new FormData()
    formData.append('file', file)
    formData.append('workspace_id', workspaceId)
    formData.append('contract_type', contractType)
    return request.post('/contracts/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
  },

  getList: () => request.get('/contracts/'),

  getDetail: (id) => request.get(`/contracts/${id}`),

  getReviewResult: (id) => request.get(`/contracts/${id}/review`)
}
```

---

### 4.7 前端与后端联调

**联调步骤**:

1. **启动后端服务**
   ```bash
   cd backend
   python main.py
   ```

2. **启动前端开发服务器**
   ```bash
   cd frontend
   npm run dev
   ```

3. **配置代理** (vite.config.js)
   ```javascript
   export default {
     server: {
       proxy: {
         '/api': {
           target: 'http://localhost:8000',
           changeOrigin: true
         }
       }
     }
   }
   ```

4. **测试流程**:
   - 注册新用户
   - 登录
   - 创建工作区
   - 上传合同
   - 查看审查报告

---

## 验收标准

### 功能验收

- [ ] 用户可完成注册流程
- [ ] 用户可完成登录流程
- [ ] 用户可查看工作区列表
- [ ] 用户可上传合同文件
- [ ] 用户可查看合同列表
- [ ] 用户可查看审查报告详情
- [ ] 审查报告包含：风险条款、缺失条款、修改建议、法条引用

### 设计验收

- [ ] 使用莫兰迪粉彩配色
- [ ] 页面响应式设计（PC + 移动）
- [ ] 统一的圆角和间距规范
- [ ] 清晰的视觉层级

### 性能验收

- [ ] 首屏加载时间 < 2 秒
- [ ] 页面切换无明显卡顿
- [ ] 大列表虚拟滚动（如需要）

---

## 依赖项

### 需要后端提供的 API

| 接口 | 方法 | 说明 | 状态 |
|------|------|------|------|
| `/api/v1/auth/register` | POST | 用户注册 | 待确认 |
| `/api/v1/auth/login` | POST | 用户登录 | ✅ |
| `/api/v1/auth/me` | GET | 获取当前用户 | 待确认 |
| `/api/v1/workspaces/` | GET | 获取工作区列表 | 待确认 |
| `/api/v1/contracts/` | GET | 获取合同列表 | 待确认 |
| `/api/v1/contracts/upload` | POST | 上传合同 | ✅ |
| `/api/v1/contracts/{id}` | GET | 获取合同详情 | 待确认 |
| `/api/v1/contracts/{id}/review` | GET | 获取审查结果 | 待确认 |

---

## 下一步

1. 确认后端 API 状态
2. 按任务列表依次实现
3. 联调测试
4. 修复 Bug

---

**准备开始执行 Phase 4 前端开发**
