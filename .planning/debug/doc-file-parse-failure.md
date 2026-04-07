---
status: resolved
trigger: 上传 DOC 格式文件后审查失败
created: 2026-04-02
updated: 2026-04-02T09:35:00
---

## Root Cause

**问题：** 用户上传的是 `.doc` 格式（老式 Word 二进制文件），但后端解析器 `python-docx` 只能处理 `.docx` 格式（Office 2007+ 的 XML 格式）。

**错误日志：**
```
docx.opc.exceptions.PackageNotFoundError: Package not found at 'C:\Users\kalvi\Documents\claude application\ai saas legal\backend\uploads\...\1553c7f9-e53e-4c39-8ddf-6a2267bd972e.doc'
```

## Resolution

**修复方案：** 前端 + 后端双重验证，只允许上传 `.pdf` 和 `.docx` 格式

**修改内容：**

1. **前端 (Upload.vue 第 36 行):**
   - `accept=".pdf,.doc,.docx"` → `accept=".pdf,.docx"`
   - 提示文案：添加"不支持 .doc 格式"说明

2. **后端 (contracts.py 第 128-138 行):**
   - 新增文件扩展名验证
   - 拒绝 `.doc` 格式，返回清晰的错误提示

**Files changed:**
  - frontend/src/views/Upload.vue (第 36 行，第 43-45 行)
  - backend/app/api/v1/endpoints/contracts.py (第 128-138 行)
