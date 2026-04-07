# Phase 10.1: Word 文档辅助编辑（风险审查 + 修订模式）

## 目标

当用户上传 Word (.docx) 文档时，提供风险审查界面，AI 生成修改建议，用户采纳后生成带**修订模式（Track Changes）**的 Word 文档，实现 AI 辅助高效修改。

## 验收标准

1. 用户上传 Word 文档后，可进入「风险审查」界面
2. AI 识别风险条款并展示修改建议
3. 用户可逐条采纳/拒绝建议
4. 采纳后的文档以**修订模式**保存，保留原文 + 修订痕迹
5. 用户可下载修订后的 Word 文档

---

## 任务拆解

### 10.1.1 后端：Word 解析增强

| ID | 任务 | 优先级 | 说明 |
|----|------|--------|------|
| 10.1.1.1 | 增强 `document/parser.py` 支持段落级别解析 | P0 | 返回每个段落的 text + index，支持精确定位 |
| 10.1.1.2 | 实现段落位置索引服务 `document/paragraph_indexer.py` | P0 | 建立段落文本 → docx paragraph 对象的映射 |
| 10.1.1.3 | 新增 `/api/v1/contracts/{id}/word-paragraphs` API | P0 | 返回带索引的段落列表供前端渲染 |

### 10.1.1.4 后端：修订模式 Word 生成

| ID | 任务 | 优先级 | 说明 |
|----|------|--------|------|
| 10.1.1.5 | 实现 `services/word/revision_doc.py` - Track Changes 写入 | P0 | 使用 python-docx 库的修订 API（`paragraph.insert_paragraph_before` + `revisionformat`） |
| 10.1.1.6 | 实现 `services/word/suggestion_engine.py` - 建议生成器 | P0 | 调用 LLM 生成风险条款的修改建议文本 |
| 10.1.1.7 | 新增 `/api/v1/contracts/{id}/apply-suggestions` API | P0 | 接收采纳的建议列表，生成修订后 Word |
| 10.1.1.8 | 新增 `/api/v1/contracts/{id}/revised-word` API | P0 | 下载修订后的 Word 文件流 |

### 10.1.1.9 前端：风险审查界面

| ID | 任务 | 优先级 | 说明 |
|----|------|--------|------|
| 10.1.1.10 | 新增 `ReviewWord.vue` 页面（风险审查视图） | P0 | 左侧原文 + 右侧建议面板，类比 Review.vue |
| 10.1.1.11 | 实现「建议卡片」组件 - 显示修改前后对比 | P0 | `components/WordSuggestionCard.vue` |
| 10.1.1.12 | 实现「一键采纳」功能 - 接受所有建议 | P1 | 批量采纳后生成修订文档 |
| 10.1.1.13 | 实现「下载修订文档」按钮 | P0 | 调用 revised-word API 下载 |
| 10.1.1.14 | 路由配置 - Word 文件上传后跳转至 ReviewWord | P0 | 更新 `router/index.js` |

---

## 技术方案

### Word 修订模式实现

使用 `python-docx` + `docx-compose` 方案：

```python
from docx import Document
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

def add_revision_insert(paragraph, new_text):
    """插入文本（修订模式 - 新增）"""
    run = paragraph.add_run(new_text)
    run.revision_format = 'insert'  # 标记为插入

def add_revision_delete(paragraph, old_text):
    """删除文本（修订模式 - 删除）"""
    run = paragraph.add_run(old_text)
    run.revision_format = 'delete'  # 标记为删除
```

> **注意**：python-docx 原生支持修订，但需确保使用较新版本（>= 0.8.10）。如需更精细控制可使用 `docx-compose` 或直接操作 XML。

### 段落级别定位

Word 解析时记录：
```python
paragraphs = []
for i, para in enumerate(doc.paragraphs):
    paragraphs.append({
        "index": i,
        "text": para.text,
        "style": para.style.name
    })
```

建议采纳时按 index 定位原段落，执行插入/删除。

### 前端界面布局

```
┌─────────────────────────────────────────────────────────┐
│  返回工作台              风险审查 - xxx.docx              │
├─────────────────────────┬─────────────────────────────┤
│  合同原文（段落列表）      │  风险建议                    │
│                         │  ┌─────────────────────────┐ │
│  [1] 鉴于甲方...         │  │ 条款1：高风险            │ │
│  [2] 乙方同意...  ←高亮  │  │ 原文：乙方同意...        │ │
│  [3] 本合同有效期...     │  │ 建议：建议增加违约金条款  │ │
│  ...                    │  │ [采纳] [拒绝] [编辑]     │ │
│                         │  └─────────────────────────┘ │
│                         │  ┌─────────────────────────┐ │
│                         │  │ 条款2：中风险            │ │
│                         │  │ ...                      │ │
│                         │  └─────────────────────────┘ │
├─────────────────────────┴─────────────────────────────┤
│                    [下载修订文档]                        │
└─────────────────────────────────────────────────────────┘
```

---

## 文件清单

### Backend 新增

```
backend/app/services/word/
├── __init__.py
├── parser.py              # Word 段落级解析（增强现有）
├── paragraph_indexer.py    # 段落索引服务
├── revision_doc.py        # 修订模式 Word 生成
└── suggestion_engine.py   # 建议生成（调用 LLM）

backend/app/api/v1/endpoints/contracts.py  # 新增 2 个 API
```

### Frontend 新增

```
frontend/src/views/ReviewWord.vue         # 新页面
frontend/src/components/WordSuggestionCard.vue  # 建议卡片
frontend/src/api/contracts.js             # 新增 API 方法
frontend/src/router/index.js              # 新增路由
```

### 数据库变更

无新增表，复用现有 `contracts` 表的 `content_text` 字段存储段落 JSON。

---

## 依赖安装

```bash
# 后端
pip install python-docx>=0.8.10 docx-compose>=0.4.0
```

---

## 验收检查点

1. ✅ 上传 .docx 文件后，审查页面能展示段落列表
2. ✅ 风险条款能对应到具体段落（高亮定位）
3. ✅ 每条建议有「采纳」「拒绝」「编辑」三个操作
4. ✅ 采纳后下载的 .docx 用 Word 打开，显示修订痕迹
5. ✅ 修订文档可通过 Word 的「接受所有修订」生成最终版
