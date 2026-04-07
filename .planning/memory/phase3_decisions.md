---
name: Phase 3 技术选型决策
description: Phase 3 RAG 与合同审查核心的技术选型决策记录
type: project
---

## Phase 3 技术选型决策

**决策日期**: 2026-03-31

### 已确认的选型

| 组件 | 选型 | 理由 |
|------|------|------|
| LLM 服务商 | 智谱 AI（GLM-4） | 法律场景表现好，国内可访问 |
| Embedding | 智谱 embedding-2 | 1024 维向量，与 GLM-4 同源 |
| 向量数据库 | MySQL 全文搜索 | MVP 阶段简化方案，避免引入 ES 增加运维成本 |
| 文档解析 | 阿里云文档智能 | 中文支持好，可处理复杂排版 |
| 规则库构建 | LLM 生成 + 人工辅助 | 半自动化构建，兼顾效率和准确性 |

### 待补充的配置

**智谱 AI API Key**: 待用户补充
```env
ZHIPU_API_KEY=<待填写>
ZHIPU_BASE_URL=https://open.bigmodel.cn/api/paas/v4
ZHIPU_MODEL=glm-4
ZHIPU_EMBEDDING_MODEL=embedding-2
```

**阿里云文档智能配置**: 待用户补充
```env
ALIYUN_ACCESS_KEY_ID=<待填写>
ALIYUN_ACCESS_KEY_SECRET=<待填写>
ALIYUN_OSS_BUCKET=<待填写>
ALIYUN_OSS_ENDPOINT=oss-cn-hangzhou.aliyuncs.com
```

### 后续可优化点

1. **向量数据库升级路径**: MVP 验证后，可从 MySQL 全文搜索迁移到 Elasticsearch 8.x 或 PGVector，支持语义相似度检索
2. **文档解析降级方案**: 如阿里云服务成本过高，可降级使用开源库（pdfplumber + python-docx）
