# 法务 AI SaaS 平台技术方案（国内版）

> 面向中小企业的轻量化合同审查工具
> 技术栈全面采用国内可访问的云服务

---

## 一、整体技术架构

```
┌─────────────────────────────────────────────────────────────┐
│                     用户层                                   │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐                  │
│  │   Web    │  │  微信小程序  │  │  H5     │                  │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘                  │
└───────┼─────────────┼─────────────┼─────────────────────────┘
        │             │             │
        └─────────────┴──────┬──────┘
                             │
                    ┌────────▼────────┐
                    │   阿里云 SLB    │  ← 统一入口
                    │ saas.yourdomain │
                    └────────┬────────┘
                             │
              ┌──────────────┴──────────────┐
              │                             │
      ┌───────▼───────┐           ┌────────▼────────┐
      │   前端托管     │           │   后端服务       │
      │   阿里云 OSS   │           │   阿里云 ECS     │
      │   + CDN      │           │   或腾讯云 CVM    │
      └───────────────┘           └────────┬────────┘
                                           │
              ┌────────────────────────────┼────────────────┐
              │                            │                │
      ┌───────▼───────┐          ┌────────▼──────┐  ┌──────▼──────┐
      │   RDS MySQL   │          │   Redis      │  │   向量检索   │
      │   (多租户)    │          │   (缓存)      │  │   ES/PG     │
      └───────────────┘          └───────────────┘  └─────────────┘
```

---

## 二、前端技术栈

### 技术选型

| 层级 | 技术选型 | 理由 |
|------|---------|------|
| **框架** | Vue 3 + Vite | 国内生态好、文档中文、人才多 |
| **UI 库** | Element Plus / Ant Design Vue | 成熟、组件全 |
| **状态管理** | Pinia | Vuex 官方替代者 |
| **HTTP** | Axios + 请求拦截器 | 标准方案 |
| **小程序** | uni-app | 一套代码多端发布（微信/支付宝/抖音） |
| **托管** | 阿里云 OSS+CDN | 便宜、快速、无需备案服务器 |
| **域名备案** | 阿里云代备案 | 免费、一站式 |

### 项目结构

```
frontend/
├── src/
│   ├── views/
│   │   ├── Landing/          # 落地页
│   │   ├── Auth/             # 登录注册
│   │   │   ├── Login.vue
│   │   │   ├── Register.vue
│   │   │   └── WxCallback.vue  # 微信回调
│   │   └── Workspace/        # 工作台
│   │       ├── Layout.vue      # 带 Sidebar
│   │       ├── Dashboard.vue
│   │       ├── Upload.vue
│   │       └── ReviewResult.vue
│   ├── components/
│   │   ├── ContractUploader.vue
│   │   ├── RiskReport.vue
│   │   └── RiskTag.vue
│   ├── api/
│   │   ├── request.js        # Axios 实例 + 拦截器
│   │   ├── auth.js
│   │   ├── contract.js
│   │   └── tenant.js
│   ├── store/
│   │   ├── user.js
│   │   └── tenant.js
│   ├── router/
│   │   └── index.js          # 路由 + 守卫
│   └── utils/
│       ├── auth.js           # Token 处理
│       └── tenant.js         # 租户上下文
├── public/
├── package.json
└── vite.config.js
```

### Axios 请求拦截器

```javascript
// src/api/request.js
import axios from 'axios'
import { ElMessage } from 'element-plus'

const request = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL,  // https://api.yourdomain.com
  timeout: 30000
})

// 请求拦截器 - 自动添加 Token 和租户 ID
request.interceptors.request.use(config => {
  const token = localStorage.getItem('token')
  const tenantId = localStorage.getItem('current_tenant_id')
  const workspaceId = localStorage.getItem('current_workspace_id')

  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  if (tenantId) {
    config.headers['X-Tenant-ID'] = tenantId
  }
  if (workspaceId) {
    config.headers['X-Workspace-ID'] = workspaceId
  }

  return config
})

// 响应拦截器 - 统一处理 401/403
request.interceptors.response.use(
  response => response.data,
  error => {
    if (error.response?.status === 401) {
      // Token 过期，跳转登录
      localStorage.removeItem('token')
      window.location.href = '/login'
    }
    if (error.response?.status === 403) {
      // 无权限
      ElMessage.error('无权访问该工作区')
    }
    return Promise.reject(error)
  }
)

export default request
```

