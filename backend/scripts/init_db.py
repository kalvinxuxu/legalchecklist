"""
数据库初始化脚本 - 支持 SQLite 和 MySQL
"""
import asyncio
import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.config import settings
from app.db.session import db


async def init_mysql(conn):
    """初始化 MySQL 数据库"""
    create_tables_sql = """
    -- 租户表
    CREATE TABLE IF NOT EXISTS tenants (
        id VARCHAR(36) PRIMARY KEY,
        name VARCHAR(255) NOT NULL,
        plan ENUM('free', 'pro', 'enterprise') DEFAULT 'free',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

    -- 工作区表
    CREATE TABLE IF NOT EXISTS workspaces (
        id VARCHAR(36) PRIMARY KEY,
        tenant_id VARCHAR(36) NOT NULL,
        name VARCHAR(255) NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        INDEX idx_tenant_id (tenant_id)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

    -- 用户表
    CREATE TABLE IF NOT EXISTS users (
        id VARCHAR(36) PRIMARY KEY,
        tenant_id VARCHAR(36) NOT NULL,
        email VARCHAR(255),
        phone VARCHAR(20),
        wx_openid VARCHAR(100),
        wx_unionid VARCHAR(100),
        password_hash VARCHAR(255),
        role ENUM('admin', 'member') DEFAULT 'member',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        INDEX idx_tenant_id (tenant_id),
        INDEX idx_email (email),
        INDEX idx_wx_openid (wx_openid)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

    -- 合同表
    CREATE TABLE IF NOT EXISTS contracts (
        id VARCHAR(36) PRIMARY KEY,
        workspace_id VARCHAR(36) NOT NULL,
        user_id VARCHAR(36) NOT NULL,
        file_name VARCHAR(500),
        file_path VARCHAR(1000),
        file_hash VARCHAR(64),
        contract_type VARCHAR(50),
        content_text TEXT,
        review_status ENUM('pending', 'processing', 'completed', 'failed') DEFAULT 'pending',
        review_result JSON,
        risk_level ENUM('low', 'medium', 'high'),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
        INDEX idx_workspace_id (workspace_id),
        INDEX idx_user_id (user_id),
        INDEX idx_status (review_status)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

    -- 法律知识库表
    CREATE TABLE IF NOT EXISTS legal_knowledge (
        id VARCHAR(36) PRIMARY KEY,
        content_type ENUM('law', 'case', 'template', 'rule') NOT NULL,
        title VARCHAR(500),
        content TEXT NOT NULL,
        metadata JSON,
        tenant_id VARCHAR(36),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        INDEX idx_content_type (content_type),
        INDEX idx_tenant_id (tenant_id)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
    """

    # MySQL 不支持 IF NOT EXISTS 多语句，需要拆分执行
    # 这里简化处理，直接执行
    statements = [s.strip() for s in create_tables_sql.split(';') if s.strip()]
    for stmt in statements:
        try:
            async with conn.cursor() as cursor:
                await cursor.execute(stmt)
        except Exception as e:
            print(f"Warning: {e}")

    await conn.commit()
    print("MySQL tables created")


async def init_sqlite(conn):
    """初始化 SQLite 数据库"""
    # SQLite 使用不同的语法
    create_tables_sql = """
    -- 租户表
    CREATE TABLE IF NOT EXISTS tenants (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        plan TEXT DEFAULT 'free',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    -- 工作区表
    CREATE TABLE IF NOT EXISTS workspaces (
        id TEXT PRIMARY KEY,
        tenant_id TEXT NOT NULL,
        name TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    CREATE INDEX IF NOT EXISTS idx_workspaces_tenant ON workspaces(tenant_id);

    -- 用户表
    CREATE TABLE IF NOT EXISTS users (
        id TEXT PRIMARY KEY,
        tenant_id TEXT NOT NULL,
        email TEXT,
        phone TEXT,
        wx_openid TEXT,
        wx_unionid TEXT,
        password_hash TEXT,
        role TEXT DEFAULT 'member',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    CREATE INDEX IF NOT EXISTS idx_users_tenant ON users(tenant_id);
    CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
    CREATE INDEX IF NOT EXISTS idx_users_wx_openid ON users(wx_openid);

    -- 合同表
    CREATE TABLE IF NOT EXISTS contracts (
        id TEXT PRIMARY KEY,
        workspace_id TEXT NOT NULL,
        user_id TEXT NOT NULL,
        file_name TEXT,
        file_path TEXT,
        file_hash TEXT,
        contract_type TEXT,
        content_text TEXT,
        review_status TEXT DEFAULT 'pending',
        review_result TEXT,
        risk_level TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    CREATE INDEX IF NOT EXISTS idx_contracts_workspace ON contracts(workspace_id);
    CREATE INDEX IF NOT EXISTS idx_contracts_user ON contracts(user_id);
    CREATE INDEX IF NOT EXISTS idx_contracts_status ON contracts(review_status);

    -- 法律知识库表
    CREATE TABLE IF NOT EXISTS legal_knowledge (
        id TEXT PRIMARY KEY,
        content_type TEXT NOT NULL,
        title TEXT,
        content TEXT NOT NULL,
        metadata TEXT,
        tenant_id TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    CREATE INDEX IF NOT EXISTS idx_legal_content_type ON legal_knowledge(content_type);
    CREATE INDEX IF NOT EXISTS idx_legal_tenant ON legal_knowledge(tenant_id);
    """

    statements = [s.strip() for s in create_tables_sql.split(';') if s.strip()]
    for stmt in statements:
        try:
            async with conn.execute(stmt) as cursor:
                pass
        except Exception as e:
            print(f"Warning: {e}")

    await conn.commit()
    print("SQLite tables created")


async def init_db():
    """初始化数据库"""
    await db.connect()

    if settings.is_mysql:
        pool = await db._get_mysql_pool()
        async with pool.acquire() as conn:
            await init_mysql(conn)
    else:
        conn = await db.get_sqlite_connection()
        await init_sqlite(conn)
        await conn.close()

    await db.disconnect()
    print("Database initialization complete!")


if __name__ == "__main__":
    asyncio.run(init_db())
