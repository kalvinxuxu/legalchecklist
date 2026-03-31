"""
数据库会话管理 - 支持 MySQL 和 SQLite
"""
import aiomysql
import aiosqlite
from typing import AsyncGenerator, Union
from app.core.config import settings


class Database:
    """数据库连接管理器 - 支持 MySQL 和 SQLite"""

    def __init__(self):
        self.mysql_pool: aiomysql.Pool | None = None
        self.sqlite_path: str | None = None

    async def connect(self) -> None:
        """初始化数据库连接"""
        if settings.is_mysql:
            await self._connect_mysql()
        else:
            await self._connect_sqlite()
        print(f"Database connected ({settings.DATABASE_TYPE})")

    async def disconnect(self) -> None:
        """关闭数据库连接"""
        if self.mysql_pool:
            self.mysql_pool.close()
            await self.mysql_pool.wait_closed()
            print("MySQL disconnected")
        if self.sqlite_path:
            print("SQLite disconnected")

    async def get_mysql_connection(self) -> aiomysql.Connection:
        """获取 MySQL 连接"""
        return await self.mysql_pool.acquire()

    async def release_mysql_connection(self, conn: aiomysql.Connection) -> None:
        """释放 MySQL 连接"""
        self.mysql_pool.release(conn)

    async def get_sqlite_connection(self) -> aiosqlite.Connection:
        """获取 SQLite 连接"""
        return await aiosqlite.connect(self.sqlite_path)

    def _connect_mysql(self) -> None:
        """连接 MySQL"""
        from urllib.parse import urlparse

        parsed = urlparse(settings.DATABASE_URL)
        self.mysql_pool = None  # 延迟创建

    def _connect_sqlite(self) -> None:
        """连接 SQLite"""
        self.sqlite_path = settings.SQLITE_PATH

    def _parse_mysql_url(self, url: str) -> dict:
        """解析 MySQL URL"""
        from urllib.parse import urlparse
        parsed = urlparse(url)
        return {
            "host": parsed.hostname or "localhost",
            "port": parsed.port or 3306,
            "user": parsed.username or "root",
            "password": parsed.password or "",
            "db": parsed.path.lstrip("/") or "legal_saas",
        }

    async def _get_mysql_pool(self) -> aiomysql.Pool:
        """获取或创建 MySQL 连接池"""
        if self.mysql_pool is None:
            params = self._parse_mysql_url(settings.DATABASE_URL)
            self.mysql_pool = await aiomysql.create_pool(
                host=params["host"],
                port=params["port"],
                user=params["user"],
                password=params["password"],
                db=params["db"],
                autocommit=True,
                cursorclass=aiomysql.DictCursor,
            )
        return self.mysql_pool


# 全局数据库实例
db = Database()


async def get_db() -> AsyncGenerator[Union[aiomysql.Connection, aiosqlite.Connection], None]:
    """依赖注入：获取数据库连接"""
    if settings.is_mysql:
        pool = await db._get_mysql_pool()
        conn = await pool.acquire()
        try:
            yield conn
        finally:
            pool.release(conn)
    else:
        async with await db.get_sqlite_connection() as conn:
            yield conn