### 多租户路由守卫

```javascript
// src/router/index.js
import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  { path: '/', component: () => import('@/views/Landing/index.vue') },
  { path: '/login', component: () => import('@/views/Auth/Login.vue') },
  {
    path: '/workspace/:workspaceId',
    component: () => import('@/views/Workspace/Layout.vue'),
    meta: { requiresAuth: true },
    children: [
      { path: '', component: () => import('@/views/Workspace/Dashboard.vue') },
      { path: 'upload', component: () => import('@/views/Workspace/Upload.vue') },
      { path: 'review/:contractId', component: () => import('@/views/Workspace/ReviewResult.vue') },
    ]
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// 全局守卫 - 验证租户权限
router.beforeEach(async (to, from, next) => {
  if (to.meta.requiresAuth) {
    const token = localStorage.getItem('token')
    if (!token) {
      return next('/login')
    }

    // 如果路径包含 workspaceId，验证用户是否有权限
    if (to.params.workspaceId) {
      const hasPermission = await verifyWorkspacePermission(to.params.workspaceId)
      if (!hasPermission) {
        return next('/403')
      }
      // 保存当前租户上下文
      localStorage.setItem('current_workspace_id', to.params.workspaceId)
    }
  }
  next()
})

async function verifyWorkspacePermission(workspaceId) {
  // 调用后端 API 验证
  try {
    const res = await axios.get(`/api/v1/workspaces/${workspaceId}/verify`)
    return res.data.valid
  } catch {
    return false
  }
}

export default router
```

### 租户上下文管理

```javascript
// src/store/tenant.js
import { defineStore } from 'pinia'

export const useTenantStore = defineStore('tenant', {
  state: () => ({
    currentTenantId: null,
    currentWorkspaceId: null,
    tenantInfo: null
  }),

  getters: {
    isLoggedIn: (state) => !!state.currentTenantId,
    tenantName: (state) => state.tenantInfo?.name
  },

  actions: {
    setTenant(tenantId, workspaceId, info) {
      this.currentTenantId = tenantId
      this.currentWorkspaceId = workspaceId
      this.tenantInfo = info

      // 持久化
      localStorage.setItem('current_tenant_id', tenantId)
      localStorage.setItem('current_workspace_id', workspaceId)
    },

    logout() {
      this.currentTenantId = null
      this.currentWorkspaceId = null
      this.tenantInfo = null
      localStorage.removeItem('token')
      localStorage.removeItem('current_tenant_id')
      localStorage.removeItem('current_workspace_id')
    }
  }
})
```

---

## 三、后端技术栈

### 技术选型

| 组件 | 选型 | 云服务 |
|------|------|--------|
| **框架** | FastAPI (Python) | 阿里云 ECS / 腾讯云 CVM |
| **ORM** | SQLAlchemy 2.0 + aiomysql | 异步 MySQL 驱动 |
| **数据库** | MySQL 8.0 | 阿里云 RDS / 腾讯云 CDB |
| **缓存** | Redis | 阿里云 Redis / 腾讯云 CKV |
| **向量检索** | Elasticsearch 8.x | 阿里云 ES / 自建 |
| **文件存储** | OSS / COS | 阿里云 OSS / 腾讯云 COS |
| **消息队列** | RabbitMQ / RocketMQ | 异步审查任务 |

### 项目结构

```
backend/
├── app/
│   ├── api/
│   │   ├── v1/
│   │   │   ├── endpoints/
│   │   │   │   ├── auth.py          # 登录注册（含微信）
│   │   │   │   ├── contracts.py     # 合同 CRUD
│   │   │   │   ├── workspaces.py    # 工作区管理
│   │   │   │   └── review.py        # 审查接口
│   │   │   └── deps.py              # 依赖注入
│   ├── core/
│   │   ├── config.py                # 配置（从环境变量读取）
│   │   ├── security.py              # JWT/密码加密
│   │   └── tenant.py                # 租户隔离逻辑
│   ├── db/
│   │   ├── base.py
│   │   └── session.py
│   ├── models/
│   │   ├── user.py
│   │   ├── tenant.py
│   │   ├── workspace.py
│   │   └── contract.py
│   ├── schemas/
│   │   └── *.py                     # Pydantic 模型
│   ├── services/
│   │   ├── rag/
│   │   │   ├── embedder.py          # 调用智谱/通义 API
│   │   │   ├── vector_store.py      # ES 向量写入
│   │   │   └── retriever.py         # 检索
│   │   ├── llm/
│   │   │   └── client.py            # 调用智谱/文心/通义
│   │   └── wx_login.py              # 微信登录
│   └── middleware/
│       ├── auth.py                  # JWT 验证
│       └── tenant_isolation.py      # 租户隔离
├── alembic/                         # 数据库迁移
├── requirements.txt
└── main.py
```

