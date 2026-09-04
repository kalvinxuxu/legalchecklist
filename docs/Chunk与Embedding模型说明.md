# Chunk 与 Embedding 模型

## Chunk

合同先转换为 `UnifiedDocument`，再按以下顺序切分：

1. 识别标题和条款编号，形成 `section_path`。
2. 普通段落按 block 顺序合并。
3. 表格独立成 chunk，避免与邻近正文混合。
4. 超过最大长度的条款按窗口拆分。
5. chunk 边界保留 overlap，默认最大 1800 字符、重叠 200 字符。

每个 chunk 使用 `version_id + text` 生成稳定 ID，并保留 block、页码和 section provenance。

## Embedding

默认配置：

```text
EMBEDDING_PROVIDER=zhipu
ZHIPU_EMBEDDING_MODEL=embedding-2
EMBEDDING_DIMENSION=1024
EMBEDDING_NORMALIZE=true
```

生产向量存储使用 PostgreSQL + pgvector，HNSW 使用 cosine distance。旧 Chroma 只作为显式兼容回退。

可选本地模型：

```text
EMBEDDING_PROVIDER=local
LOCAL_EMBEDDING_MODEL=BAAI/bge-m3
```

切换模型必须重新生成对应版本的向量，不能把不同模型或不同维度的向量混在同一索引中。

Embedding provider、模型、版本和归一化策略必须与查询向量保持一致；provider 不可用时，系统降级为 BM25，并在检索诊断中标记降级模式。
