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
    # ========== 环境 ==========
    ENVIRONMENT: str = "development"  # development / production

    # ========== Celery（已弃用，使用 asyncio）==========
    USE_CELERY: bool = False  # 是否使用 Celery（默认使用 asyncio）

    # ========== 数据库 ==========
    DATABASE_TYPE: str = "sqlite"  # sqlite / mysql / postgresql
    DATABASE_URL: Optional[str] = None  # MySQL/PostgreSQL 连接字符串
    SQLITE_PATH: Optional[str] = None  # SQLite 数据库路径

    # ========== 向量维度（pgvector）==========
    EMBEDDING_DIMENSION: int = 1536  # DeepSeek embedding 维度

    # ========== JWT ==========
    JWT_SECRET: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24小时

    # ========== DeepSeek API (LLM) ==========
    DEEPSEEK_API_KEY: Optional[str] = None
    DEEPSEEK_BASE_URL: str = "https://api.deepseek.com"
    DEEPSEEK_MODEL: str = "deepseek-chat"  # deepseek-chat 或 deepseek-coder
    DEEPSEEK_EMBEDDING_MODEL: str = "deepseek-embedding"

    # ========== MiniMax API (视觉理解) ==========
    MINIMAX_API_KEY: Optional[str] = None  # 视觉理解用
    MINIMAX_VISION_MODEL: str = "MiniMax-VL-01"

    # ========== 文件存储 ==========
    # 本地存储（开发/ Fly.io）：使用 Fly Volumes 挂载点
    # 生产环境可切换到 S3/R2/OSS
    STORAGE_TYPE: str = "local"  # local / s3 / r2 / oss
    STORAGE_PATH: str = os.getenv("STORAGE_PATH", str(BACKEND_DIR / "uploads"))

    # S3 兼容存储（可选）
    S3_BUCKET: Optional[str] = None
    S3_ENDPOINT: Optional[str] = None
    S3_ACCESS_KEY: Optional[str] = None
    S3_SECRET_KEY: Optional[str] = None

    # 阿里云 OSS（已弃用，保留用于兼容）
    ALIYUN_ACCESS_KEY_ID: Optional[str] = None
    ALIYUN_ACCESS_KEY_SECRET: Optional[str] = None
    ALIYUN_OSS_BUCKET: Optional[str] = None
    ALIYUN_OSS_ENDPOINT: Optional[str] = None

    # ========== CORS ==========
    CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
    ]

    @property
    def is_mysql(self) -> bool:
        return self.DATABASE_TYPE == "mysql"

    @property
    def is_postgresql(self) -> bool:
        return self.DATABASE_TYPE == "postgresql"

    @property
    def is_sqlite(self) -> bool:
        return self.DATABASE_TYPE == "sqlite"

    @property
    def database_url(self) -> str:
        """Get database URL based on type"""
        if self.DATABASE_URL:
            return self.DATABASE_URL
        if self.is_sqlite:
            return f"sqlite+aiosqlite:///{self.sqlite_path}"
        return ""

    @property
    def sqlite_path(self) -> str:
        """Get SQLite path, defaulting to backend dir if not set"""
        if self.SQLITE_PATH:
            return self.SQLITE_PATH
        return str(BACKEND_DIR / "legal_saas.db")

    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT == "production"

    class Config:
        env_file = str(BACKEND_DIR / ".env")
        case_sensitive = True


settings = Settings()
