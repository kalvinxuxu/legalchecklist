# 法务 AI SaaS 平台

> 面向中小企业的轻量化合同审查工具

---

## 快速开始

### 1. 环境准备

- Docker & Docker Compose
- Python 3.11 (本地开发)

### 2. 配置环境变量

```bash
cd backend
cp .env.example .env
# 编辑 .env，填入你的 DeepSeek API Key
```

## 当前生产部署

- 前端：Vercel
- API：Railway，服务根目录设置为 `backend`
- 审查 Worker：Railway API 服务内由 `start-railway.sh` 同时启动
- 数据库：Railway PostgreSQL
- 文件/Chroma：Railway Volume 挂载到 `/app/data`

Vercel 环境变量：

```text
VITE_API_BASE_URL=https://<railway-api-domain>/api/v1
```

生产向量存储使用 PostgreSQL + pgvector；Chroma 仅保留为兼容回退。首次部署 PostgreSQL 后执行 `backend/migrations/001_hybrid_fts.sql` 和 `backend/migrations/002_pgvector_contract_chunks.sql`。
Chunk 和 Embedding 参数见 `docs/Chunk与Embedding模型说明.md`。

Railway API 服务使用 `backend/railway.toml`，并由 `start-railway.sh` 启动 API 与 Worker。
两者共享同一个服务和 `/app/data` Volume。不要在生产环境设置 `USE_CELERY`；审查由
`review_worker.py` 消费 PostgreSQL 中的 ReviewRun。当前方案适合 MVP；未来横向扩展前，
应把合同文件迁移到 S3/R2/OSS，再拆分 Worker 服务。

### 3. 启动服务

```bash
cd docker
docker compose up -d
```

### 4. 验证服务

```bash
# 检查服务状态
docker compose ps

# 查看日志
docker compose logs -f app

# 测试 API
curl http://localhost/health
```

---

## 项目结构

```
legal-ai-saas/
├── backend/                 # FastAPI 后端
│   ├── app/
│   │   ├── api/            # API 路由
│   │   ├── core/           # 核心配置
│   │   ├── db/             # 数据库
│   │   ├── models/         # 数据模型
│   │   ├── schemas/        # Pydantic 模型
│   │   └── services/       # 业务服务
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/               # Vue 3 前端 (待开发)
├── miniprogram/           # 微信小程序 (待开发)
├── docker/
│   ├── docker-compose.yml
│   ├── nginx.conf
│   └── init.sql
└── docs/                  # 文档
```

---

## API 文档

启动服务后访问：http://localhost/docs

### 主要接口

| 接口 | 方法 | 描述 |
|------|------|------|
| `/api/v1/auth/register` | POST | 用户注册 |
| `/api/v1/auth/login` | POST | 用户登录 |
| `/api/v1/auth/me` | GET | 获取当前用户 |
| `/api/v1/workspaces/` | GET | 获取工作区列表 |
| `/api/v1/workspaces/` | POST | 创建工作区 |
| `/api/v1/contracts/upload` | POST | 上传合同 |
| `/api/v1/contracts/` | GET | 获取合同列表 |

---

## 技术栈

| 层级 | 技术 |
|------|------|
| **后端** | FastAPI (Python) |
| **数据库** | MySQL 8.0 |
| **缓存** | Redis |
| **LLM** | DeepSeek API |
| **部署** | Docker Compose |

---

## 下一步

1. **完善后端功能**
   - [ ] 合同审查接口
   - [ ] PDF/Word 解析
   - [ ] 法律知识库填充

2. **前端开发**
   - [ ] Vue 3 项目搭建
   - [ ] 登录/注册页面
   - [ ] 合同上传组件
   - [ ] 审查报告展示

3. **测试与部署**
   - [ ] 单元测试
   - [ ] 生产环境配置
   - [ ] 域名备案

---

## License

MIT
# Legal RAG reranker

Retrieval uses parallel BM25/vector recall, RRF, then a cross-encoder reranker and deterministic legal-source policy. Set `RAG_RERANKER_PROVIDER=bge_local` and `RAG_RERANKER_MODEL=BAAI/bge-reranker-v2-m3` for local/Railway model inference, or set `RAG_RERANKER_PROVIDER=jina` with `JINA_API_KEY` for hosted inference. If the model/provider is unavailable, results are labeled `deterministic_fallback` with a `fallback_reason`.