---

## 四、数据库设计

### 多租户数据模型

```sql
-- 租户表
CREATE TABLE tenants (
    id VARCHAR(36) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    plan ENUM('free', 'pro', 'enterprise') DEFAULT 'free',
    wx_appid VARCHAR(50),  -- 微信小程序关联
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 工作区表
CREATE TABLE workspaces (
    id VARCHAR(36) PRIMARY KEY,
    tenant_id VARCHAR(36) NOT NULL,
    name VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (tenant_id) REFERENCES tenants(id),
    INDEX idx_tenant_id (tenant_id)
);

-- 用户表
CREATE TABLE users (
    id VARCHAR(36) PRIMARY KEY,
    tenant_id VARCHAR(36) NOT NULL,
    email VARCHAR(255) UNIQUE,
    phone VARCHAR(20) UNIQUE,
    wx_openid VARCHAR(100),  -- 微信 OpenID
    wx_unionid VARCHAR(100), -- 微信 UnionID
    password_hash VARCHAR(255),
    role ENUM('admin', 'member') DEFAULT 'member',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (tenant_id) REFERENCES tenants(id)
);

-- 合同表（核心业务数据）
CREATE TABLE contracts (
    id VARCHAR(36) PRIMARY KEY,
    workspace_id VARCHAR(36) NOT NULL,
    user_id VARCHAR(36) NOT NULL,
    file_name VARCHAR(500),
    file_path VARCHAR(1000),  -- OSS/COS 路径
    file_hash VARCHAR(64),    -- 去重
    contract_type VARCHAR(50), -- NDA/劳动合同/...

    review_status ENUM('pending', 'processing', 'completed', 'failed') DEFAULT 'pending',
    review_result JSON,       -- 审查报告
    risk_level ENUM('low', 'medium', 'high'),

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    FOREIGN KEY (workspace_id) REFERENCES workspaces(id),
    FOREIGN KEY (user_id) REFERENCES users(id),
    INDEX idx_workspace_status (workspace_id, review_status)
);

-- 向量检索表
CREATE TABLE legal_knowledge (
    id VARCHAR(36) PRIMARY KEY,
    content_type ENUM('law', 'case', 'template', 'rule'),
    content TEXT NOT NULL,
    embedding JSON,  -- 向量数据（MySQL 8.0 可存 JSON）
    metadata JSON,   -- 元数据：法条号、法院、...
    tenant_id VARCHAR(36),  -- NULL 表示公共知识库
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_content_type (content_type),
    INDEX idx_tenant (tenant_id)
);
```

---

## 五、租户隔离中间件

### Python 实现

