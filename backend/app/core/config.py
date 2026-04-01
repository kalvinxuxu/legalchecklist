"""
应用配置管理
"""
from pydantic_settings import BaseSettings
from typing import List, Optional
import os
from pathlib import Path

# 获取 backend 目录的绝对路径
BACKEND_DIR = Path(__file__).resolve().parent.parent.parent

class Settings(BaseSettings):
    # 环境
    ENVIRONMENT: str = "development"

    # 数据库 - 支持 MySQL 和 SQLite
    DATABASE_TYPE: str = "mysql"  # mysql 或 sqlite
    DATABASE_URL: Optional[str] = None  # MySQL 连接字符串
    SQLITE_PATH: Optional[str] = None  # SQLite 数据库路径
    _sqlite_path_default: str = str(Path(__file__).resolve().parent.parent.parent / "legal_saas_new.db")

    # Redis（仅生产环境需要）
    REDIS_URL: Optional[str] = None  # Redis 连接 URL，用于 Celery 消息队列

    # Celery 配置
    USE_CELERY: bool = False  # 是否启用 Celery 异步任务队列

    # JWT
    JWT_SECRET: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440

    # 智谱 AI API
    ZHIPU_API_KEY: Optional[str] = None
    ZHIPU_BASE_URL: str = "https://open.bigmodel.cn/api/paas/v4"
    ZHIPU_MODEL: str = "glm-4"
    ZHIPU_EMBEDDING_MODEL: str = "embedding-2"

    # DeepSeek API（备用）
    DEEPSEEK_API_KEY: Optional[str] = None
    DEEPSEEK_BASE_URL: str = "https://api.deepseek.com"
    DEEPSEEK_MODEL: str = "deepseek-chat"
    DEEPSEEK_EMBEDDING_MODEL: str = "deepseek-embedding"

    # 阿里云 OSS
    ALIYUN_ACCESS_KEY_ID: Optional[str] = None
    ALIYUN_ACCESS_KEY_SECRET: Optional[str] = None
    ALIYUN_OSS_BUCKET: str = "legal-saas"
    ALIYUN_OSS_ENDPOINT: str = "oss-cn-hangzhou.aliyuncs.com"

    # 文件存储
    STORAGE_TYPE: str = "local"
    STORAGE_PATH: str = str(BACKEND_DIR / "uploads")

    # CORS
    CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
    ]

    @property
    def is_mysql(self) -> bool:
        return self.DATABASE_TYPE == "mysql"

    @property
    def is_sqlite(self) -> bool:
        return self.DATABASE_TYPE == "sqlite"

    @property
    def sqlite_path(self) -> str:
        """Get SQLite path, defaulting to backend dir if not set"""
        if self.SQLITE_PATH:
            return self.SQLITE_PATH
        # 使用 new.db 文件，因为旧的 legal_saas.db 可能被锁定
        return str(BACKEND_DIR / "legal_saas_new.db")

    class Config:
        env_file = str(BACKEND_DIR / ".env")
        case_sensitive = True


settings = Settings()
