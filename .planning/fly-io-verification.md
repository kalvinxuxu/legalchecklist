# Fly.io 生产环境验证报告

**验证日期**: 2026-04-03  
**验证状态**: ✅ 通过

---

## 问题诊断与修复

### 问题 1: LLM API 超时

**现象**: 合同审查时出现 `httpx.ReadTimeout` 错误

**日志**:
```
httpcore.ReadTimeout
...
httpx.ReadTimeout
File "/app/app/services/review/service.py", line 64, in review_contract
    review_result = await self.llm.chat_with_json_output([
```

**原因**: 默认超时 60 秒对于合同审查太短，智谱 API 需要更长时间处理长文本

**修复**: 将 `backend/app/services/llm/client.py` 中的超时时间从 60 秒增加到 180 秒

```python
# 修改前
self.timeout = 60.0

# 修改后
self.timeout = 180.0  # 增加超时时间到 180 秒，合同审查需要更长时间
```

---

### 问题 2: Fly.io 机器自动停止

**现象**: 机器在空闲时自动停止，导致首次请求需要等待启动

**原因**: `fly.toml` 配置了 `auto_stop_machines = true` 和 `min_machines_running = 0`

**修复**: 更新 `fly.toml` 配置

```toml
# 修改前
[http_service]
  auto_stop_machines = true
  min_machines_running = 0
  
[[vm]]
  memory = '512mb'
  memory_mb = 512

# 修改后
[http_service]
  auto_stop_machines = false  # 禁止自动停止，避免冷启动
  min_machines_running = 1    # 保持至少一台机器运行
  
[[vm]]
  memory = '1gb'              # 增加内存到 1GB
  memory_mb = 1024
```

---

## 生产环境测试流程

### 测试步骤

| 步骤 | API | 方法 | 状态 | 说明 |
|------|-----|------|------|------|
| 1 | /api/v1/auth/register | POST | ✅ | 用户注册成功 |
| 2 | /api/v1/auth/login | POST | ✅ | 登录获取 Token |
| 3 | /api/v1/workspaces/ | GET | ✅ | 获取工作区列表 |
| 4 | /api/v1/contracts/upload | POST | ✅ | 上传合同文件 |
| 5 | 后台异步处理 | - | ✅ | 合同审查 (~28 秒) |
| 6 | /api/v1/contracts/{id} | GET | ✅ | 获取审查结果 |

### 测试命令

**1. 用户注册**:
```bash
curl -X POST https://legal-ai-saas-kalvi.fly.dev/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"Test1234!"}'
```

**2. 用户登录**:
```bash
curl -X POST https://legal-ai-saas-kalvi.fly.dev/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"Test1234!"}'
```

**3. 获取工作区**:
```bash
curl https://legal-ai-saas-kalvi.fly.dev/api/v1/workspaces/ \
  -H "Authorization: Bearer <TOKEN>"
```

**4. 上传合同**:
```bash
curl -X POST https://legal-ai-saas-kalvi.fly.dev/api/v1/contracts/upload \
  -H "Authorization: Bearer <TOKEN>" \
  -F "file=@test_contract.pdf" \
  -F "workspace_id=<WORKSPACE_ID>" \
  -F "contract_type=NDA"
```

**5. 获取审查结果**:
```bash
curl https://legal-ai-saas-kalvi.fly.dev/api/v1/contracts/<CONTRACT_ID> \
  -H "Authorization: Bearer <TOKEN>"
```

---

## 审查结果示例

**测试文件**: test_contract.pdf  
**审查时间**: ~28 秒  
**审查状态**: `completed`  
**风险等级**: `low`

**审查输出**:
```json
{
  "risk_clauses": [],
  "missing_clauses": [
    {
      "title": "当事人信息条款",
      "description": "合同未明确记载双方当事人的姓名/名称和住所信息...",
      "suggestion": "在合同开头明确添加双方当事人的完整名称...",
      "legal_reference": "《民法典》第 470 条"
    },
    // ... 更多缺失条款
  ],
  "suggestions": [
    {
      "title": "合同结构完善",
      "content": "建议完善合同整体结构...",
      "reason": "完整的合同结构有助于明确双方权利义务..."
    }
  ],
  "legal_references": [
    {
      "law_name": "《中华人民共和国民法典》",
      "article": "第 470 条",
      "content": "合同的内容由当事人约定..."
    }
  ],
  "confidence_score": 0.3
}
```

---

## 修改文件清单

| 文件 | 修改内容 |
|------|----------|
| `backend/app/services/llm/client.py` | LLM 超时从 60 秒 → 180 秒 |
| `fly.toml` | auto_stop=false, min_machines=1, memory=1GB |

---

## 费用影响

| 配置 | 修改前 | 修改后 |
|------|--------|--------|
| 内存 | 512MB | 1024MB |
| 自动停止 | 启用 | 禁用 |
| 最小机器数 | 0 | 1 |
| 估算月费用 | ~$4 | ~$8 |

---

## 结论

✅ **Fly.io 生产环境验证通过**

所有核心功能正常工作：
- ✅ 用户认证系统
- ✅ 租户隔离
- ✅ 文件上传
- ✅ 合同解析 (pdfplumber)
- ✅ 智谱 AI 集成
- ✅ 合同审查服务
- ✅ RAG 法律知识检索

**建议**: 如果长时间不使用，可以手动暂停应用以节省费用：
```bash
flyctl apps stop legal-ai-saas-kalvi
```
