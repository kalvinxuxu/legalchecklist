# Phase 10: 租户个性化风险规则

**目标**: 让每家公司配置自己的风险触发规则，实现"越用越聪明"的个性化审查

**预计工期**: 5 天

---

## 核心策略

**混合审查**: 法律审查（RAG）+ 策略审查（租户规则）

```
上传合同 → 并行执行:
              ├─ 法律审查（RAG + 法律知识库）
              └─ 策略审查（租户自定义规则）
              ↓
         合并结果 → 展示
```

---

## 任务列表

| ID | 任务 | 优先级 | 预估工时 |
|----|------|--------|---------|
| 10.1 | 设计租户规则数据模型 | P0 | 4 小时 |
| 10.2 | 实现规则配置 API (CRUD) | P0 | 6 小时 |
| 10.3 | 实现规则配置前端（三种方式） | P0 | 8 小时 |
| 10.4 | 实现策略审查 LLM 集成 | P0 | 6 小时 |
| 10.5 | 实现反馈学习机制（标记 → 建议创建规则） | P1 | 6 小时 |
| 10.6 | 前端：规则管理界面 | P1 | 6 小时 |
| 10.7 | 端到端集成测试 | P0 | 4 小时 |

---

## 详细需求

### 10.1 租户规则数据模型

```python
class TenantRule(Base):
    """租户自定义风险规则"""
    __tablename__ = "tenant_rules"

    id = Column(UUID, primary_key=True)
    tenant_id = Column(UUID, ForeignKey("tenants.id"), nullable=False)
    name = Column(String(100), nullable=False)  # 规则名称
    description = Column(Text)  # 规则说明

    # 规则配置（JSON 存储，支持多种格式）
    rule_config = Column(JSON, nullable=False)

    # rule_config 格式示例（模板填充）:
    # {
    #   "type": "template",
    #   "clause_type": "payment",  # 条款类型
    #   "field": "ratio",  # 字段
    #   "operator": "<",
    #   "threshold": 30,  # 阈值
    #   "unit": "%"
    # }

    # rule_config 格式示例（条件规则）:
    # {
    #   "type": "condition",
    #   "condition": "payment_percentage < 30"
    # }

    # rule_config 格式示例（自然语言）:
    # {
    #   "type": "natural_language",
    #   "description": "合同中首付款比例不得低于30%",
    #   "parsed": {...}  # AI 解析后的结构
    # }

    risk_level = Column(Enum(RiskLevel), default="medium")
    suggestion = Column(Text)  # 建议文本
    enabled = Column(Boolean, default=True)
    priority = Column(Integer, default=0)

    # 统计
    trigger_count = Column(Integer, default=0)  # 触发次数
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)

class UserRuleFeedback(Base):
    """用户对条款的标记反馈（用于学习）"""
    __tablename__ = "user_rule_feedbacks"

    id = Column(UUID, primary_key=True)
    contract_id = Column(UUID, ForeignKey("contracts.id"))
    clause_hash = Column(String(64))  # 条款内容哈希
    clause_text = Column(Text)
    is_risk = Column(Boolean)  # 是否标记为风险
    created_at = Column(DateTime, default=datetime.utcnow)
```

---

### 10.2 规则配置 API

```
# 规则管理
GET    /api/v1/tenant/rules          # 列出当前租户所有规则
POST   /api/v1/tenant/rules           # 创建规则
GET    /api/v1/tenant/rules/{id}     # 获取规则详情
PUT    /api/v1/tenant/rules/{id}      # 更新规则
DELETE /api/v1/tenant/rules/{id}      # 删除规则
PATCH  /api/v1/tenant/rules/{id}/toggle  # 启用/禁用

# 规则配置方式
POST   /api/v1/tenant/rules/from-template    # 模板填充创建
POST   /api/v1/tenant/rules/from-condition  # 条件规则创建
POST   /api/v1/tenant/rules/from-text       # 自然语言创建

# 反馈
POST   /api/v1/contracts/{id}/clauses/{clause_hash}/feedback  # 标记条款
GET    /api/v1/tenant/rule-suggestions      # 获取建议创建的规则

# 策略开关
GET    /api/v1/tenant/policy-enabled          # 获取策略审查开关状态
PUT    /api/v1/tenant/policy-enabled         # 设置策略审查开关
```

---

### 10.3 规则配置前端

#### 三种配置方式（测试阶段都提供）

