# 法务 AI SaaS 后端技术栈

## 核心技术架构

```
FastAPI (ASGI) → Uvicorn → 异步数据库 → MySQL/SQLite
                    ↓
              Celery + Redis (异步任务队列)
                    ↓
              文档解析 (pdfplumber / python-docx)
                    ↓
              LLM 服务 (DeepSeek API - RAG 增强)
```

---

## 1. 核心框架

### FastAPI 0.109.0
- **用途**：高性能异步 Web 框架
- **优势**：自动 OpenAPI 文档、类型提示、Pydantic 集成、异步原生支持
- **替代方案**：Flask（同步）、Django（重量级）

```python
app = FastAPI(
    title="法务 AI SaaS API",
    description="面向中小企业的轻量化合同审查服务",
    version="0.1.0",
    lifespan=lifespan,
)
```

### Uvicorn 0.27.0
- **用途**：ASGI 应用服务器
- **启动命令**：`uvicorn main:app --reload --host 0.0.0.0 --port 8000`
- **特性**：支持热重载、多 worker、生产级性能

### Pydantic 2.5.3
- **用途**：数据验证、序列化、settings 管理
- **应用**：API 请求/响应模型、配置管理（`pydantic-settings`）

---

## 2. 数据库层

### SQLAlchemy 2.0.25（异步）
- **用途**：ORM 框架，支持异步操作
- **模式**：AsyncEngine + AsyncSession（异步会话）
- **模型基类**：declarative_base

```python
self.engine = create_async_engine(sqlite_url, echo=True)
self.async_session_maker = async_sessionmaker(
    self.engine,
    class_=AsyncSession,
    expire_on_commit=False,
)
```

### 数据库适配器

| 数据库 | 驱动 | 用途 |
|--------|------|------|
| **SQLite** | `aiosqlite` | 开发环境、轻量部署 |
| **MySQL** | `aiomysql` | 生产环境 |

### 数据模型

```
Tenant（租户）
  └── User（用户）
        └── Workspace（工作空间）
              └── Contract（合同）
                    ├── ContractUnderstanding（合同理解）
                    ├── ClauseLocation（条款定位）
                    └── LegalKnowledge（法律知识库）
```

---

## 3. 认证与安全

### JWT 认证
| 技术 | 用途 |
|------|------|
| `python-jose[cryptography]` | JWT token 生成与验证 |
| `passlib[bcrypt]` | 密码哈希（bcrypt） |

- Token 有效期：可配置
- 存储：localStorage（前端）
- 传输：Authorization Bearer Token

### 密码安全
- 哈希算法：bcrypt
- 盐值：自动生成
- 验证：constant-time 比较

---

## 4. 异步任务队列

### Celery 5.3.0
- **用途**：处理耗时的合同审查任务
- **Broker**：Redis 5.0.1
- **启动**：`python celery_worker.py`

```python
@celery_app.task
def review_contract_task(contract_id: str):
    # 合同审查逻辑
    pass
```

### Redis 5.0.1
- **用途**：Celery 消息代理（broker）
- **端口**：6379
- **DB**：0（默认）

### 任务类型
| 任务 | 描述 |
|------|------|
| `review_contract_task` | 合同审查（PDF/Word → 风险分析） |
| `process_understanding_task` | 合同理解（自然语言问答） |
| `locate_clause_task` | 条款定位（RAG 检索） |

---

## 5. 文档解析

### pdfplumber >= 0.10.0
- **用途**：从 PDF 提取文本和表格
- **特性**：支持多页、表格提取、坐标获取

```python
import pdfplumber
with pdfplumber.open("合同.pdf") as pdf:
    text = pdf.pages[0].extract_text()
```

### python-docx >= 0.8.11
- **用途**：解析 Word 文档（.docx）
- **替代方案**：`python-docx`（只支持 .docx）

---

## 6. LLM 与 RAG

### DeepSeek API（外部）
- **用途**：合同审查的 LLM 能力
- **调用方式**：HTTP API（`httpx`）
- **RAG 增强**：检索相关法条后作为上下文

### httpx 0.26.0
- **用途**：异步 HTTP 客户端，调用 DeepSeek API
- **特性**：支持 async/await、连接池、超时控制

---

## 7. 其他依赖

| 包 | 版本 | 用途 |
|----|------|------|
| `tenacity` | 8.2.3 | 重试机制（LLM 调用失败重试） |
| `python-multipart` | 0.0.6 | 文件上传表单处理 |
| `pydantic-settings` | 2.1.0 | 环境变量管理 |

---

## 8. 部署架构

### 开发环境
```
┌─────────────┐
│   Uvicorn   │  ← SQLite + asyncio 后台任务（无需 Redis）
│  (FastAPI)  │
└─────────────┘
       ↓
┌─────────────┐
│  SQLite DB   │
└─────────────┘
```

### 生产环境
```
┌─────────────┐
│   Nginx     │  ← 反向代理 + 静态文件
└─────────────┘
       ↓
┌─────────────┐
│   Uvicorn   │  ← 多 worker + MySQL
│  (FastAPI)  │
└─────────────┘
       ↓
┌─────────────┐
│    Redis    │  ← Celery Broker
└─────────────┘
       ↓
┌─────────────┐
│ Celery Worker│ ← 异步任务处理
└─────────────┘
       ↓
┌─────────────┐
│    MySQL     │
└─────────────┘
```

---

## 9. 环境变量配置

| 变量 | 说明 | 示例 |
|------|------|------|
| `DATABASE_URL` | 数据库连接 | `mysql://user:pass@host/db` 或 `sqlite:///./legal_saas.db` |
| `REDIS_URL` | Redis 连接 | `redis://localhost:6379/0` |
| `DEEPSEEK_API_KEY` | DeepSeek API 密钥 | `sk-xxxx` |
| `SECRET_KEY` | JWT 签名密钥 | `your-secret-key` |
| `ENVIRONMENT` | 环境 | `development` / `production` |
| `USE_CELERY` | 是否启用 Celery | `true` / `false` |

---

## 10. API 路由结构

```
/api/v1
├── /auth
│   ├── POST /register      # 用户注册
│   ├── POST /login        # 用户登录
│   └── POST /logout       # 登出
├── /workspaces
│   ├── GET /              # 列出工作空间
│   ├── POST /             # 创建工作空间
│   └── DELETE /{id}       # 删除工作空间
├── /contracts
│   ├── GET /              # 列出合同
│   ├── POST /upload       # 上传合同
│   ├── GET /{id}          # 获取合同详情
│   ├── DELETE /{id}       # 删除合同
│   ├── GET /{id}/review   # 获取审查结果
│   ├── GET /{id}/understanding  # 合同理解
│   └── GET /{id}/clause-locations # 条款定位
└── /legal-knowledge
    ├── GET /              # 列出法律知识
    └── POST /             # 添加法律知识
```

---

## 11. 依赖清单

```
fastapi==0.109.0
uvicorn[standard]==0.27.0
pydantic==2.5.3
pydantic-settings==2.1.0
pydantic[email]==2.5.3
sqlalchemy==2.0.25
aiomysql==0.2.0
aiosqlite==0.19.0
redis==5.0.1
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
python-multipart==0.0.6
httpx==0.26.0
tenacity==8.2.3
bcrypt==4.0.1

# 文档解析
pdfplumber>=0.10.0
python-docx>=0.8.11

# 异步任务队列
celery>=5.3.0
```