```python
# app/middleware/tenant_isolation.py
from fastapi import Request, HTTPException, Depends
from app.core.security import verify_token
from app.db.session import get_db
import aiomysql

async def get_tenant_context(
    request: Request,
    db: aiomysql.Connection = Depends(get_db)
):
    """
    从 Header 或路径提取租户 ID，验证用户权限
    """
    # 1. 从 JWT 获取用户 ID
    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    if not token:
        raise HTTPException(status_code=401, detail="未认证")

    user_id = verify_token(token)
    if not user_id:
        raise HTTPException(status_code=401, detail="Token 无效")

    # 2. 从路径或 Header 获取 workspace_id
    workspace_id = request.path_params.get("workspace_id") \
                   or request.headers.get("X-Workspace-ID")

    if not workspace_id:
        raise HTTPException(status_code=400, detail="缺少 workspace_id")

    # 3. 验证用户是否有权访问该工作区
    async with db.cursor() as cursor:
        await cursor.execute("""
            SELECT w.id, w.tenant_id, u.role
            FROM workspaces w
            JOIN users u ON u.tenant_id = w.tenant_id
            WHERE w.id = %s AND u.id = %s
        """, (workspace_id, user_id))

        result = await cursor.fetchone()

        if not result:
            raise HTTPException(status_code=403, detail="无权访问该工作区")

    return {
        "tenant_id": result[1],
        "workspace_id": workspace_id,
        "user_id": user_id,
        "role": result[2]
    }

# API 中使用
@router.post("/workspace/{workspace_id}/contracts")
async def upload_contract(
    workspace_id: str,
    file: UploadFile,
    tenant_ctx: dict = Depends(get_tenant_context),
    db = Depends(get_db)
):
    # 数据隔离已保证，直接写入
    async with db.cursor() as cursor:
        await cursor.execute("""
            INSERT INTO contracts (workspace_id, user_id, file_name, ...)
            VALUES (%s, %s, %s, ...)
        """, (
            tenant_ctx["workspace_id"],
            tenant_ctx["user_id"],
            file.filename,
            ...
        ))
    await db.commit()
```

---

## 六、RAG 实现（国内 LLM）

### Embedding 服务

```python
# app/services/rag/embedder.py
from typing import List
import httpx
import os

class TextEmbedder:
    """
    调用国内 Embedding API
    可选：智谱 GLM、百度文心、阿里通义、腾讯混元
    """
    def __init__(self):
        # 以智谱为例
        self.api_key = os.getenv("ZHIPU_API_KEY")
        self.url = "https://open.bigmodel.cn/api/paas/v4/embeddings"
        self.model = "embedding-2"

    async def embed(self, text: str) -> List[float]:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                self.url,
                headers={"Authorization": f"Bearer {self.api_key}"},
                json={"model": self.model, "input": text}
            )
            resp.raise_for_status()
            data = resp.json()
            return data["data"][0]["embedding"]
```

### Elasticsearch 向量检索

```python
# app/services/rag/vector_store.py
from elasticsearch import AsyncElasticsearch
from typing import List

class ESVectorStore:
    def __init__(self):
        self.es = AsyncElasticsearch(
            hosts=["https://es-cn-xxx.elasticsearch.aliyuncs.com:9200"],
            http_auth=("username", "password")
        )

    async def create_index(self):
        """创建向量索引"""
        await self.es.indices.create(
            index="legal_knowledge",
            body={
                "mappings": {
                    "properties": {
                        "content": {"type": "text"},
                        "embedding": {
                            "type": "dense_vector",
                            "dims": 1024  # 智谱 embedding-2 维度
                        },
                        "content_type": {"type": "keyword"},
                        "tenant_id": {"type": "keyword"},  # NULL 或租户 ID
                        "metadata": {"type": "object"}
                    }
                }
            }
        )

    async def search(
        self,
        query_vector: List[float],
        tenant_id: str,
        top_k: int = 5
    ):
        """
        检索：公共知识库 + 租户私有库
        """
        body = {
            "size": top_k,
            "query": {
                "bool": {
                    "should": [
                        # 向量相似度
                        {
                            "script_score": {
                                "query": {"match_all": {}},
                                "script": {
                                    "source": "cosineSimilarity(params.queryVector, 'embedding') + 1.0",
                                    "params": {"queryVector": query_vector}
                                }
                            }
                        }
                    ],
                    "filter": [
                        # 租户隔离：公共 OR 当前租户
                        {
                            "bool": {
                                "should": [
                                    {"term": {"tenant_id": tenant_id}},
                                    {"bool": {"must_not": {"exists": {"field": "tenant_id"}}}}
                                ]
                            }
                        }
                    ]
                }
            }
        }

        resp = await self.es.search(index="legal_knowledge", body=body)
        return resp["hits"]["hits"]
```

### RAG 检索器

