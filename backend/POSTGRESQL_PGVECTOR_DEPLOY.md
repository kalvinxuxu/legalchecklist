# PostgreSQL + pgvector 部署指南

## 概述

本文档说明如何将法务 AI SaaS 后端从 SQLite 迁移到 PostgreSQL + pgvector，实现 RAG 向量语义检索。

---

## 部署步骤

### Step 1: 安装 PostgreSQL + pgvector

#### macOS
```bash
# 安装 PostgreSQL
brew install postgresql@15
brew install pgvector

# 启动 PostgreSQL
brew services start postgresql@15
```

#### Ubuntu/Debian
```bash
# 添加 PostgreSQL APT 源
sudo apt install -y postgresql postgresql-contrib

# 安装 pgvector
sudo apt install -y postgresql-15-pgvector

# 启动服务
sudo systemctl start postgresql
sudo systemctl enable postgresql
```

#### Windows
推荐使用 Docker:

```powershell
docker run -d \
  --name postgres-pgvector \
  -e POSTGRES_PASSWORD=your_password \
  -e POSTGRES_DB=legal_saas \
  -p 5432:5432 \
  -v postgres_data:/var/lib/postgresql/data \
  pgvector/pgvector:pg16
```

#### 阿里云 RDS PostgreSQL（如已使用阿里云）
1. 在阿里云控制台创建 PostgreSQL 14+ 实例
2. 在"插件管理"中启用 `vector` 扩展
3. 获取连接地址和端口

---

### Step 2: 创建数据库

```bash
# 连接到 PostgreSQL
psql -U postgres -h localhost

# 创建数据库
CREATE DATABASE legal_saas;

# 连接到新数据库
\c legal_saas

# 启用 pgvector
CREATE EXTENSION IF NOT EXISTS vector;

# 验证
SELECT extversion FROM pg_extension WHERE extname = 'vector';
```

---

### Step 3: 配置环境变量

复制配置示例文件：

```bash
cp .env.postgresql.example .env
```

编辑 `.env`:

```env
# 数据库配置
DATABASE_TYPE=postgresql
DATABASE_URL=postgresql://postgres:your_password@localhost:5432/legal_saas

# 向量维度（DeepSeek embedding = 1536）
EMBEDDING_DIMENSION=1536
```

---

### Step 4: 安装 Python 依赖

```bash
cd backend

# 激活虚拟环境
.\venv\Scripts\activate  # Windows
# 或
source venv/bin/activate  # macOS/Linux

# 安装新依赖
pip install -r requirements.txt
```

---

### Step 5: 运行 SQL 迁移脚本

```bash
psql -U postgres -d legal_saas -f scripts/migrate_add_pgvector.sql
```

此脚本会：
1. 启用 `vector` 扩展
2. 添加 `embedding` 列（1536维）
3. 创建 HNSW 向量索引

---

### Step 6: 启动后端服务

```bash
# 确保数据库连接正常
python -c "from app.db.session import db; db.connect(); print('DB OK')"

# 启动后端
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8001
```

---

### Step 7: 迁移历史数据（可选）

如果已有法律知识数据，需要为历史记录生成向量：

```bash
# 检查向量化状态
python scripts/backfill_embeddings.py --status

# 批量向量化（建议在业务低峰期执行）
python scripts/backfill_embeddings.py --batch-size 16
```

---

## 验证部署

### 1. API 健康检查

```bash
curl http://localhost:8001/health
```

### 2. 向量检索测试

```python
import requests

response = requests.post(
    "http://localhost:8001/api/v1/contracts/upload",
    files={"file": open("test_contract.pdf", "rb")},
    data={"workspace_id": "your-workspace-id", "contract_type": "NDA"},
    headers={"Authorization": "Bearer YOUR_TOKEN"}
)
print(response.json())
```

### 3. 检查向量是否正确存储

```sql
SELECT id, title, embedding::text
FROM legal_knowledge
WHERE embedding IS NOT NULL
LIMIT 5;
```

---

## 性能优化

### HNSW 索引参数调优

```sql
-- 更快的搜索（但索引更大）
CREATE INDEX idx_embedding_fast
ON legal_knowledge USING hnsw (embedding vector_cosine_ops)
WITH (m = 32, ef = 128);

-- 更快构建（但搜索稍慢）
CREATE INDEX idx_embedding_small
ON legal_knowledge USING hnsw (embedding vector_cosine_ops)
WITH (m = 8, ef = 32);
```

### 连接池配置

在 `app/db/session.py` 中可根据并发量调整：

```python
pool_size=20,      # 常规连接数
max_overflow=40,   # 额外连接数
```

---

## 监控与告警

### 关键指标

| 指标 | 正常值 | 告警阈值 |
|------|--------|----------|
| 向量检索延迟 | < 50ms | > 200ms |
| 连接池使用率 | < 70% | > 90% |
| 向量化任务队列 | < 100 | > 1000 |

### 日志查询

```sql
-- 查看慢查询
SELECT query, calls, mean_time
FROM pg_stat_statements
WHERE query LIKE '%legal_knowledge%'
ORDER BY mean_time DESC
LIMIT 10;
```

---

## 故障排查

### 问题 1: `pgvector` 扩展不存在

```
ERROR: could not open extension control file
```

解决：安装 pgvector 或确认 PostgreSQL 版本 >= 14

```bash
# 检查 PostgreSQL 版本
psql --version

# 如使用 Docker，确认镜像包含 pgvector
docker run -d --name test-pg pgvector/pgvector:pg16
```

### 问题 2: 向量维度不匹配

```
ERROR: vector dimension must be 1536
```

解决：确认 `EMBEDDING_DIMENSION=1536` 与 `embedding vector(1536)` 一致

### 问题 3: 向量检索无结果

检查：
1. 是否有记录包含非空 `embedding` 字段
2. HNSW 索引是否创建成功

```sql
SELECT COUNT(*) FROM legal_knowledge WHERE embedding IS NOT NULL;
SELECT indexname, indexdef FROM pg_indexes WHERE tablename = 'legal_knowledge';
```

---

## 回滚方案

如需回滚到 SQLite：

1. 停止后端服务
2. 修改 `.env`：
   ```env
   DATABASE_TYPE=sqlite
   SQLITE_PATH=./legal_saas_backup.db
   ```
3. 注释掉 `embedding` 相关代码（在 `LegalKnowledge` 模型中）
4. 重启服务

---

## 成本估算

### 自建 PostgreSQL（阿里云 RDS）

| 配置 | 月费用（参考） |
|------|--------------|
| 2核4G SSD | ~500元/月 |
| 4核8G SSD | ~1000元/月 |
| 8核16G SSD | ~2000元/月 |

### Pinecone（云向量库）

| 规模 | 月费用 |
|------|--------|
| 100K 向量 | $70/月 |
| 1M 向量 | $300/月 |

pgvector 成本更低，适合中小规模（< 10M 向量）场景。
