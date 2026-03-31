# Phase 2: 数据库与后端基础 - 执行计划

**版本**: 1.0
**创建日期**: 2026-03-31
**状态**: 待执行

---

## 目标

完成数据库设计和后端基础框架，实现用户认证和租户隔离功能。

**预计工期**: 5 天

---

## 任务分解

### Task 2.1: 设计并创建数据库表结构

**优先级**: P0
**预估工时**: 4 小时

**步骤**:
1. 创建数据库迁移脚本（使用 Alembic）
2. 设计表结构
3. 执行迁移

**核心表结构**:

```sql
-- 租户表
CREATE TABLE tenants (
    id VARCHAR(36) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    plan ENUM('free', 'pro', 'enterprise') DEFAULT 'free',
    wx_appid VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 工作区表
CREATE TABLE workspaces (
    id VARCHAR(36) PRIMARY KEY,
    tenant_id VARCHAR(36) NOT NULL,
    name VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_tenant_id (tenant_id),
    FOREIGN KEY (tenant_id) REFERENCES tenants(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 用户表
CREATE TABLE users (
    id VARCHAR(36) PRIMARY KEY,
    tenant_id VARCHAR(36) NOT NULL,
    email VARCHAR(255) UNIQUE,
    phone VARCHAR(20) UNIQUE,
    wx_openid VARCHAR(100),
    wx_unionid VARCHAR(100),
    password_hash VARCHAR(255),
    role ENUM('admin', 'member') DEFAULT 'member',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_tenant_id (tenant_id),
    FOREIGN KEY (tenant_id) REFERENCES tenants(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 合同表
CREATE TABLE contracts (
    id VARCHAR(36) PRIMARY KEY,
    workspace_id VARCHAR(36) NOT NULL,
    user_id VARCHAR(36) NOT NULL,
    file_name VARCHAR(500),
    file_path VARCHAR(1000),
    file_hash VARCHAR(64),
    contract_type VARCHAR(50),
    review_status ENUM('pending', 'processing', 'completed', 'failed') DEFAULT 'pending',
    review_result JSON,
    risk_level ENUM('low', 'medium', 'high'),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_workspace_status (workspace_id, review_status),
    FOREIGN KEY (workspace_id) REFERENCES workspaces(id),
    FOREIGN KEY (user_id) REFERENCES users(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 法律知识库表
CREATE TABLE legal_knowledge (
    id VARCHAR(36) PRIMARY KEY,
    content_type ENUM('law', 'case', 'template', 'rule'),
    content TEXT NOT NULL,
    embedding JSON,
    metadata JSON,
    tenant_id VARCHAR(36),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_content_type (content_type),
    INDEX idx_tenant (tenant_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```

**验收标准**:
- [ ] 所有表创建成功
- [ ] 外键约束生效
- [ ] 索引创建成功

---

### Task 2.2: 实现 SQLAlchemy 模型层

**优先级**: P0
**预估工时**: 4 小时

**文件**: `backend/app/models/`

**模型类**:
- `Tenant` - 租户模型
- `Workspace` - 工作区模型
- `User` - 用户模型
- `Contract` - 合同模型
- `LegalKnowledge` - 法律知识模型

**验收标准**:
- [ ] 所有模型类定义完整
- [ ] 关系定义正确（一对多、多对一）
- [ ] 可通过 SQLAlchemy 正确查询

---

### Task 2.3: 实现 JWT 认证系统

**优先级**: P0
**预估工时**: 4 小时

**文件**: `backend/app/core/security.py`

**功能**:
1. Token 生成
   ```python
   def create_access_token(data: dict, expires_delta: timedelta = None) -> str
   ```
2. Token 验证
   ```python
   def verify_token(token: str) -> Optional[str]
   ```
3. 密码加密
   ```python
   def hash_password(password: str) -> str
   def verify_password(password: str, hashed: str) -> bool
   ```

**验收标准**:
- [ ] Token 生成和验证正常
- [ ] Token 过期时间正确
- [ ] 密码加密存储安全

---

### Task 2.4: 实现租户隔离中间件

**优先级**: P0
**预估工时**: 4 小时

**文件**: `backend/app/middleware/tenant_isolation.py`

**功能**:
1. 从请求中提取租户上下文
2. 验证用户权限
3. 确保数据隔离

**验收标准**:
- [ ] 租户 A 用户无法访问租户 B 数据
- [ ] 未授权访问返回 403
- [ ] 中间件在所有 API 上生效

