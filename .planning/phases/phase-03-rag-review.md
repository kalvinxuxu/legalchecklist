# Phase 3: RAG 与合同审查核心 - 执行计划

**版本**: 2.1
**创建日期**: 2026-03-31
**更新日期**: 2026-03-31
**状态**: 已完成

---

## 目标

搭建 RAG 知识库，实现 LLM 驱动的合同审查核心功能。

**预计工期**: 8 天

## 技术选型确认

| 组件 | 选型 | 说明 |
|------|------|------|
| LLM | 智谱 GLM-4 | 法律场景表现好 |
| Embedding | 智谱 embedding-2 | 1024 维向量 |
| 向量检索 | MySQL 全文搜索 | MVP 阶段简化方案 |
| 文档解析 | 阿里云文档智能 | 中文支持好 |
| 规则库构建 | LLM 生成 + 人工辅助 | 半自动化构建 |

---

## 完成情况

**完成日期**: 2026-03-31
**完成状态**: 95% 完成

### 已完成任务

- [x] Task 3.1: 配置智谱 AI API 密钥
- [x] Task 3.2: 接入智谱 Embedding API
- [x] Task 3.3: 接入阿里云文档智能
- [x] Task 3.4: 实现合同上传 API
- [x] Task 3.5: 实现 RAG 检索服务（MySQL 版）
- [x] Task 3.6: 接入智谱 GLM-4 API
- [x] Task 3.7: LLM 生成审查规则库（NDA）
- [x] Task 3.8: LLM 生成审查规则库（劳动合同）
- [x] Task 3.9: 实现审查 Prompt 模板
- [x] Task 3.10: 实现审查报告生成
- [x] Task 3.11: 实现置信度评分

### 待测试任务

- [ ] 端到端测试（需要智谱 API Key）
- [ ] 文档解析测试（需要阿里云配置）
- [ ] 法律知识库初始化

### Task 3.1: 配置智谱 AI API 密钥

**优先级**: P0
**预估工时**: 30 分钟

**文件**: `backend/.env` 和 `backend/app/core/config.py`

**配置项**:
```env
ZHIPU_API_KEY=your_api_key_here
ZHIPU_BASE_URL=https://open.bigmodel.cn/api/paas/v4
ZHIPU_MODEL=glm-4
ZHIPU_EMBEDDING_MODEL=embedding-2
```

**验收标准**:
- [ ] API Key 配置完成
- [ ] 配置文件支持智谱 AI 所有端点

---

### Task 3.2: 接入智谱 Embedding API

**优先级**: P0
**预估工时**: 2 小时

**文件**: `backend/app/services/rag/embedder.py`

```python
class ZhipuEmbedder:
    def __init__(self):
        self.api_key = settings.ZHIPU_API_KEY
        self.url = "https://open.bigmodel.cn/api/paas/v4/embeddings"
        self.model = "embedding-2"  # 1024 维向量

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

### Task 3.3: 接入阿里云文档智能

**优先级**: P0
**预估工时**: 4 小时

**文件**: `backend/app/services/document/parser.py`

**服务**: 阿里云文档智能（Document Mind）
- PDF 解析
- Word 解析
- 表格识别
- OCR（如需要）

**配置项**:
```env
ALIYUN_ACCESS_KEY_ID=your_key
ALIYUN_ACCESS_KEY_SECRET=your_secret
ALIYUN_OSS_BUCKET=your-bucket
ALIYUN_OSS_ENDPOINT=oss-cn-hangzhou.aliyuncs.com
```

**验收标准**:
- [ ] PDF 文件可解析为文本
- [ ] Word 文件可解析为文本
- [ ] 保留基本格式（标题、段落）

---

### Task 3.4: 实现合同上传 API

**优先级**: P0
**预估工时**: 4 小时

**文件**: `backend/app/api/v1/endpoints/contracts.py`

**接口**:
| 方法 | 路径 | 描述 |
|------|------|------|
| POST | `/api/v1/contracts/upload` | 上传合同文件 |
| GET | `/api/v1/contracts/` | 获取合同列表 |
| GET | `/api/v1/contracts/{id}` | 获取合同详情 |
| DELETE | `/api/v1/contracts/{id}` | 删除合同 |

**流程**:
1. 接收文件上传
2. 上传到阿里云 OSS
3. 创建合同记录
4. 异步触发解析任务

**验收标准**:
- [ ] 支持 PDF 和 Word 文件
- [ ] 文件大小限制（最大 10MB）
- [ ] 文件哈希去重

---

### Task 3.5: 实现 RAG 检索服务（MySQL 版）

**优先级**: P0
**预估工时**: 4 小时

**文件**: `backend/app/services/rag/retriever.py`

**方案**: 使用 MySQL 全文搜索（MVP 简化方案）

```sql
-- 为 legal_knowledge 表添加全文索引
ALTER TABLE legal_knowledge
ADD FULLTEXT INDEX ft_title_content (title, content)
WITH PARSER ngram;
```

**功能**:
1. 关键词检索
2. 租户隔离过滤
3. 结果按相关性排序

**验收标准**:
- [ ] 检索返回相关法条
- [ ] 公共知识库 + 私有库混合检索
- [ ] 响应时间 < 500ms

---

### Task 3.6: 接入智谱 GLM-4 API

**优先级**: P0
**预估工时**: 2 小时

**文件**: `backend/app/services/llm/client.py`

```python
class ZhipuLLMClient:
    def __init__(self):
        self.api_key = settings.ZHIPU_API_KEY
        self.base_url = "https://open.bigmodel.cn/api/paas/v4"
        self.model = "glm-4"

    async def chat_with_json_output(self, messages, temperature=0.3):
        # 调用智谱 GLM-4 API
        # 返回 JSON 格式响应
