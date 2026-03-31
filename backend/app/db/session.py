"""
数据库会话管理
"""
import aiomysql
from typing import AsyncGenerator
from app.core.config import settings


class Database:
    def __init__(self):
        self.pool: aiomysql.Pool | None = None

    async def connect(self) -> None:
        """初始化数据库连接池"""
        self.pool = await aiomysql.create_pool(
            host=self._parse_host(settings.DATABASE_URL),
            port=3306,
            user=self._parse_user(settings.DATABASE_URL),
            password=self._parse_password(settings.DATABASE_URL),
            db=self._parse_database(settings.DATABASE_URL),
            autocommit=True,
            cursorclass=aiomysql.DictCursor,
        )
        print("Database connected")

    async def disconnect(self) -> None:
        """关闭连接池"""
        if self.pool:
            self.pool.close()
            await self.pool.wait_closed()
            print("Database disconnected")

    async def get_connection(self) -> aiomysql.Connection:
        """获取数据库连接"""
        return await self.pool.acquire()

    async def release_connection(self, conn: aiomysql.Connection) -> None:
        """释放数据库连接"""
        self.pool.release(conn)

    def _parse_host(self, url: str) -> str:
        # mysql://user:pass@host:port/db
        from urllib.parse import urlparse
        parsed = urlparse(url)
        return parsed.hostname or "localhost"

    def _parse_user(self, url: str) -> str:
        from urllib.parse import urlparse
        parsed = urlparse(url)
        return parsed.username or "root"

    def _parse_password(self, url: str) -> str:
        from urllib.parse import urlparse
        parsed = urlparse(url)
        return parsed.password or ""

    def _parse_database(self, url: str) -> str:
        from urllib.parse import urlparse
        parsed = urlparse(url)
        return parsed.path.lstrip("/") or "legal_saas"


# 全局数据库实例
db = Database()


async def get_db() -> AsyncGenerator[aiomysql.Connection, None]:
    """依赖注入：获取数据库连接"""
    conn = await db.get_connection()
    try:
        yield conn
    finally:
        await db.release_connection(conn)