**A. 模板填充**
- 选择条款类型（付款、违约、保密、交付、知识产权等）
- 选择字段（金额、比例、期限、违约金比例等）
- 设置阈值和操作符（< > >= <= == contains）
- 示例：条款类型=付款，字段=首付款比例，操作符=<，阈值=30%

**B. 条件规则**
- IF-THEN 格式
- 示例：`IF payment_ratio < 30 THEN high_risk "首付款比例建议不低于30%"`
- 提供语法高亮和验证

**C. 自然语言**
- 文本框输入业务规则描述
- 示例："当合同中首付款比例低于30%时提示风险"
- AI 解析并转换为结构化规则（需用户确认）

#### 规则管理界面
- 规则列表（名称、类型、触发次数、状态）
- 启用/禁用切换
- 编辑、删除操作
- 导入/导出规则（JSON 格式）

---

### 10.4 策略审查 LLM 集成

```python
async def review_with_policy(
    contract_text: str,
    contract_type: str,
    tenant_rules: List[TenantRule],
    legal_review_result: Dict  # 法律审查结果
) -> Dict[str, Any]:
    """
    策略审查

    把租户规则作为 context 传给 LLM 进行判断
    """
    # 构建规则 context
    rules_context = build_rules_context(tenant_rules)

    prompt = f"""
    法律审查结果:
    {legal_review_result}

    公司自定义风险规则:
    {rules_context}

    请根据上述规则，审查合同中是否符合公司政策。
    对于每条公司规则，检查合同对应条款并输出：
    - 规则名称
    - 是否触发（true/false）
    - 如触发，给出建议
    """

    # 调用 LLM
    result = await llm.chat_with_json_output([...])

    return result
```

---

### 10.5 反馈学习机制

**流程**:
1. 用户在审查结果中标记某条款为"风险"（点击风险标签）
2. 系统记录到 `user_rule_feedbacks` 表
3. 当同一类条款（相似哈希）被标记 3 次：
   - 系统生成规则建议
   - 在工作台显示通知："检测到重复风险，建议创建规则"
   - 用户确认后一键创建规则

**触发条件**:
- 同一 `clause_hash` 被标记为风险 3 次
- 条款内容相似度 > 80%

---

### 10.6 前端：规则管理界面

**路由**: `/workspace/settings/rules`

**功能**:
1. 规则列表（表格）
2. 创建规则（三种方式 Tab 切换）
3. 规则详情/编辑
4. 反馈建议列表
5. 策略开关设置

---

## 验收标准

- [ ] 租户可创建、编辑、删除自己的规则
- [ ] 三种配置方式都可用
- [ ] 策略审查与法律审查并行执行
- [ ] 标记 3 次同类条款后提示创建规则
- [ ] 规则严格隔离，仅租户自己可见
- [ ] 策略审查可开启/关闭

---

## 新增文件清单

```
backend/app/models/
├── tenant_rule.py         # 租户规则模型
└── user_rule_feedback.py  # 用户反馈模型

backend/app/services/
├── review/
│   ├── policy.py          # 策略审查服务
│   └── rule_suggestion.py # 规则建议服务
└── llm/
    └── rule_parser.py     # 自然语言规则解析

backend/app/api/v1/endpoints/
├── tenant_rules.py        # 租户规则 API
└── policy.py              # 策略开关 API

frontend/src/views/
├── RulesSettings.vue      # 规则设置页面
└── RuleEditor.vue         # 规则编辑器（三种模式）

frontend/src/components/
├── RuleList.vue           # 规则列表组件
├── TemplateRuleForm.vue    # 模板填充表单
├── ConditionRuleForm.vue   # 条件规则表单
└── NaturalLanguageRuleForm.vue  # 自然语言表单
```

---

## 流程图

```
用户配置规则
       │
       ▼
┌─────────────────┐
│ 1. 模板填充    │
│ 2. 条件规则    │
│ 3. 自然语言    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ 规则存储       │
│ (tenant_rules) │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ 合同审查       │
│ 法律审查(RAG)  │
└────────┬────────┘
         │并行
         ▼
┌─────────────────┐
│ 策略审查       │ ← 租户规则作为 context
│ (LLM 判断)     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ 结果合并展示   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ 用户标记风险   │ → user_rule_feedbacks
└────────┬────────┘
         │
         ▼ (3次同类标记)
┌─────────────────┐
│ 规则建议       │
│ 用户确认 → 创建│
└─────────────────┘
```