```

**验收标准**:
- [ ] API 调用成功
- [ ] 响应格式正确（JSON）
- [ ] 异常处理完善

---

### Task 3.7: LLM 生成审查规则库（NDA）

**优先级**: P0
**预估工时**: 4 小时

**文件**: `backend/app/services/review/rules/nda.py`

**方法**: 使用 LLM 从法律法规中提取审查点

**Prompt 示例**:
```
请根据以下《民法典》相关法条，生成 NDA 合同审查规则：

【输入法条】
《民法典》第 470 条：合同的内容由当事人约定...
《民法典》第 577 条：当事人一方不履行合同义务...

【输出格式】
审查点名称 | 风险类型 | 依据法条 | 检查方法 | 风险等级
```

**输出示例**:
```python
NDA_REVIEW_RULES = [
    {
        "id": "nda_001",
        "name": "保密信息范围定义",
        "risk_type": "missing_clause",
        "legal_basis": "《民法典》第 470 条",
        "check_prompt": "检查合同是否明确定义了保密信息的具体范围",
        "risk_level": "high"
    },
    # ... 20+ 审查点
]
```

**验收标准**:
- [ ] 规则库包含 20+ 审查点
- [ ] 每个审查点有明确法条依据
- [ ] 可通过 LLM 动态生成

---

### Task 3.8: LLM 生成审查规则库（劳动合同）

**优先级**: P0
**预估工时**: 4 小时

**文件**: `backend/app/services/review/rules/labor.py`

**审查点清单** (20+ 项):
- 劳动合同期限
- 工作内容和工作地点
- 工作时间和休息休假
- 劳动报酬
- 社会保险
- 试用期规定
- 竞业限制条款
- 违约金条款

**验收标准**:
- [ ] 规则库包含 20+ 审查点
- [ ] 每个审查点有明确法条依据
- [ ] 风险等级定义清晰

---

### Task 3.9: 实现审查 Prompt 模板

**优先级**: P0
**预估工时**: 4 小时

**文件**: `backend/app/services/review/prompts.py`

**Prompt 模板结构**:
```python
REVIEW_PROMPT = """
你是一位专业律师，请审查以下{contract_type}合同。

【参考法律依据】
{context}

【合同内容】
{contract_text}

【输出要求】
请以 JSON 格式输出审查报告：
1. missing_clauses: 缺失条款列表
2. risk_clauses: 风险条款列表
3. suggestions: 修改建议列表
4. legal_references: 引用法条列表
"""
```

**验收标准**:
- [ ] Prompt 结构清晰
- [ ] LLM 输出格式稳定
- [ ] 法条引用准确

---

### Task 3.10: 实现审查报告生成

**优先级**: P0
**预估工时**: 4 小时

**文件**: `backend/app/services/review/generator.py`

**审查报告格式**:
```json
{
  "contract_id": "uuid",
  "contract_type": "NDA",
  "review_status": "completed",
  "risk_level": "medium",
  "confidence_score": 0.85,
  "missing_clauses": [...],
  "risk_clauses": [...],
  "suggestions": [...],
  "legal_references": [...]
}
```

**验收标准**:
- [ ] 报告格式符合 JSON Schema
- [ ] 所有字段完整
- [ ] 法条引用准确

---

### Task 3.11: 实现置信度评分

**优先级**: P1
**预估工时**: 2 小时

**评分逻辑**:
- 基于检索结果数量和质量
- 基于 LLM 响应完整性
- 基于规则匹配度

**验收标准**:
- [ ] 置信度评分合理
- [ ] 低质量结果对应低置信度

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
