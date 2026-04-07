"""
数据库初始化脚本
"""
import asyncio
import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.config import settings
from app.db.session import db


async def init_db():
    """初始化数据库"""
    print(f"初始化数据库 ({settings.DATABASE_TYPE})...")

    # 连接数据库
    db.connect()

    # 创建所有表
    print("创建数据表...")
    await db.create_all_tables()

    print("数据库初始化完成!")
    print(f"数据库类型：{settings.DATABASE_TYPE}")
    if settings.is_mysql:
        print(f"数据库连接：{settings.DATABASE_URL}")
    else:
        print(f"SQLite 路径：{settings.sqlite_path}")


async def reset_db():
    """重置数据库（删除所有表后重新创建）"""
    print("警告：即将删除所有数据表！")
    confirm = input("确认重置？(yes/no): ")
    if confirm.lower() != "yes":
        print("已取消")
        return

    db.connect()

    print("删除所有表...")
    await db.drop_all_tables()

    print("重新创建表...")
    await db.create_all_tables()

    print("数据库重置完成!")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "reset":
        asyncio.run(reset_db())
    else:
        asyncio.run(init_db())
