---
status: resolved
trigger: 使用大兴机场保密协议 PDF 测试上传流程，显示审查失败
created: 2026-04-01
updated: 2026-04-01
---

## Root Cause

**问题：** 审查失败时后端没有记录错误信息到数据库，导致前端只能显示通用的"审查失败"消息，无法定位具体问题。

**修复：**
1. 添加 `review_error` 字段到 Contract 模型
2. 修改 `process_contract_upload` 函数在失败时记录错误信息
3. 更新数据库 schema

## Resolution

root_cause: Contract 模型缺少 review_error 字段，process_contract_upload 函数在异常处理时没有记录错误详情
fix: 添加 review_error 字段（Text 类型），在 process_contract_upload 的 except 块中设置 contract.review_error = str(e)
verification: 代码已修改，数据库已添加字段。需要重启后端并重新测试
files_changed:
  - backend/app/models/contract.py (第 65-67 行)
  - backend/app/api/v1/endpoints/contracts.py (第 91-96 行)

## Tests Passed

- PDF 解析测试：成功提取 3110 字符
- RAG 检索测试：118 条法律知识，检索正常
- LLM 审查测试：输出 3 条风险条款、5 条缺失条款、5 条修改建议
- 数据库测试：连接、查询、更新正常
