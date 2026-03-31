#!/bin/bash

# 初始化脚本：创建.env 文件并生成 JWT Secret

set -e

echo "=== 法务 AI SaaS 初始化脚本 ==="

# 1. 创建后端 .env 文件
if [ ! -f backend/.env ]; then
    echo "创建 backend/.env 文件..."
    cp backend/.env.example backend/.env

    # 生成随机 JWT Secret
    JWT_SECRET=$(openssl rand -hex 32)
    sed -i.bak "s/JWT_SECRET=.*/JWT_SECRET=$JWT_SECRET/" backend/.env
    rm backend/.env.bak 2>/dev/null || true

    echo "✓ .env 文件创建成功"
else
    echo "✓ .env 文件已存在"
fi

# 2. 创建必要的目录
echo "创建必要目录..."
mkdir -p uploads
mkdir -p logs
mkdir -p docker/ssl

echo "✓ 目录创建完成"

# 3. 提示用户编辑.env
echo ""
echo "=== 下一步操作 ==="
echo "1. 编辑 backend/.env 文件，填入你的 DeepSeek API Key"
echo "2. 运行：cd docker && docker compose up -d"
echo "3. 访问：http://localhost/docs 查看 API 文档"
echo ""
