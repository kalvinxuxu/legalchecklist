"""
应用配置管理
"""
from pydantic_settings import BaseSettings
from typing import List
import os


class Settings(BaseSettings):
    # 环境
    ENVIRONMENT: str = "development"

    # 数据库
    DATABASE_URL: str

    # Redis
    REDIS_URL: str

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

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
