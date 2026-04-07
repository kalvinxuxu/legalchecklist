---
status: awaiting_human_verify
trigger: "审查报告数据为空、导航失效、进度不显示"
created: 2026-04-01T00:00:00Z
updated: 2026-04-01T00:25:00Z
---

## Current Focus

**Awaiting human verification** - 所有三个问题的修复已完成，需要用户验证

已完成的修复：
1. Issue 1: 后端字段转换 - 已完成
2. Issue 2: 导航栏添加 - 已完成
3. Issue 3: 进度文本显示 - 已完成

next_action: 等待用户验证修复效果

## Symptoms

### Issue 1: 审查报告数据为空
expected: 风险条款应显示原文、风险描述；缺失条款应显示建议、建议修改
actual: 风险条款原文字段为空、风险字段为空；缺失条款建议字段为空、建议修改字段为空
errors:
reproduction: 上传合同 -> 审查 -> 查看报告
started: 一直存在

### Issue 2: 导航问题
expected: 可以从审查报告页面退回到工作台、合同列表、上传合同
actual: 无法退回，导航栏缺失或失效
errors:
reproduction: 进入审查报告页面 -> 尝试返回
started: 一直存在

### Issue 3: 进度显示
expected: 审查过程中显示动态进度（如"正在分析第 1/5 条条款"）
actual: 没有进度显示，用户不知道处理状态
errors:
reproduction: 上传合同 -> 点击审查 -> 等待过程
started: 一直存在

## Eliminated

## Evidence

- timestamp: 2026-04-01T00:05:00Z
  checked: Review.vue 前端模板
  found: 前端期望的字段格式：
    - risk_clauses[].original_text (原文)
    - risk_clauses[].risk_description (风险描述)
    - risk_clauses[].suggestion (建议)
    - missing_clauses[].suggestion (建议)
    - missing_clauses[].legal_reference (法条依据)
  implication: 前端字段期望与服务端返回格式可能不匹配

- timestamp: 2026-04-01T00:06:00Z
  checked: backend/app/services/review/service.py
  found: 后端审查服务返回的格式：
    - risk_clauses[].clause (不是 original_text)
    - risk_clauses[].reason (不是 risk_description)
    - missing_clauses[].description (没有 suggestion 字段)
    - missing_clauses[].legal_reference (没有这个字段)
  implication: **字段名称不匹配** - 服务端返回的字段名与前端期望的字段名不一致

- timestamp: 2026-04-01T00:07:00Z
  checked: Review.vue 导航栏
  found:  loading 和 error 状态下有返回合同列表按钮，但 review 状态（审查报告页面）没有导航栏
  implication: 审查报告页面缺少顶部导航栏和返回按钮

- timestamp: 2026-04-01T00:08:00Z
  checked: Review.vue 进度显示逻辑
  found: 进度条使用模拟定时器 startProgress() 每 500ms 增加 2%，直到 90%；轮询间隔 3000ms
  implication: 进度条是假的动画效果，不是真实进度；轮询间隔 3 秒可能造成卡顿感

- timestamp: 2026-04-01T00:10:00Z
  checked: backend/app/api/v1/endpoints/contracts.py
  found: API 端点 `/contracts/{id}/review` 直接返回 contract.review_result，没有做字段名称转换
  implication: 确认 Issue 1 根因：后端返回的字段名与前端期望不一致，导致前端显示为空

## Resolution

root_cause:
**Issue 1 - 数据为空：**
服务端 `service.py` 返回的字段名与前端 `Review.vue` 期望的字段名不匹配：
- 服务端返回 `clause`，前端期望 `original_text`
- 服务端返回 `reason`，前端期望 `risk_description`
- 服务端 `missing_clauses` 没有 `suggestion` 字段，前端期望有
- 服务端 `missing_clauses` 没有 `legal_reference` 字段，前端期望有

**Issue 2 - 导航问题：**
Review.vue 页面在审查完成后（`v-else-if="review"`）没有显示返回按钮，而 loading 和 error 状态都有返回按钮。路由配置正常，问题在于页面组件本身缺少导航元素。

**Issue 3 - 进度显示：**
当前进度条是模拟动画（每 500ms 增加 2% 直到 90%），不是真实进度。后端审查服务没有进度更新机制，前端通过 3 秒轮询检查状态，在审查过程中无法看到真实进度。

fix:
**Issue 1 - 数据为空:**
- 修改 `backend/app/services/review/service.py`:
  1. 更新 `_build_review_prompt` 方法，让 LLM 直接返回正确的字段名
  2. 新增 `_transform_review_result` 方法，将 LLM 返回的字段转换为前端期望的格式
  3. 新增 `_generate_missing_suggestion` 方法，为缺失条款生成默认建议

**Issue 2 - 导航问题:**
- 修改 `frontend/src/views/Review.vue`:
  1. 在页面顶部添加导航栏，包含"返回工作台"按钮和导航链接（工作台、合同列表、上传合同）
  2. 导入 `ArrowLeft` 图标和 `useRouter`

**Issue 3 - 进度显示:**
- 修改 `frontend/src/views/Review.vue`:
  1. 添加 `statusText` 状态变量显示当前处理阶段
  2. 更新 `startProgress` 方法，根据进度百分比显示不同的状态文本（解析文档、检索法规、分析条款、生成报告）
  3. 将静态提示文本改为动态绑定 `statusText`

verification:
需要用户验证：
1. 上传一份 NDA 或劳动合同，查看审查报告
2. 确认风险条款显示原文、风险描述、建议
3. 确认缺失条款显示建议、法条依据
4. 确认可以通过顶部导航栏返回工作台、合同列表、上传合同
5. 确认审查过程中显示动态进度文本

files_changed:
  - backend/app/services/review/service.py
  - frontend/src/views/Review.vue