```python
# app/services/rag/retriever.py
class LegalRAGRetriever:
    def __init__(self):
        self.embedder = TextEmbedder()
        self.vector_store = ESVectorStore()

    async def retrieve(
        self,
        query: str,
        tenant_id: str,
        top_k: int = 5
    ) -> List[dict]:
        """
        两层检索：标准知识库 + 租户自定义知识库
        """
        # 1. 生成查询向量
        query_vector = await self.embedder.embed(query)

        # 2. 检索
        results = await self.vector_store.search(
            query_vector=query_vector,
            tenant_id=tenant_id,
            top_k=top_k
        )

        return [
            {
                "id": hit["_id"],
                "content": hit["_source"]["content"],
                "metadata": hit["_source"]["metadata"],
                "score": hit["_score"]
            }
            for hit in results
        ]
```

### 合同审查服务

```python
# app/services/contract_review.py
from app.services.rag.retriever import LegalRAGRetriever

class ContractReviewService:
    def __init__(self):
        self.rag = LegalRAGRetriever()
        self.llm = self._init_llm()  # 初始化 LLM 客户端

    def _init_llm(self):
        """初始化 LLM（智谱/文心/通义）"""
        # 以智谱为例
        from zhipuai import ZhipuAI
        return ZhipuAI(api_key=os.getenv("ZHIPU_API_KEY"))

    async def review_contract(
        self,
        contract_text: str,
        contract_type: str,
        tenant_ctx: dict
    ) -> dict:
        """
        审查合同并生成报告
        """
        # 1. 检索相关知识
        context = await self.rag.retrieve(
            query=f"{contract_type} 合同审查要点",
            tenant_id=tenant_ctx["tenant_id"]
        )

        # 2. 构建 prompt
        prompt = f"""你是一位专业律师，请审查以下{contract_type}合同。

参考法律依据：
{self._format_context(context)}

合同内容：
{contract_text}

请输出：
1. 缺失条款
2. 风险条款（标注风险等级：高/中/低）
3. 修改建议
4. 引用法条（带原文）

以 JSON 格式输出。
"""

        # 3. 调用 LLM
        response = self.llm.chat.completions.create(
            model="glm-4",
            messages=[{"role": "user", "content": prompt}]
        )

        # 4. 解析结果并添加置信度
        import json
        review_result = json.loads(response.choices[0].message.content)
        review_result["confidence_score"] = self._calculate_confidence(context)

        return review_result

    def _format_context(self, context: List[dict]) -> str:
        return "\n\n".join([item["content"] for item in context])

    def _calculate_confidence(self, context: List[dict]) -> float:
        # 基于检索结果质量计算置信度
        if len(context) == 0:
            return 0.3
        avg_score = sum(item["score"] for item in context) / len(context)
        return min(1.0, avg_score / 2.0 + 0.5)
```

---

## 七、微信小程序接入

### 小程序登录流程

```javascript
// 小程序端 - pages/login/login.js
Page({
  data: {
    loading: false
  },

  async onLogin() {
    this.setData({ loading: true })

    try {
      // 1. 获取 code
      const { code } = await wx.login()

      // 2. 发送到后端
      const res = await wx.request({
        url: 'https://api.yourdomain.com/api/v1/auth/wx-login',
        method: 'POST',
        data: { code }
      })

      // 3. 保存 Token
      const { token, tenant_id, workspace_id } = res.data
      wx.setStorageSync('token', token)
      wx.setStorageSync('current_tenant_id', tenant_id)
      wx.setStorageSync('current_workspace_id', workspace_id)

      // 4. 跳转工作台
      wx.switchTab({ url: '/pages/workspace/index' })
    } catch (err) {
      wx.showToast({ title: '登录失败', icon: 'none' })
    } finally {
      this.setData({ loading: false })
    }
  }
})
```

### 后端微信登录处理

