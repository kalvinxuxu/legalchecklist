@echo off
REM 快速启动脚本（Windows）

echo === 法务 AI SaaS 本地启动脚本 ===
echo.

REM 1. 检查 .env 文件
if not exist "backend\.env" (
    echo 创建 backend\.env 文件...
    copy "backend\.env.example" "backend\.env"
    echo.
    echo 请编辑 backend\.env 文件，填入你的 DeepSeek API Key
    echo 按任意键继续...
    pause >nul
)

REM 2. 创建必要目录
if not exist "uploads" mkdir uploads
if not exist "logs" mkdir logs

REM 3. 启动 Docker Compose
echo 启动 Docker 服务...
cd docker
docker compose up -d

echo.
echo === 启动完成 ===
echo.
echo 服务地址:
echo - API 文档：http://localhost/docs
echo - 前端开发：cd .. ^&^& cd frontend ^&^& npm install ^&^& npm run dev
echo.
echo 查看日志：docker compose logs -f app
echo 停止服务：docker compose down
echo.
