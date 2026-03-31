"""
应用配置管理
"""
from pydantic_settings import BaseSettings
from typing import List, Optional
import os


class Settings(BaseSettings):
    # 环境
    ENVIRONMENT: str = "development"

    # 数据库 - 支持 MySQL 和 SQLite
    DATABASE_TYPE: str = "mysql"  # mysql 或 sqlite
    DATABASE_URL: Optional[str] = None  # MySQL 连接字符串
    SQLITE_PATH: str = "./legal_saas.db"  # SQLite 数据库路径

    # Redis（仅生产环境需要）
    REDIS_URL: Optional[str] = None

    # JWT
    JWT_SECRET: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440

    # DeepSeek API
    DEEPSEEK_API_KEY: str
    DEEPSEEK_BASE_URL: str = "https://api.deepseek.com"
    DEEPSEEK_MODEL: str = "deepseek-chat"
    DEEPSEEK_EMBEDDING_MODEL: str = "deepseek-embedding"

    # 文件存储
    STORAGE_TYPE: str = "local"
    STORAGE_PATH: str = "./uploads"

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

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