```python
# app/services/wx_login.py
import httpx

async def wx_login(code: str, db):
    """
    微信小程序登录
    """
    # 1. 用 code 换 OpenID
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            "https://api.weixin.qq.com/sns/jscode2session",
            params={
                "appid": os.getenv("WX_APPID"),
                "secret": os.getenv("WX_SECRET"),
                "js_code": code,
                "grant_type": "authorization_code"
            }
        )
        data = resp.json()

        if "errcode" in data:
            raise HTTPException(status_code=400, detail=f"微信登录失败：{data['errmsg']}")

        openid = data["openid"]
        session_key = data["session_key"]

    # 2. 查找或创建用户
    async with db.cursor() as cursor:
        await cursor.execute(
            "SELECT id, tenant_id, role FROM users WHERE wx_openid = %s",
            (openid,)
        )
        user = await cursor.fetchone()

        if not user:
            # 新用户，自动创建租户
            import uuid
            tenant_id = str(uuid.uuid4())
            user_id = str(uuid.uuid4())
            workspace_id = str(uuid.uuid4())

            await cursor.execute(
                "INSERT INTO tenants (id, name, plan) VALUES (%s, %s, %s)",
                (tenant_id, "新用户", "free")
            )
            await cursor.execute(
                "INSERT INTO users (id, tenant_id, wx_openid, role) VALUES (%s, %s, %s, %s)",
                (user_id, tenant_id, openid, "admin")
            )
            await cursor.execute(
                "INSERT INTO workspaces (id, tenant_id, name) VALUES (%s, %s, %s)",
                (workspace_id, tenant_id, "默认工作区")
            )
            await db.commit()

            user = (user_id, tenant_id, "admin")

    # 3. 生成 JWT
    from app.core.security import create_access_token
    token = create_access_token(data={"sub": user[0]})

    return {
        "token": token,
        "tenant_id": user[1],
        "workspace_id": workspace_id,
        "role": user[2]
    }
```

---

## 八、云服务选型与成本

### 推荐配置

| 组件 | 推荐服务 | 配置 | 月成本 |
|------|---------|------|--------|
| **前端托管** | 阿里云 OSS+CDN | 100GB 存储 +1TB 流量 | ¥50 |
| **域名+SSL** | 阿里云域名 | .com + 免费 SSL | ¥60/年 |
| **后端服务器** | 腾讯云轻量应用服务器 | 2 核 4G | ¥80 |
| **数据库** | 阿里云 RDS MySQL | 基础版 2 核 4G | ¥170 |
| **缓存** | 腾讯云 Redis | 1GB 主从版 | ¥50 |
| **向量检索** | 自建 ES（ECS 上） | 与后端同机 | ¥0 |
| **文件存储** | 阿里云 OSS | 100GB | ¥20 |
| **LLM** | 智谱 AI | 按量付费 | ¥200-500 |
| **备案** | 阿里云免费 | - | ¥0 |

**MVP 总成本：¥600-900/月**

### 各阶段成本预估

| 阶段 | 用户量 | 月成本 |
|------|-------|--------|
| **MVP** | 0-100 | ¥600-900 |
| **增长期** | 100-1000 | ¥2000-5000 |
| **成熟期** | 1000+ | ¥10000+ |

---

## 九、部署架构

### MVP 阶段（单服务器）

```
┌─────────────────────────────────────────────────────────┐
│              腾讯云轻量应用服务器 (2 核 4G)                │
│  ┌─────────────────────────────────────────────────┐   │
│  │              Docker Compose                      │   │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐      │   │
│  │  │ FastAPI  │  │  MySQL   │  │  Redis   │      │   │
│  │  │ + Nginx  │  │ (容器)   │  │ (容器)   │      │   │
│  │  └──────────┘  └──────────┘  └──────────┘      │   │
│  └─────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
                          ▲
                          │
              ┌───────────┴───────────┐
              │     阿里云 SLB        │
              └───────────┬───────────┘
                          │
              ┌───────────┴───────────┐
              │   阿里云 OSS+CDN      │
              │   (前端静态资源)      │
              └───────────────────────┘
```

### Docker Compose 配置

```yaml
# docker-compose.yml
version: '3.8'

services:
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - app

  app:
    build: ./backend
    environment:
      - DATABASE_URL=mysql://root:password@db:3306/legal_saaS
      - REDIS_URL=redis://redis:6379
      - ZHIPU_API_KEY=${ZHIPU_API_KEY}
      - WX_APPID=${WX_APPID}
      - WX_SECRET=${WX_SECRET}
    depends_on:
      - db
      - redis

  db:
    image: mysql:8.0
    environment:
      - MYSQL_ROOT_PASSWORD=password
      - MYSQL_DATABASE=legal_saaS
    volumes:
      - mysql_data:/var/lib/mysql

  redis:
    image: redis:alpine
    volumes:
      - redis_data:/data

volumes:
  mysql_data:
  redis_data:
```

### Nginx 配置

