# Phase 1: 项目初始化 - 执行计划

**版本**: 1.0
**创建日期**: 2026-03-31
**状态**: 待执行

---

## 目标

完成项目基础设置，验证技术可行性，为后续开发做准备。

**预计工期**: 3 天

---

## 任务分解

### Task 1.1: 购买域名并开始 ICP 备案

**优先级**: P0
**预估工时**: 1 天

**步骤**:
1. 登录阿里云官网 (aliyun.com)
2. 选择并购买域名（建议：`.com` 或 `.cn`）
   - 域名示例：`fatiao.ai`, `hetong-ai.com`, `lawbot.cn`
3. 完成域名实名认证（上传营业执照或身份证）
4. 提交 ICP 备案申请
   - 准备材料：身份证正反面、域名证书
   - 选择备案类型：企业备案（需要营业执照）或个人备案
5. 等待初审（1-2 工作日）和管局审核（10-20 工作日）

**验收标准**:
- [ ] 域名购买成功
- [ ] 域名实名认证完成
- [ ] 备案申请已提交，获得备案编号

**注意事项**:
- 备案期间域名无法访问
- 个人备案不能用于商业网站
- 建议使用企业主体备案

---

### Task 1.2: 购买云服务器

**优先级**: P0
**预估工时**: 2 小时

**步骤**:
1. 登录腾讯云官网 (cloud.tencent.com)
2. 选择轻量应用服务器（Lighthouse）
   - 配置：2 核 CPU / 4GB 内存 / 50GB SSD
   - 系统：Ubuntu 22.04 LTS
   - 地域：广州/上海（离用户近）
3. 完成支付
4. 设置 SSH 密钥对
5. 测试 SSH 连接

**推荐配置**:
- 机型：腾讯云轻量应用服务器 Lighthouse
- CPU: 2 核
- 内存：4GB
- 存储：50GB SSD
- 带宽：5Mbps
- 月费用：约 ¥80

**验收标准**:
- [ ] 服务器创建成功
- [ ] 可通过 SSH 连接
- [ ] 服务器可访问外网

---

### Task 1.3: 配置开发环境（Docker Compose）

**优先级**: P0
**预估工时**: 4 小时

**步骤**:
1. SSH 登录服务器
2. 安装 Docker
   ```bash
   curl -fsSL https://get.docker.com | bash
   ```
3. 安装 Docker Compose
   ```bash
   apt install docker-compose-plugin
   ```
4. 创建项目目录
   ```bash
   mkdir -p /opt/legal-ai-saas
   cd /opt/legal-ai-saas
   ```
5. 创建 `docker-compose.yml` 文件
6. 创建 `.env` 文件（环境变量）
7. 测试启动
   ```bash
   docker compose up -d
   ```

**验收标准**:
- [ ] Docker 正常安装
- [ ] Docker Compose 可正常启动容器
- [ ] MySQL 可连接
- [ ] Redis 可连接

---

### Task 1.4: 创建 Git 仓库 + 项目骨架

**优先级**: P0
**预估工时**: 2 小时

**步骤**:
1. 创建 GitHub/Gitee 仓库
   - 仓库名：`legal-ai-saas`
   - 可见性：私有（初期）
2. 初始化本地仓库
   ```bash
   git init
   git remote add origin git@github.com:your-org/legal-ai-saas.git
   ```
3. 创建 `.gitignore` 文件
4. 创建项目目录结构
   ```
   legal-ai-saas/
   ├── frontend/
   ├── backend/
   ├── miniprogram/
   ├── docs/
   ├── scripts/
   └── docker/
   ```
5. 初始提交
   ```bash
   git add .
   git commit -m "Initial commit: project skeleton"
   git push -u origin main
   ```

**验收标准**:
- [ ] Git 仓库创建成功
- [ ] 项目目录结构完整
- [ ] 代码已推送到远程仓库

---

### Task 1.5: 申请智谱 AI API Key

**优先级**: P0
**预估工时**: 30 分钟

**步骤**:
1. 访问智谱 AI 开放平台 (open.bigmodel.cn)
2. 注册/登录账号
3. 创建应用
4. 获取 API Key
5. 测试 API 调用
   ```python
   from zhipuai import ZhipuAI
   client = ZhipuAI(api_key="your-api-key")
   response = client.chat.completions.create(
       model="glm-4",
       messages=[{"role": "user", "content": "你好"}]
   )
   print(response.choices[0].message.content)
   ```

**验收标准**:
- [ ] API Key 获取成功
- [ ] 可成功调用智谱 API
- [ ] Embedding API 也可正常调用

**参考链接**:
- [智谱 AI 开放平台](https://open.bigmodel.cn/)
- [API 文档](https://open.bigmodel.cn/dev/api)

---

### Task 1.6: 申请微信小程序 AppID

**优先级**: P1
**预估工时**: 1 天

**步骤**:
1. 访问微信公众平台 (mp.weixin.qq.com)
2. 注册小程序账号
   - 主体类型：企业/个体工商户
   - 准备材料：营业执照、法人身份证
3. 完成账号信息设置
4. 获取 AppID 和 AppSecret
5. 配置服务器域名（后续）

**验收标准**:
- [ ] 小程序账号注册成功
- [ ] 获得 AppID 和 AppSecret
- [ ] 可登录小程序开发后台

**注意事项**:
- 小程序需要企业认证
- 部分类目需要特殊资质
- 法务 AI 可能属于"工具 - 办公"类目

**参考链接**:
- [微信公众平台](https://mp.weixin.qq.com/)
- [小程序开发文档](https://developers.weixin.qq.com/miniprogram/dev/framework/)

---

## 依赖关系

```
Task 1.1 (域名备案) ────────────────┐
                                     │
Task 1.2 (服务器) ─→ Task 1.3 (Docker) ─→ Task 1.4 (Git)
                                     │
Task 1.5 (智谱 API) ←────────────────┘
Task 1.6 (微信小程序)
```

---

## 验收清单

### 环境验收
- [ ] 域名已购买，备案申请已提交
- [ ] 服务器可 SSH 连接
- [ ] Docker Compose 可正常启动
- [ ] MySQL 可远程连接
- [ ] Redis 可远程连接

### 服务验收
- [ ] 智谱 API 可正常调用
- [ ] 智谱 Embedding API 可正常调用
- [ ] 微信小程序 AppID 已获取

### 代码验收
- [ ] Git 仓库已创建
- [ ] 项目目录结构完整
- [ ] 首次提交已完成

---

## 风险与问题

| 风险 | 影响 | 缓解措施 |
|------|------|---------|
| ICP 备案周期长（20 工作日） | 影响正式上线 | 开发阶段可用测试环境，备案期间不影响开发 |
| 微信小程序审核不通过 | 影响小程序发布 | 提前咨询类目要求，准备相关资质 |
| 服务器配置不当 | 安全风险 | 配置防火墙、禁用密码登录、定期更新 |

---

## 下一步

Phase 1 完成后，进入 **Phase 2: 数据库与后端基础**

主要工作：
1. 设计并创建数据库表结构
2. 实现 SQLAlchemy 模型层
3. 实现 JWT 认证系统
4. 实现租户隔离中间件
