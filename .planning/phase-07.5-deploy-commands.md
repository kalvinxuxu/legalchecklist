# 阿里云 ECS 部署命令 - 法务 AI SaaS

**服务器要求**: Ubuntu 20.04 或 22.04

---

## 步骤 1: SSH 登录服务器

```bash
ssh root@<你的服务器 IP>
```

---

## 步骤 2: 系统初始化和安装 Docker

```bash
# 更新系统
apt update && apt upgrade -y

# 安装必要工具
apt install -y curl git vim ufw

# 配置防火墙
ufw allow 22/tcp
ufw allow 80/tcp
ufw allow 443/tcp
ufw --force enable

# 安装 Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh
rm get-docker.sh

# 启动 Docker
systemctl enable docker
systemctl start docker

# 验证安装
docker --version
docker compose version
```

---

## 步骤 3: 创建项目目录并上传代码

```bash
# 创建项目目录
mkdir -p /opt/legal-ai-saas
cd /opt/legal-ai-saas
```

**从本地上传代码** (在本地 PowerShell 执行，不是在服务器):

```powershell
# 将项目文件打包
cd "C:\Users\kalvi\Documents\claude application\ai saas legal"

# 使用 scp 上传 (替换 <服务器 IP> 为你的阿里云 IP)
scp -r backend docker scripts frontend root@<服务器 IP>:/opt/legal-ai-saas/
```

---

## 步骤 4: 配置环境变量

```bash
cd /opt/legal-ai-saas/backend

# 复制配置模板
cp .env.production.example .env

# 编辑配置
vi .env
```

**按 `i` 进入编辑模式，修改以下内容**:

```bash
# 环境配置
ENVIRONMENT=production

# MySQL 数据库密码 (生成强密码)
MYSQL_PASSWORD=LegalSaas2026!Strong#888

# JWT 密钥 (生成随机密钥)
JWT_SECRET=在此粘贴 openssl rand -hex 32 的输出

# 智谱 AI API Key
ZHIPU_API_KEY=de4f2b05ed614848b844a77928dbcb3e.nUbrXEpkVAnpD62O

# 阿里云 OSS (如果没有先留空)
ALIYUN_ACCESS_KEY_ID=
ALIYUN_ACCESS_KEY_SECRET=
ALIYUN_OSS_BUCKET=legal-saas
ALIYUN_OSS_ENDPOINT=oss-cn-hangzhou.aliyuncs.com
```

**编辑完成后**:
- 按 `ESC` 退出编辑
- 输入 `:wq` 保存并退出

**生成 JWT 密钥** (新开一个 SSH 窗口或后台执行):
```bash
openssl rand -hex 32
```
复制输出结果粘贴到 `.env` 文件的 `JWT_SECRET=` 后面

---

## 步骤 5: 构建并启动服务

```bash
cd /opt/legal-ai-saas/docker

# 构建所有镜像 (首次需要 10-20 分钟)
docker compose build

# 启动服务
docker compose up -d

# 查看服务状态
docker compose ps
```

**等待服务启动** (约 30 秒):
```bash
sleep 30
```

---

## 步骤 6: 验证服务

```bash
# 健康检查
curl http://localhost/health

# 应该返回：{"status":"healthy"}

# 查看应用日志
docker compose logs app

# 查看 Nginx 日志
docker compose logs nginx
```

**测试 API** (注册新用户):
```bash
curl http://localhost/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"Test1234!"}'
```

---

## 步骤 7: 配置数据库备份

```bash
# 创建备份目录
mkdir -p /opt/backups/legal-saas

# 赋予备份脚本执行权限
chmod +x /opt/legal-ai-saas/scripts/backup-db.sh

# 测试备份
bash /opt/legal-ai-saas/scripts/backup-db.sh

# 配置定时任务 (每天凌晨 3 点备份)
crontab -e
```

**添加以下内容**:
```
0 3 * * * /opt/legal-ai-saas/scripts/backup-db.sh
```

---

## 常用运维命令

```bash
# 查看服务状态
docker compose ps

# 查看实时日志
docker compose logs -f app
docker compose logs -f nginx

# 重启服务
docker compose restart

# 停止服务
docker compose down

# 查看资源使用
docker stats

# 进入容器
docker compose exec app bash
docker compose exec db bash

# 更新代码后重新部署
cd /opt/legal-ai-saas
git pull  # 如果使用 Git
docker compose build
docker compose up -d
```

---

## 访问服务

部署完成后:

- **前端访问**: `http://<你的服务器 IP>/`
- **API 文档**: `http://<你的服务器 IP>/docs`
- **健康检查**: `http://<你的服务器 IP>/health`

---

## 故障排查

### 容器启动失败
```bash
# 查看详细日志
docker compose logs app

# 检查配置
docker compose config
```

### 数据库连接失败
```bash
# 等待 MySQL 完全启动
sleep 30

# 测试连接
docker compose exec db mysql -uroot -p<MYSQL_PASSWORD> -e "SHOW DATABASES;"
```

### 前端 404
```bash
# 检查前端是否构建成功
docker compose logs frontend

# 重新构建
docker compose build frontend
docker compose up -d
```

---

## 下一步

1. **测试功能** - 访问 `http://<服务器 IP>` 测试前端
2. **配置域名** - 在阿里云 DNS 控制台添加 A 记录
3. **配置 HTTPS** - 有域名后运行 `scripts/setup-https.sh`
4. **种子用户测试** - Phase 7.7
