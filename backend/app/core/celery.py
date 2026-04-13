"""
Celery 异步任务队列配置
"""
from celery import Celery
from app.core.config import settings

# Celery 配置（当 REDIS_URL 未配置时使用默认本地 Redis）
broker_url = getattr(settings, 'REDIS_URL', None) or "redis://localhost:6379/0"

# Celery 配置
celery_app = Celery(
    "legal_saas",
    broker=broker_url,
    backend=broker_url,
    include=["app.services.review.tasks"]
)

# Celery 配置优化
celery_app.conf.update(
    # 任务序列化
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",

    # 时区配置
    timezone="Asia/Shanghai",
    enable_utc=True,

    # 任务确认
    task_acks_late=True,
    task_reject_on_worker_or_lost=True,

    # 预取限制
    worker_prefetch_multiplier=1,

    # 任务超时
    task_soft_time_limit=300,  # 5 分钟软超时
    task_time_limit=600,       # 10 分钟硬超时

    # 重试配置
    task_default_retry_delay=60,
    task_max_retries=3,
)