```nginx
# nginx.conf
server {
    listen 80;
    server_name saas.yourdomain.com;

    # HTTP 跳转 HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name saas.yourdomain.com;

    ssl_certificate /etc/nginx/ssl/fullchain.pem;
    ssl_certificate_key /etc/nginx/ssl/privkey.pem;

    # 前端静态资源
    location / {
        root /usr/share/nginx/html;
        try_files $uri $uri/ /index.html;
    }

    # 后端 API 反向代理
    location /api/ {
        proxy_pass http://app:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```

---

## 十、ICP 备案流程

### 备案步骤

```
1. 购买域名（阿里云/腾讯云）
         ↓
2. 域名实名认证（1-3 工作日）
         ↓
3. 提交备案申请（阿里云/腾讯云代备案系统）
   - 上传身份证
   - 上传域名证书
   - 填写网站信息
         ↓
4. 阿里云/腾讯云初审（1-2 工作日）
         ↓
5. 管局审核（10-20 工作日）
         ↓
6. 备案成功，获得 ICP 备案号
         ↓
7. 域名解析到国内服务器
```

### 备案所需材料

| 材料 | 说明 |
|------|------|
| 域名证书 | 阿里云/腾讯云后台下载 |
| 身份证正反面 | 个人备案 or 企业法人 |
| 营业执照 | 企业备案需要 |
| 网站名称 | 不能包含"中国""国家"等字眼 |
| 网站服务内容 | 选择"其他"或"企业服务" |

### 注意事项

- 备案期间域名不能访问
- 个人不能备案商业性质网站
- 建议使用企业主体备案

---

## 十一、技术选型总结

### 完整技术栈

| 层级 | 选型 |
|------|------|
| **前端框架** | Vue 3 + Vite + Element Plus |
| **小程序** | uni-app（微信/支付宝/抖音） |
| **后端框架** | FastAPI (Python) |
| **数据库** | MySQL 8.0 (阿里云 RDS) |
| **缓存** | Redis (阿里云 Redis) |
| **向量库** | Elasticsearch (自建) |
| **文件存储** | 阿里云 OSS |
| **LLM** | 智谱 GLM-4 |
| **Embedding** | 智谱 embedding-2 |
| **部署** | Docker Compose + 云服务器 |
| **域名备案** | 阿里云/腾讯云免费代办 |

### 国内 LLM API 对比

| 厂商 | 模型 | 价格 (元/千 tokens) | 特点 |
|------|------|-------------------|------|
| **智谱 AI** | GLM-4 | 输入 0.05 / 输出 0.10 | 法律场景表现好 |
| **百度文心** | ERNIE 4.0 | 输入 0.06 / 输出 0.12 | 中文理解强 |
| **阿里通义** | Qwen-Max | 输入 0.04 / 输出 0.08 | 性价比高 |
| **腾讯混元** | HunYuan | 输入 0.05 / 输出 0.10 | 微信生态好 |

---

## 十二、下一步行动

### 第一周：基础搭建
- [ ] 购买域名并开始备案
- [ ] 购买云服务器
- [ ] 搭建开发环境（Docker Compose）
- [ ] 创建数据库表结构

### 第二周：核心功能
- [ ] 实现用户注册/登录（含微信）
- [ ] 实现租户管理
- [ ] 实现合同上传接口

### 第三周：RAG 集成
- [ ] 接入智谱 Embedding API
- [ ] 搭建 Elasticsearch 向量索引
- [ ] 实现 RAG 检索

### 第四周：LLM 审查
- [ ] 接入智谱 GLM-4
- [ ] 实现审查 prompt 模板
- [ ] 前端展示审查报告

### 第五周：测试上线
- [ ] 内测（邀请 5-10 家种子用户）
- [ ] 修复 bug
- [ ] 正式上线

---

## 附录：参考资源

- [智谱 AI 开放平台](https://open.bigmodel.cn/)
- [阿里云 RDS MySQL](https://www.aliyun.com/product/rds/mysql)
- [阿里云 OSS](https://www.aliyun.com/product/oss)
- [uni-app 官网](https://uniapp.dcloud.net.cn/)
- [FastAPI 文档](https://fastapi.tiangolo.com/)
- [微信小程序开发文档](https://developers.weixin.qq.com/miniprogram/dev/framework/)
