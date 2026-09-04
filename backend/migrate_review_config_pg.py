"""
添加 review_config 字段到 contracts 表 (PostgreSQL版本)

用于 PostgreSQL 生产环境
"""
import asyncio
import os
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

DATABASE_URL = os.environ.get("DATABASE_URL")
if not DATABASE_URL:
    # Try to get from internal vault
    DATABASE_URL = "postgresql+asyncpg://"
    print("[ERROR] DATABASE_URL not set")
    exit(1)

async def migrate():
    engine = create_async_engine(DATABASE_URL, echo=False)
    async with engine.begin() as conn:
        # Check if column exists
        result = await conn.execute(
            text("SELECT column_name FROM information_schema.columns WHERE table_name = 'contracts' AND column_name = 'review_config'")
        )
        row = result.fetchone()
        if not row:
            await conn.execute(text('ALTER TABLE contracts ADD COLUMN review_config JSON'))
            print("[OK] review_config field added")
        else:
            print("[OK] review_config field already exists")
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(migrate())
