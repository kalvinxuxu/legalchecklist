---
status: awaiting_human_verify
trigger: "上传 PDF 合同后审查失败，浏览器控制台显示 422 Unprocessable Entity 错误"
created: 2026-04-01T00:00:00
updated: 2026-04-01T00:15:00
---

## Current Focus

hypothesis: 修复已完成，等待用户验证
test: 用户重启后端并测试前端功能
expecting: GET /contracts/ 不再返回 422 错误，合同列表能正常加载
next_action: 等待用户确认修复是否有效

## Symptoms

expected: 上传 PDF 合同后应该能正常审查合同
actual: 上传成功但审查失败，返回 422 Unprocessable Entity
errors:
  - POST /api/v1/contracts/ returns 422
  - GET /api/v1/contracts/ returns 422 (加载合同列表失败)
  - 401 Unauthorized on /api/v1/auth/login (可能是 token 过期)
reproduction: 通过页面上传按钮选择文件上传
started: 功能从未正常工作过
file_type: PDF 文档

## Eliminated

## Evidence

- timestamp: 2026-04-01T00:00:00
  checked: 前端 contracts.js 和后端 contracts.py 字段名对比
  found: 字段名匹配 (workspace_id, contract_type)
  implication: 字段名不是问题根源，需要进一步调查
- timestamp: 2026-04-01T00:00:00
  checked: 后端 GET /contracts/ 端点定义 (第 196-218 行)
  found: list_contracts 需要 workspace_id 作为必需查询参数
  implication: 前端 getList() 没有传 workspace_id 参数，导致 422
- timestamp: 2026-04-01T00:00:00
  checked: 前端 Contracts.vue 和 Dashboard.vue
  found: 两处调用 contractsApi.getList() 都没有传 workspace_id
  implication: 前端设计假设获取当前租户下所有合同，不需要指定工作区
- timestamp: 2026-04-01T00:00:00
  checked: 后端查询逻辑 (第 205-212 行)
  found: 查询通过 current_user.tenant_id 过滤工作区，再获取合同
  implication: workspace_id 参数是多余的，后端可以从 current_user 获取租户信息
- timestamp: 2026-04-01T00:10:00
  checked: 后端模块导入测试
  found: contracts.py 和 review_service 都能正常导入
  implication: 代码语法正确，依赖完整
- timestamp: 2026-04-01T00:10:00
  checked: POST /contracts/upload 端点
  found: 字段名匹配，逻辑正确
  implication: 上传端点本身没问题，422 可能来自 GET 端点连锁反应

## Resolution

root_cause: 后端 list_contracts 端点要求 workspace_id 作为必需查询参数，但前端设计是获取当前租户下所有合同，没有传这个参数，导致 FastAPI 返回 422 验证错误
fix: 移除后端 list_contracts 的 workspace_id 参数，直接从 current_user.tenant_id 获取租户信息
verification: 代码语法验证通过，模块导入测试通过。需要用户重启后端并测试前端功能
files_changed:
  - backend/app/api/v1/endpoints/contracts.py (第 196-215 行)
