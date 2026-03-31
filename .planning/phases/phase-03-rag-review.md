# Phase 3: RAG 与合同审查核心 - 执行计划

**版本**: 1.0
**创建日期**: 2026-03-31
**状态**: 待执行

---

## 目标

搭建 RAG 知识库，实现 LLM 驱动的合同审查核心功能。

**预计工期**: 10 天

---

## 任务分解

### Task 3.1: 搭建 Elasticsearch 集群

**优先级**: P0
**预估工时**: 4 小时

**部署方式**: Docker Compose

```yaml
# docker-compose.yml
services:
  elasticsearch:
    image: docker.elastic.co/elasticsearch/elasticsearch:8.11.0
    environment:
      - discovery.type=single-node
      - xpack.security.enabled=true
      - ELASTIC_PASSWORD=${ES_PASSWORD}
    ports:
      - "9200:9200"
    volumes:
      - es_data:/usr/share/elasticsearch/data
    ulimits:
      memlock:
        soft: -1
        hard: -1

volumes:
  es_data:
```

**验收标准**:
- [ ] ES 容器正常启动
- [ ] 可通过 HTTP 访问 ES API
- [ ] 集群状态为 green

---

### Task 3.2: 创建向量索引 mapping

**优先级**: P0
**预估工时**: 2 小时

**索引配置**:

```json
PUT /legal_knowledge
{
  "mappings": {
    "properties": {
      "content": {
        "type": "text",
        "analyzer": "ik_max_word"
      },
      "embedding": {
        "type": "dense_vector",
        "dims": 1024,
        "index": true,
        "similarity": "cosine"
      },
      "content_type": {
        "type": "keyword"
      },
      "tenant_id": {
        "type": "keyword"
      },
      "metadata": {
        "type": "object",
        "properties": {
          "law_number": { "type": "keyword" },
          "effective_date": { "type": "date" },
          "source": { "type": "keyword" }
        }
      }
    }
  }
}
```

**验收标准**:
- [ ] 索引创建成功
- [ ] mapping 配置正确
- [ ] 可写入和查询数据

---

### Task 3.3: 接入智谱 Embedding API

**优先级**: P0
**预估工时**: 2 小时

**文件**: `backend/app/services/rag/embedder.py`

```python
class TextEmbedder:
    def __init__(self):
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

**验收标准**:
- [ ] 可成功调用 Embedding API
- [ ] 返回向量维度为 1024
- [ ] 异常处理完善

---

### Task 3.4: 实现 RAG 检索服务

**优先级**: P0
**预估工时**: 6 小时

**文件**: `backend/app/services/rag/retriever.py`

**功能**:
1. 向量检索
2. 租户隔离过滤
3. 结果合并与排序

**验收标准**:
- [ ] 检索返回相关法条
- [ ] 公共知识库 + 私有库混合检索
- [ ] 响应时间 < 500ms

---

### Task 3.5: 构建 NDA 审查规则库

**优先级**: P0
**预估工时**: 8 小时

**审查点清单** (20+ 项):

| 序号 | 审查点 | 风险类型 | 依据法条 |
|------|--------|---------|---------|
| 1 | 保密信息范围定义是否清晰 | 缺失条款 | 《民法典》470 条 |
| 2 | 保密期限是否合理（≤5 年） | 风险条款 | 《民法典》相关规定 |
| 3 | 违约责任是否明确 | 缺失条款 | 《民法典》577 条 |
| 4 | 违约金是否过高 | 风险条款 | 《民法典》585 条 |
| 5 | 争议解决方式 | 缺失条款 | 《民事诉讼法》 |
| 6 | 保密信息例外情况 | 缺失条款 | 行业惯例 |
| 7 | 返还/销毁条款 | 缺失条款 | 《民法典》 |
| 8 | 知识产权保护 | 风险条款 | 《著作权法》 |
| ... | ... | ... | ... |

**验收标准**:
- [ ] 规则库包含 20+ 审查点
- [ ] 每个审查点有明确法条依据
- [ ] 风险等级定义清晰

---

### Task 3.6: 构建劳动合同审查规则库

**优先级**: P0
**预估工时**: 8 小时

**审查点清单** (20+ 项):

| 序号 | 审查点 | 风险类型 | 依据法条 |
|------|--------|---------|---------|
| 1 | 劳动合同期限 | 缺失条款 | 《劳动合同法》17 条 |
| 2 | 工作内容和工作地点 | 缺失条款 | 《劳动合同法》17 条 |
| 3 | 工作时间和休息休假 | 缺失条款 | 《劳动合同法》17 条 |
| 4 | 劳动报酬 | 缺失条款 | 《劳动合同法》17 条 |
| 5 | 社会保险 | 缺失条款 | 《劳动合同法》17 条 |
| 6 | 试用期规定是否合法 | 风险条款 | 《劳动合同法》19 条 |
| 7 | 竞业限制条款 | 风险条款 | 《劳动合同法》23-24 条 |
| 8 | 违约金条款 | 风险条款 | 《劳动合同法》25 条 |
| ... | ... | ... | ... |

**验收标准**:
- [ ] 规则库包含 20+ 审查点
- [ ] 每个审查点有明确法条依据
- [ ] 风险等级定义清晰

---

### Task 3.7: 接入智谱 GLM-4 API

**优先级**: P0
**预估工时**: 2 小时

**文件**: `backend/app/services/llm/client.py`

```python
class LLMClient:
    def __init__(self):
        self.api_key = os.getenv("ZHIPU_API_KEY")
        self.model = "glm-4"
        self.client = ZhipuAI(api_key=self.api_key)

    async def review_contract(
        self,
        contract_text: str,
        context: List[dict],
        contract_type: str
    ) -> dict:
        prompt = self._build_prompt(contract_text, context, contract_type)
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}]
        )
        return json.loads(response.choices[0].message.content)
