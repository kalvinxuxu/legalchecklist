#!/bin/bash

# 法务 AI SaaS - 服务器一键部署脚本
# 用法：bash deploy.sh

set -e

echo "=========================================="
echo "  法务 AI SaaS - 服务器部署脚本"
echo "=========================================="
echo ""

# === 配置区域 ===
PROJECT_NAME="legal-ai-saas"
PROJECT_DIR="/opt/legal-ai-saas"
DOCKER_COMPOSE_FILE="$PROJECT_DIR/docker/docker-compose.yml"

# === 颜色定义 ===
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# === 步骤 1: 检查是否已安装 Docker ===
check_docker() {
    log_info "检查 Docker 安装状态..."
    if ! command -v docker &> /dev/null; then
        log_warn "Docker 未安装，开始安装..."
        install_docker
    else
        log_info "Docker 已安装：$(docker --version)"
    fi

    if ! command -v docker compose &> /dev/null; then
        log_warn "Docker Compose 未安装，开始安装..."
        install_docker_compose
    else
        log_info "Docker Compose 已安装：$(docker compose version)"
    fi
}

# === 步骤 2: 安装 Docker ===
install_docker() {
    curl -fsSL https://get.docker.com -o get-docker.sh
    sh get-docker.sh
    rm get-docker.sh
    systemctl enable docker
    systemctl start docker
    log_info "Docker 安装完成"
}

# === 步骤 3: 安装 Docker Compose ===
install_docker_compose() {
    apt-get update
    apt-get install -y docker-compose-plugin
    log_info "Docker Compose 安装完成"
}

# === 步骤 4: 检查项目代码 ===
check_project() {
    log_info "检查项目代码..."

    if [ ! -d "$PROJECT_DIR" ]; then
        log_warn "项目目录不存在，请上传代码到 $PROJECT_DIR"
        echo ""
        echo "你可以选择以下任一方式上传代码:"
        echo "  1. Git clone: git clone <仓库地址> $PROJECT_DIR"
        echo "  2. SCP 上传：scp -r ./* root@服务器 IP:$PROJECT_DIR"
        echo ""
        exit 1
    fi

    if [ ! -f "$PROJECT_DIR/backend/.env" ]; then
        log_warn "backend/.env 文件不存在"
        echo ""
        echo "请先配置环境变量:"
        echo "  cd $PROJECT_DIR/backend"
        echo "  cp .env.example .env"
        echo "  vi .env  # 填入 DeepSeek API Key"
        echo ""
        exit 1
    fi
}

# === 步骤 5: 创建必要目录 ===
create_directories() {
    log_info "创建必要目录..."
    mkdir -p "$PROJECT_DIR/uploads"
    mkdir -p "$PROJECT_DIR/logs"
    mkdir -p "$PROJECT_DIR/docker/ssl"
}

# === 步骤 6: 配置防火墙 ===
setup_firewall() {
    log_info "配置防火墙..."
    if command -v ufw &> /dev/null; then
        ufw allow 22/tcp
        ufw allow 80/tcp
        ufw allow 443/tcp
        ufw --force enable
        log_info "防火墙配置完成"
    else
        log_warn "ufw 未安装，跳过防火墙配置"
    fi
}

# === 步骤 7: 启动服务 ===
start_services() {
    log_info "启动服务..."
    cd "$PROJECT_DIR/docker"

    # 停止旧容器
    docker compose down || true

    # 启动新容器
    docker compose up -d

    # 等待服务启动
    sleep 5

    # 检查服务状态
    docker compose ps
}

# === 步骤 8: 验证服务 ===
verify_services() {
    log_info "验证服务..."

    # 检查 API 是否可访问
    if curl -s http://localhost/health | grep -q "healthy"; then
        log_info "API 服务正常运行"
    else
        log_error "API 服务启动失败，请查看日志：docker compose logs app"
        exit 1
    fi

    # 检查数据库是否可连接
    if docker compose exec -T db mysql -uroot -p"${MYSQL_ROOT_PASSWORD:-legal_saas_2024}" -e "SELECT 1" &> /dev/null; then
        log_info "MySQL 服务正常"
    else
        log_warn "MySQL 服务可能需要初始化，请稍候重试"
    fi
}

# === 步骤 9: 初始化数据库 ===
init_database() {
    log_info "初始化数据库..."
    cd "$PROJECT_DIR/backend"

    # 等待 MySQL 完全启动
    sleep 5

    # 执行初始化脚本（如果有）
    if [ -f "scripts/init_db.py" ]; then
        python scripts/init_db.py || log_warn "数据库初始化失败，可手动执行"
    fi
}

# === 主流程 ===
main() {
    check_docker
    check_project
    create_directories
    setup_firewall
    start_services
    init_database
    verify_services

    echo ""
    echo "=========================================="
    echo -e "${GREEN}  部署完成!${NC}"
    echo "=========================================="
    echo ""
    echo "服务地址:"
    echo "  - API 文档：http://$(curl -s ifconfig.me)/docs"
    echo "  - 健康检查：http://$(curl -s ifconfig.me)/health"
    echo ""
    echo "常用命令:"
    echo "  - 查看日志：docker compose logs -f app"
    echo "  - 重启服务：docker compose restart"
    echo "  - 停止服务：docker compose down"
    echo "  - 更新代码：cd $PROJECT_DIR && git pull && docker compose up -d"
    echo ""
}

# 执行主流程
main
