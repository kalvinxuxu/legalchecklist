# PostgreSQL + pgvector RAG 迁移方案

## 迁移概述

**目标**：将 RAG 检索从 SQL LIKE 模糊搜索升级为向量语义检索

**核心变更**：
1. 数据库：SQLite → PostgreSQL + pgvector
2. 存储：新增 `embedding` 向量列
3. 检索：LIKE 模糊搜索 → 余弦相似度向量检索

---

## 迁移步骤

### Step 1: 修改配置 (`app/core/config.py`)

新增 PostgreSQL 数据库配置支持：

```python
# PostgreSQL + pgvector
DATABASE_TYPE=postgresql
DATABASE_URL=postgresql://user:password@localhost:5432/legal_saas
EMBEDDING_DIMENSION=1536  # deepseek-embedding 维度
```

### Step 2: 修改模型 (`app/models/legal_knowledge.py`)

新增向量列：

```python
from pgvector.sqlalchemy import Vector

class LegalKnowledge(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "legal_knowledge"

    # ... existing columns ...
    embedding = Column(Vector(1536), nullable=True)  # 新增：1536维向量

    __table_args__ = (
        Index("idx_embedding", "embedding", postgresql_using="hnsw",
              postgresql_ops={"embedding": "vector_cosine_ops"}),
    )
```

### Step 3: 重写检索器 (`app/services/rag/retriever.py`)

向量检索逻辑：

```python
async def retrieve(self, query: str, top_k: int = 5, tenant_id: str = None):
    # 1. 将查询文本向量化
    query_vector = await embedder.embed(query)

    # 2. 向量相似度检索
    sql = """
        SELECT id, title, content, content_type, metadata_json, tenant_id,
               1 - (embedding <=> :query_vector) AS similarity
        FROM legal_knowledge
        WHERE tenant_id IS NULL OR tenant_id = :tenant_id
        ORDER BY embedding <=> :query_vector
        LIMIT :limit
    """
```

### Step 4: 数据迁移

#### 4.1 启用 pgvector 扩展

```sql
CREATE EXTENSION IF NOT EXISTS vector;

-- 启用 HNSW 索引（比 IVFFlat 更快）
CREATE EXTENSION IF NOT EXISTS pgvector;
ALTER EXTENSION pgvector UPDATE;
```

#### 4.2 添加向量列

```sql
ALTER TABLE legal_knowledge ADD COLUMN embedding vector(1536);
```

#### 4.3 创建 HNSW 索引

```sql
CREATE INDEX ON legal_knowledge USING hnsw (embedding vector_cosine_ops)
WITH (m = 16, ef_construction = 64);
```

#### 4.4 批量向量化历史数据

```python
# scripts/backfill_embeddings.py
async def backfill_embeddings(batch_size: int = 32):
    """批量为历史法律知识生成向量"""
    records = await get_all_knowledge_without_embedding()
    for i in range(0, len(records), batch_size):
        batch = records[i:i+batch_size]
        texts = [f"{r.title} {r.content}" for r in batch]
        vectors = await embedder.embed_batch(texts)
        await update_embeddings(list(zip([r.id for r in batch], vectors)))
```

---

## 依赖清单

```txt
# requirements.txt 新增
psycopg2-binary==2.9.9        # PostgreSQL 驱动（同步，用于 Celery）
asyncpg==0.29.0               # PostgreSQL 异步驱动（SQLAlchemy asyncio）
pgvector==0.2.4              # 向量支持
```

---

## 环境变量配置

```env
# .env
DATABASE_TYPE=postgresql
DATABASE_URL=postgresql://postgres:password@localhost:5432/legal_saas

# pgvector 配置
EMBEDDING_DIMENSION=1536
```

---

## 性能对比

| 指标 | SQLite LIKE | pgvector |
|------|-------------|----------|
| 10K 向量检索延迟 | ~200ms | ~5ms |
| 100K 向量检索延迟 | ~2000ms | ~15ms |
| 语义理解能力 | ❌ | ✅ |
| 混合检索 | ❌ | ✅ |

---

## 风险与回滚

### 风险
1. 历史数据向量化需要调用 DeepSeek API（成本考虑）
2. 迁移过程中服务短暂不可用

### 回滚方案
1. 保留 LIKE 搜索作为 fallback
2. 迁移前备份 SQLite 数据库
3. 分批次迁移，先迁移公共库

---

## 实施时间线

| 阶段 | 任务 | 预计时间 |
|------|------|----------|
| 1 | 安装 PostgreSQL + pgvector | 1h |
| 2 | 修改配置和模型 | 1h |
| 3 | 重写检索器 | 2h |
| 4 | 数据迁移脚本 | 1h |
| 5 | 历史数据向量化 | 2h |
| 6 | 测试验证 | 1h |
| **总计** | | **8h** |