```

**验收标准**:
- [ ] API 调用成功
- [ ] 响应格式正确
- [ ] 异常处理完善

---

### Task 3.8: 实现审查 Prompt 模板

**优先级**: P0
**预估工时**: 4 小时

**文件**: `backend/app/services/rag/prompts.py`

**Prompt 模板**:

```
你是一位专业律师，请审查以下{contract_type}合同。

【参考法律依据】
{context}

【合同内容】
{contract_text}

【输出要求】
请以 JSON 格式输出审查报告，包含以下字段：
1. missing_clauses: 缺失条款列表
2. risk_clauses: 风险条款列表（包含风险等级：high/medium/low）
3. suggestions: 修改建议列表
4. legal_references: 引用法条列表（包含法条原文）
5. confidence_score: 置信度评分（0-1）

注意：
- 每条风险条款必须注明具体违反的法条
- 修改建议要具体可操作
- 置信度评分基于检索结果质量
```

**验收标准**:
- [ ] Prompt 结构清晰
- [ ] LLM 输出格式稳定
- [ ] 法条引用准确

---

### Task 3.9: 实现审查报告生成

**优先级**: P0
**预估工时**: 4 小时

**文件**: `backend/app/services/contract_review.py`

**审查报告格式**:

```json
{
  "contract_id": "uuid",
  "contract_type": "NDA",
  "review_status": "completed",
  "risk_level": "medium",
  "confidence_score": 0.85,
  "missing_clauses": [
    {
      "title": "保密信息范围定义",
      "description": "合同未明确定义保密信息的具体范围",
      "legal_reference": "《民法典》第 470 条"
    }
  ],
  "risk_clauses": [
    {
      "clause": "保密期限为永久",
      "risk_level": "medium",
      "reason": "保密期限过长，建议调整为 3-5 年",
      "legal_reference": "《民法典》相关规定"
    }
  ],
  "suggestions": [
    "建议明确保密信息的具体范围",
    "建议将保密期限调整为 3-5 年"
  ],
  "legal_references": [
    {
      "law": "《民法典》第 470 条",
      "content": "合同的内容由当事人约定，一般包括下列条款..."
    }
  ]
}
```

**验收标准**:
- [ ] 报告格式符合 JSON Schema
- [ ] 所有字段完整
- [ ] 法条引用准确

---

### Task 3.10: 实现置信度评分

**优先级**: P1
**预估工时**: 4 小时

**评分逻辑**:

```python
def calculate_confidence(context: List[dict], llm_response: dict) -> float:
    """
    基于以下因素计算置信度：
    1. 检索结果数量和质量
    2. 检索结果相似度
    3. LLM 响应完整性
    """
    if len(context) == 0:
        return 0.3

    # 基于平均相似度
    avg_similarity = sum(item["score"] for item in context) / len(context)

    # 基于响应完整性
    completeness = self._check_completeness(llm_response)

    # 综合评分
    confidence = 0.5 * avg_similarity + 0.5 * completeness
    return min(1.0, confidence)
```

**验收标准**:
- [ ] 置信度评分合理
- [ ] 低质量检索结果对应低置信度
- [ ] 前端可根据置信度展示不同提示

---

### Task 3.11: 实现异步审查任务队列

**优先级**: P1
**预估工时**: 6 小时

**技术栈**: Celery + Redis

**文件**: `backend/app/tasks/review.py`

```python
@celery.task(bind=True)
def review_contract_task(self, contract_id: str):
    """
    异步审查任务
    """
    # 1. 获取合同
    contract = get_contract(contract_id)

    # 2. 更新状态为 processing
    update_status(contract_id, "processing")

    try:
        # 3. 执行审查
        result = await review_service.review(contract)

        # 4. 保存结果
        save_review_result(contract_id, result)
        update_status(contract_id, "completed")
    except Exception as e:
        update_status(contract_id, "failed", error=str(e))
```

**验收标准**:
- [ ] 任务可异步执行
- [ ] 任务状态可查询
- [ ] 异常处理完善

---

## 验收清单

### RAG 验收
- [ ] Elasticsearch 正常运行
- [ ] 向量索引工作正常
- [ ] RAG 检索返回相关法条
- [ ] 检索响应时间 < 500ms

### 审查功能验收
- [ ] NDA 审查功能正常
- [ ] 劳动合同审查功能正常
- [ ] 审查报告格式正确
- [ ] 法条引用准确
- [ ] 单份合同审查时间 < 30 秒

### 质量验收
- [ ] 审查准确率 > 85%（人工抽检 50 份）
- [ ] 置信度评分合理
- [ ] 异步任务队列工作正常

---

## 下一步

Phase 3 完成后，进入 **Phase 4: 前端开发**

主要工作：
1. 搭建 Vue 3 项目框架
2. 实现登录/注册页面
3. 实现合同上传组件
4. 实现审查报告展示页
