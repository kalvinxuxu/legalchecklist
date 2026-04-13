"""
SQLAlchemy 异步会话管理 - 支持 MySQL、PostgreSQL 和 SQLite
"""
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import sessionmaker, declarative_base
from typing import AsyncGenerator
from app.core.config import settings


class Database:
    """数据库连接管理器"""

    def __init__(self):
        self.engine = None
        self.async_session_maker = None

    def connect(self) -> None:
        """初始化数据库引擎"""
        if settings.is_mysql:
            # MySQL 异步连接
            mysql_url = settings.DATABASE_URL
            # 转换为异步 URL
            if mysql_url.startswith("mysql://"):
                mysql_url = mysql_url.replace("mysql://", "mysql+aiomysql://", 1)
            elif mysql_url.startswith("mysql+pymysql://"):
                mysql_url = mysql_url.replace("mysql+pymysql://", "mysql+aiomysql://", 1)

            self.engine = create_async_engine(
                mysql_url,
                echo=settings.ENVIRONMENT == "development",
                pool_pre_ping=True,
                pool_size=10,
                max_overflow=20,
            )
        elif settings.is_postgresql:
            # PostgreSQL 异步连接
            postgres_url = settings.DATABASE_URL
            # 转换为异步 URL（postgresql+asyncpg://）
            if postgres_url.startswith("postgresql://"):
                postgres_url = postgres_url.replace("postgresql://", "postgresql+asyncpg://", 1)
            elif postgres_url.startswith("postgres://"):
                postgres_url = postgres_url.replace("postgres://", "postgresql+asyncpg://", 1)

            self.engine = create_async_engine(
                postgres_url,
                echo=settings.ENVIRONMENT == "development",
                pool_pre_ping=True,
                pool_size=10,
                max_overflow=20,
            )
        else:
            # SQLite 异步连接
            sqlite_path = settings.sqlite_path
            self.engine = create_async_engine(
                f"sqlite+aiosqlite:///{sqlite_path}",
                echo=settings.ENVIRONMENT == "development",
                connect_args={"check_same_thread": False, "timeout": 30},
            )

        self.async_session_maker = async_sessionmaker(
            self.engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autocommit=False,
            autoflush=False,
        )

    async def disconnect(self) -> None:
        """关闭数据库连接"""
        if self.engine:
            await self.engine.dispose()

    async def create_all_tables(self) -> None:
        """创建所有表"""
        from app.models.base import Base
        from app.models import Tenant, User, Workspace, Contract, LegalKnowledge, ContractUnderstanding, ClauseLocation  # noqa: F401

        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    async def drop_all_tables(self) -> None:
        """删除所有表（仅开发环境）"""
        from app.models.base import Base

        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)

    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """获取数据库会话"""
        async with self.async_session_maker() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()


# 全局数据库实例
db = Database()


async def get_db() -> AsyncGenerator:
    """依赖注入：获取数据库会话"""
    async for session in db.get_session():
        yield session
