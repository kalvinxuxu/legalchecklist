# Phase 7.5 生产环境部署 - 阿里云 ECS 部署方案

**创建日期**: 2026-04-02  
**目标平台**: 阿里云 ECS (Ubuntu 20.04/22.04)

---

## 一、部署架构

```
                    用户请求
                       │
                       ▼
              ┌─────────────────┐
              │ 阿里云安全组     │
              │ 端口：22,80,443 │
              └────────┬────────┘
                       │
                       ▼
              ┌─────────────────┐
              │  Nginx          │
              │  - 前端静态文件  │
              │  - HTTPS 终止    │
              │  - API 反向代理   │
              └────────┬────────┘
                       │
         ┌─────────────┼─────────────┐
         ▼             ▼             ▼
  ┌──────────┐  ┌──────────┐  ┌──────────┐
  │FastAPI   │  │MySQL 8.0 │  │Redis 7   │
  │:8000     │  │:3306     │  │:6379     │
  └──────────┘  └──────────┘  └──────────┘
```

---

## 二、新增文件清单

### 2.1 前端 Dockerfile (待创建)
**路径**: `frontend/Dockerfile`

```dockerfile
# 构建阶段
FROM node:20-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci --registry=https://registry.npmmirror.com
COPY . .
RUN npm run build

# 生产阶段
FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

### 2.2 前端 Nginx 配置 (待创建)
**路径**: `frontend/nginx.conf`

```nginx
server {
    listen 80;
    server_name _;
    
    root /usr/share/nginx/html;
    index index.html;
    
    location / {
        try_files $uri $uri/ /index.html;
    }
    
    # API 代理到后端
    location /api/ {
        proxy_pass http://app:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### 2.3 更新 docker-compose.yml
**路径**: `docker/docker-compose.yml`

需要添加 frontend 服务并配置 volume 挂载。

### 2.4 生产环境 .env 模板 (待创建)
**路径**: `backend/.env.production.example`

### 2.5 数据库备份脚本 (待创建)
**路径**: `scripts/backup-db.sh`

### 2.6 HTTPS 配置脚本 (待创建)
**路径**: `scripts/setup-https.sh`

---

## 三、部署步骤

### 步骤 1: 阿里云安全组配置

登录阿里云控制台 → 云服务器 ECS → 安全组 → 配置规则：

| 端口 | 协议 | 授权对象 | 说明 |
|------|------|----------|------|
| 22 | TCP | 0.0.0.0/0 | SSH 远程连接 |
| 80 | TCP | 0.0.0.0/0 | HTTP (HTTPS 重定向) |
| 443 | TCP | 0.0.0.0/0 | HTTPS |

### 步骤 2: 服务器初始化

```bash
# SSH 登录
ssh root@<你的服务器 IP>

# 更新系统
apt update && apt upgrade -y

# 安装必要工具
apt install -y curl git vim ufw

# 配置防火墙
ufw allow 22/tcp
ufw allow 80/tcp
ufw allow 443/tcp
ufw --force enable
```

### 步骤 3: 安装 Docker

```bash
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

### 步骤 4: 上传项目代码

**方式 A - Git 克隆**:
```bash
mkdir -p /opt/legal-ai-saas
cd /opt/legal-ai-saas
git clone <你的仓库地址> .
```

**方式 B - SCP 上传**:
```bash
# 在本地 PowerShell 执行
scp -r ./* root@<服务器 IP>:/opt/legal-ai-saas/
```

### 步骤 5: 配置环境变量

```bash
cd /opt/legal-ai-saas/backend
cp .env.example .env
vi .env
```

**生产环境配置示例**:
```bash
# 环境
ENVIRONMENT=production

# 数据库 (Docker 内部使用)
DATABASE_TYPE=mysql
DATABASE_URL=mysql://root:<强密码>@db:3306/legal_saas

# Redis
REDIS_URL=redis://redis:6379

# JWT
JWT_SECRET=<生成随机密钥：openssl rand -hex 32>
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440

# AI API
ZHIPU_API_KEY=你的智谱 AI Key

# 阿里云 OSS
ALIYUN_ACCESS_KEY_ID=你的 AccessKey
ALIYUN_ACCESS_KEY_SECRET=你的 AccessSecret
ALIYUN_OSS_BUCKET=legal-saas
ALIYUN_OSS_ENDPOINT=oss-cn-hangzhou.aliyuncs.com
```

### 步骤 6: 构建并启动服务

```bash
cd /opt/legal-ai-saas/docker

# 构建镜像
docker compose build

# 启动服务
docker compose up -d

# 查看状态
docker compose ps

# 查看日志
docker compose logs -f
```

### 步骤 7: 初始化数据库

```bash
# 等待 MySQL 启动
sleep 10

# 进入数据库容器
docker compose exec db bash

# 执行初始化脚本
mysql -uroot -p<密码> legal_saas < /docker-entrypoint-initdb.d/init.sql

# 退出
exit
```

### 步骤 8: 验证服务

```bash
# 健康检查
curl http://localhost/health

# 测试 API
curl http://localhost/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"Test1234!"}'
```

---

## 四、HTTPS 配置 (两种方式)

### 方式 A: Let's Encrypt (推荐，需域名)

**前提**: 已有域名并完成 ICP 备案

```bash
# 安装 Certbot
apt install certbot -y

# 获取证书 ( standalone 模式，无需 Nginx)
certbot certonly --standalone -d your-domain.com

# 证书位置
# /etc/letsencrypt/live/your-domain.com/fullchain.pem
# /etc/letsencrypt/live/your-domain.com/privkey.pem
```

**配置 Docker 挂载证书**:

编辑 `docker/docker-compose.yml`:
```yaml
services:
  nginx:
    volumes:
      - /etc/letsencrypt/live/your-domain.com:/etc/nginx/ssl:ro
```

编辑 `docker/nginx.conf`:
```nginx
server {
    listen 443 ssl;
    server_name your-domain.com;
    
    ssl_certificate /etc/nginx/ssl/fullchain.pem;
    ssl_certificate_key /etc/nginx/ssl/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    
    location / {
        root /usr/share/nginx/html;
        try_files $uri $uri/ /index.html;
    }
    
    location /api/ {
        proxy_pass http://app:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}

# HTTP 自动跳转 HTTPS
server {
    listen 80;
    server_name your-domain.com;
    return 301 https://$server_name$request_uri;
}
```

**自动续期**:
```bash
# 添加定时任务
crontab -e
# 添加：0 0 1 * * certbot renew --quiet
```

### 方式 B: 阿里云免费 SSL (需域名)

1. 登录阿里云控制台 → SSL 证书服务
2. 申请免费证书（1 年有效期）
3. 下载 Nginx 格式的证书
4. 上传到服务器 `/etc/nginx/ssl/` 目录
5. 配置同上

### 方式 C: 仅 IP 访问 (临时方案，无 HTTPS)

```nginx
server {
    listen 80;
    server_name <服务器 IP>;
    
    location / {
        root /usr/share/nginx/html;
        try_files $uri $uri/ /index.html;
    }
    
    location /api/ {
        proxy_pass http://app:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

**注意**: 生产环境强烈建议使用 HTTPS，否则浏览器可能限制部分功能。

---

## 五、数据库备份策略

### 创建备份脚本

**路径**: `scripts/backup-db.sh`

```bash
#!/bin/bash

# 配置
BACKUP_DIR="/opt/backups/legal-saas"
MYSQL_CONTAINER="legal-ai-saas-db-1"
MYSQL_USER="root"
MYSQL_PASS="<你的数据库密码>"
DB_NAME="legal_saas"
RETENTION_DAYS=30

# 创建目录
mkdir -p $BACKUP_DIR

# 生成备份文件名
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/${DB_NAME}_${DATE}.sql"

# 执行备份
docker exec $MYSQL_CONTAINER mysqldump -u$MYSQL_USER -p$MYSQL_PASS $DB_NAME > $BACKUP_FILE

# 压缩
gzip $BACKUP_FILE

# 删除旧备份
find $BACKUP_DIR -name "*.sql.gz" -mtime +$RETENTION_DAYS -delete

echo "Backup completed: ${BACKUP_FILE}.gz"
```

### 配置定时任务

```bash
# 赋予执行权限
chmod +x /opt/legal-ai-saas/scripts/backup-db.sh

# 添加 cron 任务 (每天凌晨 3 点)
crontab -e
# 添加：0 3 * * * /opt/legal-ai-saas/scripts/backup-db.sh
```

### 备份到阿里云 OSS (可选)

```bash
# 安装 ossutil
wget https://gosspublic.alicdn.com/ossutil/install.sh
bash install.sh

# 配置
ossutil config -e oss-cn-hangzhou.aliyuncs.com -i <AccessKey> -k <AccessSecret>

# 上传备份
ossutil cp -r /opt/backups/legal-saas oss://legal-saas/backups/
```

---

## 六、监控与日志

### 查看服务状态

```bash
# 容器状态
docker compose ps

# 实时日志
docker compose logs -f app
docker compose logs -f nginx

# 资源使用
docker stats
```

### 应用监控 (可选)

配置 Prometheus + Grafana:
```yaml
# docker-compose.monitoring.yml
services:
  prometheus:
    image: prom/prometheus
    ports:
      - "9090:9090"
  
  grafana:
    image: grafana/grafana
    ports:
      - "3000:3000"
```

### 错误追踪 (推荐)

集成 Sentry:
```bash
pip install sentry-sdk
```

在 `backend/main.py` 中添加:
```python
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration

sentry_sdk.init(
    dsn="你的 Sentry DSN",
    integrations=[FastApiIntegration()],
    traces_sample_rate=1.0
)
```

---

## 七、部署检查清单

| 项目 | 状态 |
|------|------|
| 阿里云安全组配置 (22,80,443) | ⬜ |
| Docker 安装 | ⬜ |
| 项目代码上传 | ⬜ |
| 环境变量配置 (.env) | ⬜ |
| Docker 镜像构建 | ⬜ |
| 服务启动 | ⬜ |
| 数据库初始化 | ⬜ |
| 健康检查通过 | ⬜ |
| HTTPS 配置 | ⬜ |
| 数据库备份配置 | ⬜ |
| 监控配置 | ⬜ |

---

## 八、常见问题

### Q1: 容器启动失败
```bash
# 查看详细日志
docker compose logs app

# 检查配置
docker compose config
```

### Q2: 数据库连接超时
- 确保 MySQL 完全启动 (等待 30 秒)
- 检查密码是否正确
- 确认网络连通：`docker compose exec app ping db`

### Q3: 前端页面 404
- 检查 `frontend/dist` 是否构建成功
- 确认 Nginx 配置中的 root 路径

### Q4: HTTPS 证书无效
- 检查证书文件路径
- 确认域名解析正确
- 查看 Nginx 日志：`docker compose logs nginx`

---

## 九、费用估算

| 资源 | 配置 | 月费用 (CNY) |
|------|------|-------------|
| ECS | 2 核 4G, 3Mbps | ~160 |
| 域名 | .com | ~5/月 (60/年) |
| SSL 证书 | Let's Encrypt | 免费 |
| OSS | 40GB 存储 | ~10 |
| **总计** | | **~175/月** |

---

## 十、下一步

1. **执行部署** - 按照上述步骤部署到阿里云
2. **配置 HTTPS** - 建议先申请域名再配置
3. **设置监控告警** - 阿里云云监控
4. **种子用户测试** - Phase 7.7
