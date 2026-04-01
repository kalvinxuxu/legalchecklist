"""
Celery Worker 启动脚本

使用方法:
    python celery_worker.py

开发环境（不使用 Celery）:
    后端服务会自动使用 asyncio 后台任务

生产环境（使用 Celery）:
    1. 确保 Redis 运行中
    2. 设置 USE_CELERY=true 在 .env 文件中
    3. 运行此脚本启动 Celery Worker
"""
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.celery import celery_app

if __name__ == "__main__":
    print("Starting Celery Worker...")
    print("Broker: redis://localhost:6379/0")
    print("Press Ctrl+C to stop")

    # 启动 Celery Worker
    argv = [
        'worker',
        '--loglevel=info',
        '--timezone=Asia/Shanghai',
        '--concurrency=2',  # 默认 2 个并发 worker
    ]

    celery_app.start(argv)
