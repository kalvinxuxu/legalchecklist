"""
应用配置管理
"""
from pydantic import field_validator
from pydantic_settings import BaseSettings
from typing import List, Optional
import os
from pathlib import Path

# 获取 backend 目录的绝对路径
BACKEND_DIR = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    # ========== 环境 ==========
    ENVIRONMENT: str = "development"  # development / production

    # ========== 数据库 ==========
    DATABASE_TYPE: str = "postgresql"
    DATABASE_URL: Optional[str] = None  # MySQL/PostgreSQL 连接字符串
    SQLITE_PATH: Optional[str] = None  # SQLite 数据库路径

    # ========== 向量数据库（Chroma）==========
    EMBEDDING_DIMENSION: int = 1024  # 智谱 embedding-2 维度
    CHROMA_PERSIST_DIR: str = os.getenv("CHROMA_PERSIST_DIR", "/app/data/chroma")
    VECTOR_STORE: str = "pgvector"  # pgvector / chroma

    # ========== 智谱 AI Embedding ==========
    ZHIPU_EMBEDDING_API_KEY: Optional[str] = None
    ZHIPU_EMBEDDING_MODEL: str = "embedding-2"
    ZHIPU_EMBEDDING_BASE_URL: str = "https://open.bigmodel.cn/api/paas/v4"

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

    # ========== 统一文档摄取 ==========
    DOCUMENT_AST_ENABLED: bool = True
    DOCLING_ENABLED: bool = False
    MINERU_ENABLED: bool = False
    LINUX_OCR_ENABLED: bool = False
    DOCUMENT_PARSE_QUALITY_THRESHOLD: float = 0.75
    OCR_LANGUAGES: str = "chi_sim+eng"
    RAG_HYBRID_ENABLED: bool = True
    RAG_BM25_CANDIDATE_K: int = 20
    RAG_VECTOR_CANDIDATE_K: int = 20
    RAG_RRF_K: int = 60
    RAG_RERANK_TOP_K: int = 8
    RAG_RERANKER_PROVIDER: str = "bge_local"
    RAG_RERANKER_MODEL: str = "BAAI/bge-reranker-v2-m3"
    RAG_RERANKER_TIMEOUT_SECONDS: float = 8.0
    RAG_RERANKER_BATCH_SIZE: int = 8
    RAG_RERANKER_CANDIDATE_K: int = 40
    RAG_CONTRACT_CANDIDATE_K: int = 12
    RAG_CONTRACT_TOP_K: int = 8
    RAG_CHUNK_MAX_CHARS: int = 1800
    RAG_CHUNK_OVERLAP_CHARS: int = 200
    RAG_CHUNK_TARGET_TOKENS: int = 700
    RAG_CHUNK_MAX_TOKENS: int = 1200
    RAG_CHUNK_OVERLAP_TOKENS: int = 100
    RAG_SEMANTIC_CHUNKING_ENABLED: bool = False
    RAG_SEMANTIC_BOUNDARY_THRESHOLD: float = 0.35
    EMBEDDING_PROVIDER: str = "zhipu"  # zhipu / local
    EMBEDDING_MODEL_VERSION: str = "v1"
    EMBEDDING_NORMALIZE: bool = True
    LOCAL_EMBEDDING_MODEL: str = "BAAI/bge-m3"
    RAG_RERANKER_CACHE_DIR: Optional[str] = None
    RAG_RERANKER_SCORE_NORMALIZATION: str = "sigmoid"
    JINA_API_KEY: Optional[str] = None
    JINA_RERANKER_MODEL: str = "jina-reranker-v2-base-multilingual"
    JINA_BASE_URL: str = "https://api.jina.ai/v1/rerank"
    MAIL_PROVIDER: str = "mock"  # mock / qq_imap
    QQ_IMAP_HOST: str = "imap.qq.com"
    QQ_IMAP_PORT: int = 993
    # 兼容现有本地/部署环境中的通用邮件变量。
    QQ_MAIL_USERNAME: Optional[str] = os.getenv("QQ_MAIL_USERNAME") or os.getenv("MAIL_USER")
    QQ_MAIL_APP_PASSWORD: Optional[str] = os.getenv("QQ_MAIL_APP_PASSWORD") or os.getenv("MAIL_PASSWORD")
    QQ_MAIL_DRAFTS_FOLDER: str = "草稿箱"
    RAG_FTS_LANGUAGE: str = "simple"
    RAG_P95_LATENCY_MS: int = 1200

    # ========== 文件存储 ==========
    # 本地存储（开发环境或 Railway 持久化卷）
    # 生产环境可切换到 S3/R2/OSS
    STORAGE_TYPE: str = "local"  # local / s3 / r2 / oss
    # Railway 中建议挂载 Volume 到 /app/data
    STORAGE_PATH: str = os.getenv("STORAGE_PATH", "/app/data/uploads")

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

    @field_validator(
        "JWT_SECRET",
        "ZHIPU_EMBEDDING_API_KEY",
        "DEEPSEEK_API_KEY",
        "MINIMAX_API_KEY",
        "JINA_API_KEY",
        "QQ_MAIL_USERNAME",
        "QQ_MAIL_APP_PASSWORD",
        mode="before",
    )
    @classmethod
    def strip_secret_whitespace(cls, value):
        """Prevent pasted Railway secrets from introducing invalid header characters."""
        return value.strip() if isinstance(value, str) else value

    @property
    def is_mysql(self) -> bool:
        return self.DATABASE_TYPE == "mysql"

    @property
    def is_postgresql(self) -> bool:
        return self.DATABASE_TYPE == "postgresql"

    def require_postgresql(self) -> None:
        """Fail fast: durable review cannot run without PostgreSQL."""
        if not self.is_postgresql:
            raise RuntimeError("PostgreSQL is required; set DATABASE_TYPE=postgresql")
        if not self.DATABASE_URL:
            raise RuntimeError("PostgreSQL is required; set DATABASE_URL")

    @property
    def is_sqlite(self) -> bool:
        return self.DATABASE_TYPE == "sqlite"

    @property
    def database_url(self) -> str:
        """Get database URL based on type"""
        if self.DATABASE_URL:
            # Railway/PostgreSQL 可能注入 postgres://，SQLAlchemy async driver 需要转换。
            url = self.DATABASE_URL
            if url.startswith("postgres://"):
                url = url.replace("postgres://", "postgresql+asyncpg://", 1)
            return url
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
        # 本地开发使用 .env；Railway 生产环境直接注入环境变量。
        env_file = str(BACKEND_DIR / ".env")
        case_sensitive = True
        extra = "ignore"  # 允许 .env 中存在未定义的字段


settings = Settings()
