# Fly.io 部署指南 - 法务 AI SaaS
## 前后端合并部署方案

---

## 部署架构

```
用户请求 → fly.io (legal-ai-saas)
              ├─ FastAPI 后端 (:8000)
              ├─ 前端静态文件 (/assets, /fonts)
              └─ SQLite 数据库 (持久化存储)
```

**访问 URL**：
- 主页：`https://legal-ai-saas.fly.dev/`
- API：`https://legal-ai-saas.fly.dev/api/v1/...`
- 文档：`https://legal-ai-saas.fly.dev/docs`

---

## 部署前准备

### 1. 安装 Fly.io CLI

```powershell
# 使用 npm 安装
npm install -g @fly/flyctl

# 验证
flyctl version
```

### 2. 登录

```powershell
flyctl auth login
```

---

## 部署步骤

### 步骤 1: 创建应用

```powershell
cd "C:\Users\kalvi\Documents\claude application\ai saas legal"

# 创建应用
flyctl launch --name legal-ai-saas-kalvi
```

**交互选项**：
- `Would you like to copy its configuration to the new app?` → **No**
- `Select region:` → **sin (Singapore, 新加坡)**

### 步骤 2: 设置密钥

```powershell
# 生成 JWT 密钥
$JWT_SECRET = -join ((48..57) + (65..90) + (97..122) | Get-Random -Count 32 | ForEach-Object {[char]$_})

# 设置密钥
flyctl secrets set JWT_SECRET=$JWT_SECRET
flyctl secrets set ZHIPU_API_KEY=de4f2b05ed614848b844a77928dbcb3e.nUbrXEpkVAnpD62O
flyctl secrets set ENVIRONMENT=production
flyctl secrets set DATABASE_TYPE=sqlite
```

### 步骤 3: 创建持久化存储

```powershell
flyctl volumes create legal_data --size 1 --region sin
```

### 步骤 4: 部署

```powershell
# 部署（首次需要 5-10 分钟）
flyctl deploy --dockerfile backend/Dockerfile.fly
```

### 步骤 5: 初始化数据库

```powershell
# 进入容器执行初始化
flyctl ssh console --app legal-ai-saas-kalvi -C "python init_db.py"
```

### 步骤 6: 验证

```powershell
# 查看状态
flyctl status

# 查看日志
flyctl logs

# 打开浏览器
flyctl open
```

---

## 费用

| 项目 | 费用 |
|------|------|
| VM (shared-cpu-2x, 512MB) | $3.88/月 |
| 存储 1GB | $0.13/月 |
| 流量 | $0.02/GB |
| **总计** | **~$4/月** |

**$3 免费额度后：约 $1/月**

---

## 常用命令

```powershell
# 查看日志
flyctl logs -f

# 查看状态
flyctl status

# 重启
flyctl restart

# SSH 进入容器
flyctl ssh console

# 暂停 (停止计费)
flyctl apps stop legal-ai-saas-kalvi

# 恢复
flyctl apps start legal-ai-saas-kalvi

# 更新部署
flyctl deploy --dockerfile backend/Dockerfile.fly
```

---

## 本地测试

```powershell
# 1. 构建前端
cd frontend
npm install
npm run build

# 2. 复制 dist 到 backend/static
Copy-Item -Path dist\* -Destination ..\backend\static\ -Recurse

# 3. 启动后端
cd ..\backend
python main.py

# 访问 http://localhost:8000
```
