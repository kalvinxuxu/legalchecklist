-- PostgreSQL + pgvector 迁移脚本
-- 用途：为 legal_knowledge 表添加向量嵌入列和 HNSW 索引
--
-- 前置条件：
--   1. PostgreSQL 14+
--   2. pgvector 扩展已安装
--
-- 使用方法：
--   psql -U postgres -d legal_saas -f scripts/migrate_add_pgvector.sql

-- ============================================================
-- Step 1: 启用 pgvector 扩展
-- ============================================================
CREATE EXTENSION IF NOT EXISTS vector;

-- 确认版本
SELECT extversion FROM pg_extension WHERE extname = 'vector';

-- ============================================================
-- Step 2: 添加 embedding 列（1536维 = DeepSeek embedding）
-- ============================================================
ALTER TABLE legal_knowledge
ADD COLUMN IF NOT EXISTS embedding vector(1536);

-- ============================================================
-- Step 3: 创建 HNSW 向量索引
-- 注意：HNSW 索引比 IVFFlat 更快，但构建更慢、内存占用更高
-- m=16, ef_construction=64 是常用默认值
-- ============================================================
CREATE INDEX IF NOT EXISTS idx_legal_knowledge_embedding
ON legal_knowledge
USING hnsw (embedding vector_cosine_ops)
WITH (m = 16, ef_construction = 64);

-- ============================================================
-- Step 4: 验证迁移
-- ============================================================
-- 查看表结构
\d+ legal_knowledge

-- 查看索引
SELECT indexname, indexdef
FROM pg_indexes
WHERE tablename = 'legal_knowledge';

-- 查看向量维度
SELECT id, embedding::text
FROM legal_knowledge
WHERE embedding IS NOT NULL
LIMIT 5;

-- ============================================================
-- 回滚脚本（如需回滚）
-- ============================================================
-- DROP INDEX IF EXISTS idx_legal_knowledge_embedding;
-- ALTER TABLE legal_knowledge DROP COLUMN IF EXISTS embedding;
