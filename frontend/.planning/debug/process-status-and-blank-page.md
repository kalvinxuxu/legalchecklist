---
status: awaiting_human_verify
trigger: "进度状态不清晰（缺少"理解中"、"审查中"提示）+ 从合同列表返回工作台经常出现空白页面"
created: 2026-04-04T00:00:00
updated: 2026-04-04T00:00:00
---

## Current Focus
next_action: "Awaiting human verification of fixes"

## Symptoms
expected: |
  1. 上传合同时显示"上传中"，完成后显示"上传完成"；理解合同后台运转时显示"理解中"；审查时显示"审查中"
  2. 从合同列表页面点击返回工作台，应该正常显示工作台内容，不出现空白
actual: |
  1. 上传有状态显示，但"理解合同"后台运转时用户不知道进度，审查状态也不够清晰
  2. 从合同列表(/workspace/contracts)返回工作台(/workspace)时经常出现空白页面
errors: 无错误信息，只是状态不清晰/空白
reproduction: |
  1. 上传合同后进入审查页面，等待后台任务完成，但不知道当前是"理解中"还是"审查中"
  2. 进入合同列表后点击左侧菜单"工作台"返回
started: Phase 9 集成后

## Eliminated

## Evidence
- timestamp: 2026-04-04
  checked: "Router configuration (index.js)"
  found: "Dashboard route is at path '' (empty string), which matches /workspace, NOT /workspace/dashboard"
  implication: "handleMenuSelect('dashboard') pushes /workspace/dashboard which doesn't exist"

- timestamp: 2026-04-04
  checked: "Workspace.vue handleMenuSelect function"
  found: "router.push(`/workspace/${index}`) - when index='dashboard', it pushes /workspace/dashboard"
  implication: "This is wrong - /workspace/dashboard has no matching route"

- timestamp: 2026-04-04
  checked: "Backend tasks.py review workflow"
  found: "Understanding runs as background task after review_service.review_contract completes (line 164-171)"
  implication: "Frontend has no way to know understanding phase is running - backend doesn't expose understanding status"

- timestamp: 2026-04-04
  checked: "Review.vue loadReviewResult polling"
  found: "Only checks for pending/processing/completed/failed - no understanding status"
  implication: "Progress bar shows generic messages, doesn't reflect actual stages"

## Resolution
root_cause: |
  1. **Blank page**: handleMenuSelect pushes `/workspace/dashboard` but Dashboard route is at `/workspace` (empty path). The route /workspace/dashboard doesn't exist.
  2. **Status**: Backend runs understanding as background task with no status exposure. Frontend only shows generic progress messages.

fix: |
  1. **Blank page fix**: Changed handleMenuSelect to map 'dashboard' to '/workspace' instead of '/workspace/dashboard'
  2. **Status fix**:
     - Added "正在生成智能理解..." message at 95%+ progress
     - Added checkUnderstandingAvailable() function to poll for understanding data
     - After review completes, if understanding not available, continue showing "理解中" status until available

verification: |
  - Test: From /workspace/contracts, click "工作台" -> should show Dashboard without blank
  - Test: Upload contract, check if "理解中" status shows when review completed but understanding not yet available

files_changed:
  - frontend/src/views/Workspace.vue: Fixed handleMenuSelect to push '/workspace' for dashboard
  - frontend/src/views/Review.vue: Added understanding availability check and "理解中" status display
