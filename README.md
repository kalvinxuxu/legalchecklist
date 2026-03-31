# 法务 AI SaaS 平台

> 面向中小企业的轻量化合同审查工具

---

## 快速开始

### 1. 环境准备

- Docker & Docker Compose
- Python 3.11 (本地开发)

### 2. 配置环境变量

```bash
cd backend
cp .env.example .env
# 编辑 .env，填入你的 DeepSeek API Key
```

### 3. 启动服务

```bash
cd docker
docker compose up -d
```

### 4. 验证服务

```bash
# 检查服务状态
docker compose ps

# 查看日志
docker compose logs -f app

# 测试 API
curl http://localhost/health
```

---

## 项目结构

```
legal-ai-saas/
├── backend/                 # FastAPI 后端
│   ├── app/
│   │   ├── api/            # API 路由
│   │   ├── core/           # 核心配置
│   │   ├── db/             # 数据库
│   │   ├── models/         # 数据模型
│   │   ├── schemas/        # Pydantic 模型
│   │   └── services/       # 业务服务
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/               # Vue 3 前端 (待开发)
├── miniprogram/           # 微信小程序 (待开发)
├── docker/
│   ├── docker-compose.yml
│   ├── nginx.conf
│   └── init.sql
└── docs/                  # 文档
```

---

## API 文档

启动服务后访问：http://localhost/docs

### 主要接口

| 接口 | 方法 | 描述 |
|------|------|------|
| `/api/v1/auth/register` | POST | 用户注册 |
| `/api/v1/auth/login` | POST | 用户登录 |
| `/api/v1/auth/me` | GET | 获取当前用户 |
| `/api/v1/workspaces/` | GET | 获取工作区列表 |
| `/api/v1/workspaces/` | POST | 创建工作区 |
| `/api/v1/contracts/upload` | POST | 上传合同 |
| `/api/v1/contracts/` | GET | 获取合同列表 |

---

## 技术栈

| 层级 | 技术 |
|------|------|
| **后端** | FastAPI (Python) |
| **数据库** | MySQL 8.0 |
| **缓存** | Redis |
| **LLM** | DeepSeek API |
| **部署** | Docker Compose |

---

## 下一步

1. **完善后端功能**
   - [ ] 合同审查接口
   - [ ] PDF/Word 解析
   - [ ] 法律知识库填充

2. **前端开发**
   - [ ] Vue 3 项目搭建
   - [ ] 登录/注册页面
   - [ ] 合同上传组件
   - [ ] 审查报告展示

3. **测试与部署**
   - [ ] 单元测试
   - [ ] 生产环境配置
   - [ ] 域名备案

---

## License

MIT