---

### Task 2.5: 实现用户注册/登录 API

**优先级**: P0
**预估工时**: 4 小时

**文件**: `backend/app/api/v1/endpoints/auth.py`

**接口**:
| 方法 | 路径 | 描述 |
|------|------|------|
| POST | `/api/v1/auth/register` | 用户注册 |
| POST | `/api/v1/auth/login` | 用户登录 |
| POST | `/api/v1/auth/logout` | 用户登出 |
| GET | `/api/v1/auth/me` | 获取当前用户信息 |

**请求/响应示例**:
```json
// POST /api/v1/auth/register
{
  "email": "user@example.com",
  "password": "secure123",
  "tenant_name": "我的公司"
}

// Response
{
  "token": "eyJhbG...",
  "user": {
    "id": "uuid",
    "email": "user@example.com",
    "tenant_id": "uuid"
  }
}
```

**验收标准**:
- [ ] 注册流程完整
- [ ] 登录返回 Token
- [ ] 邮箱唯一性校验
- [ ] 密码强度校验

---

### Task 2.6: 实现微信登录 API

**优先级**: P1
**预估工时**: 4 小时

**文件**: `backend/app/api/v1/endpoints/auth.py`

**接口**:
| 方法 | 路径 | 描述 |
|------|------|------|
| POST | `/api/v1/auth/wx-login` | 微信登录 |

**流程**:
1. 小程序端调用 `wx.login()` 获取 code
2. 后端用 code 换 OpenID
3. 查找或创建用户
4. 返回 JWT Token

**验收标准**:
- [ ] 微信登录流程打通
- [ ] 新用户自动创建租户
- [ ] 老用户正常登录

---

### Task 2.7: 实现工作区管理 API

**优先级**: P1
**预估工时**: 4 小时

**文件**: `backend/app/api/v1/endpoints/workspaces.py`

**接口**:
| 方法 | 路径 | 描述 |
|------|------|------|
| GET | `/api/v1/workspaces` | 获取工作区列表 |
| POST | `/api/v1/workspaces` | 创建工作区 |
| GET | `/api/v1/workspaces/{id}` | 获取工作区详情 |
| PUT | `/api/v1/workspaces/{id}` | 更新工作区 |
| DELETE | `/api/v1/workspaces/{id}` | 删除工作区 |

**验收标准**:
- [ ] 工作区 CRUD 操作完整
- [ ] 租户隔离生效
- [ ] 权限校验正确

---

## 依赖关系

```
Task 2.1 (数据库) ─→ Task 2.2 (模型)
                        │
Task 2.3 (JWT) ←────────┘
                        │
Task 2.4 (租户隔离) ←───┘
                        │
Task 2.5 (注册登录) ←───┘
                        │
Task 2.6 (微信登录) ←───┘
                        │
Task 2.7 (工作区) ←─────┘
```

---

## 验收清单

### 数据库验收
- [ ] 所有表创建成功
- [ ] 外键约束生效
- [ ] 索引工作正常
- [ ] 可执行基础 CRUD 操作

### 后端 API 验收
- [ ] 用户注册 API 正常
- [ ] 用户登录 API 正常
- [ ] JWT Token 验证通过
- [ ] 租户隔离中间件生效
- [ ] 工作区 CRUD API 正常

### 安全验收
- [ ] 密码加密存储
- [ ] Token 过期时间正确
- [ ] 跨租户访问被阻止
- [ ] SQL 注入防护

---

## 代码结构

```
backend/
├── app/
│   ├── api/
│   │   └── v1/
│   │       ├── endpoints/
│   │       │   ├── auth.py
│   │       │   └── workspaces.py
│   │       └── deps.py
│   ├── core/
│   │   ├── config.py
│   │   └── security.py
│   ├── db/
│   │   ├── base.py
│   │   └── session.py
│   ├── models/
│   │   ├── tenant.py
│   │   ├── workspace.py
│   │   ├── user.py
│   │   └── contract.py
│   └── middleware/
│       └── tenant_isolation.py
├── alembic/
└── requirements.txt
```

---

## 下一步

Phase 2 完成后，进入 **Phase 3: 合同上传与解析**

主要工作：
1. 实现文件上传 API（对接阿里云 OSS）
2. 实现 PDF 解析功能
3. 实现 Word 解析功能
4. 实现合同类型自动识别
