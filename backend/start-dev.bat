@echo off
REM 本地开发环境启动脚本（无需 Docker）

echo === 法务 AI SaaS 本地开发环境 ===
echo.

REM 1. 检查 .env 文件
if not exist ".env" (
    echo 创建 .env 文件...
    copy .env.example .env
    echo.
    echo ========================================
    echo 请编辑 .env 文件，填入你的 DeepSeek API Key:
    echo DEEPSEEK_API_KEY=sk-your-api-key-here
    echo ========================================
    echo.
    pause
)

REM 2. 创建虚拟环境（如果不存在）
if not exist "venv" (
    echo 创建 Python 虚拟环境...
    python -m venv venv
)

REM 3. 激活虚拟环境
echo 激活虚拟环境...
call venv\Scripts\activate.bat

REM 4. 安装依赖
echo 安装依赖...
pip install -r requirements.txt

REM 5. 初始化数据库
echo 初始化数据库...
python scripts\init_db.py

REM 6. 创建上传目录
if not exist "uploads" mkdir uploads

echo.
echo === 启动完成 ===
echo.
echo 启动后端服务...
uvicorn main:app --reload --host 0.0.0.0 --port 8000
