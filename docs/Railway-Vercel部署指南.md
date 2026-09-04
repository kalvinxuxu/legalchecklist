# Vercel + Railway 部署

## Vercel 前端

将项目根目录设置为 `frontend`，构建命令为 `npm run build`，输出目录为 `dist`。

配置环境变量：

```text
VITE_API_BASE_URL=https://<Railway API 域名>/api/v1
```

`VITE_API_BASE_URL` 必须包含 `/api/v1`。

## Railway API

创建 Railway Service，Root Directory 设置为 `backend`。Railway 会读取
`backend/railway.toml`，使用 `Dockerfile` 启动 FastAPI。

至少配置：

```text
DATABASE_TYPE=postgresql
DATABASE_URL=<Railway PostgreSQL 提供的连接串>
JWT_SECRET=<随机长字符串>
DEEPSEEK_API_KEY=<DeepSeek Key>
ZHIPU_EMBEDDING_API_KEY=<智谱 Embedding Key>
ENVIRONMENT=production
STORAGE_PATH=/app/data/uploads
CORS_ORIGINS=["https://<你的 Vercel 域名>"]
```

给 API 服务挂载 Railway Volume 到 `/app/data`，用于合同文件和 Chroma 数据。

## Railway review Worker

当前 MVP 先使用一个 Railway Service，同时运行 API 和 Worker。`backend/railway.toml`
会调用 `start-railway.sh`，它启动 `review_worker.py` 和 Uvicorn。这样两者可以共享
`/app/data` Volume，避免本地合同文件在两个 Service 之间不可见。

API 只创建 `ReviewRun`，Worker 执行合同解析、RAG、LLM 审查和报告生成。未来需要水平
扩展时，应先将合同文件迁移到 S3/R2/OSS，再将 Worker 拆成独立 Service。

## 验证

```text
GET https://<Railway API 域名>/health
```

注册并上传合同后，确认 API 日志出现 `queued`，Worker 日志出现 `Starting review run`。
# Railway + Vercel 部署指南

Railway 环境建议设置 `DOCUMENT_AST_ENABLED=true`、`RAG_HYBRID_ENABLED=true`、`VECTOR_STORE=pgvector`、`RAG_FTS_LANGUAGE=simple` 和 `RAG_P95_LATENCY_MS=1200`。PostgreSQL 部署后依次执行 `backend/migrations/001_hybrid_fts.sql` 和 `backend/migrations/002_pgvector_contract_chunks.sql`，再运行 provenance backfill 脚本。

## 生产发布检查清单

- [ ] Railway PostgreSQL 已启用 `vector` extension，并执行两份 migration。
- [ ] 已运行 `python backend/scripts/migrate_chroma_to_pgvector.py --apply`，并保留迁移前备份。
- [ ] 已完成法律知识和合同 chunk embedding backfill，检查 `embedding_model` 与维度。
- [ ] `VECTOR_STORE=pgvector`；只有迁移验证完成后才允许移除 Chroma Volume。
- [ ] Embedding/pgvector 暂时不可用时，审查结果必须显示 `bm25_rerank`/`contract_bm25_rerank`，不得显示 hybrid。
- [ ] 审查结果的 contract chunk 均属于 `DocumentRecord.current_version_id`。
- [ ] 已检查 `retrieval_diagnostics`、worker heartbeat、失败重试和 pgvector 查询延迟。
- [x] Docling 复杂版式验收已通过：`python -m pytest backend/tests/integration/test_docling_acceptance.py -q`；生产环境仍建议保持 `DOCLING_ENABLED=false`，直到完成线上资源评估和原生 Docling AST 映射。

## 合同 Chunking 升级

合同 chunk 现按章节层级优先、句子/子条款次之、token hard limit 兜底切分；默认目标 700 tokens、上限 1200 tokens，并保存 `section_id`、`section_path`、`parent_chunk_id`、`span_ids` 和字符范围。升级数据库时需额外执行 `backend/migrations/003_structure_chunk_metadata.sql`。

语义边界切分默认关闭；本地验证通过后可设置 `RAG_SEMANTIC_CHUNKING_ENABLED=true`，并通过已有 embedding provider 注入语义边界计算。合同章节边界始终优先于语义边界。

当检索命中 child chunk 时，审查上下文会自动追加不超过 6000 字符的 parent 条款；LLM 仍只能使用 child 的 `source_id` 作为 evidence 来源，parent 仅作为完整语义上下文。
