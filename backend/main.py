"""
后端应用入口
"""
import logging
import traceback
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from pathlib import Path
from sqlalchemy import select

from app.core.config import settings
from app.api.v1 import api_router
from app.db.session import db
from app.models.contract import Contract, ReviewStatus as ReviewStatusEnum
from app.models.review_run import ReviewRun

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时连接数据库并创建表
    settings.require_postgresql()
    db.connect()
    logger.info("Database connected. Type: PostgreSQL")
    # 开发环境或 PostgreSQL 生产环境自动创建表
    if settings.ENVIRONMENT == "development" or not settings.is_sqlite:
        logger.info("Creating database tables...")
        # PostgreSQL 环境先尝试修复不完整的表结构
        if settings.is_postgresql:
            await fix_postgres_schema()
        await db.create_all_tables()
        await recover_legacy_processing_contracts()
        logger.info("Database tables created/verified")
    yield
    # 关闭时断开数据库连接
    await db.disconnect()


async def fix_postgres_schema():
    """修复早期 PostgreSQL 表结构问题。"""
    try:
        from sqlalchemy import text
        async with db.engine.connect() as conn:
            # create_all 不会修改已有表；这些字段需要兼容旧 Docker volume。
            await conn.execute(text(
                "ALTER TABLE contracts ADD COLUMN IF NOT EXISTS review_config JSONB"
            ))
            await conn.commit()
            # 检查 users 表是否有 name 列
            result = await conn.execute(text("""
                SELECT column_name FROM information_schema.columns
                WHERE table_name = 'users' AND column_name = 'name'
            """))
            has_name_column = result.fetchone() is not None

            if not has_name_column:
                logger.warning("PostgreSQL: users table missing 'name' column, adding it...")
                # 检查 tenants 表是否存在
                result = await conn.execute(text("""
                    SELECT table_name FROM information_schema.tables
                    WHERE table_name = 'tenants'
                """))
                tenants_exists = result.fetchone() is not None

                if not tenants_exists:
                    # 表结构完全不完整，需要重建
                    logger.warning("PostgreSQL: tables are incomplete, will recreate...")
                    await conn.execute(text("DROP TABLE IF EXISTS users CASCADE"))
                    await conn.execute(text("DROP TABLE IF EXISTS workspaces CASCADE"))
                    await conn.execute(text("DROP TABLE IF EXISTS contracts CASCADE"))
                    await conn.execute(text("DROP TABLE IF EXISTS legal_knowledge CASCADE"))
                    await conn.execute(text("DROP TABLE IF EXISTS tenants CASCADE"))
                    await conn.execute(text("DROP TABLE IF EXISTS contract_understandings CASCADE"))
                    await conn.execute(text("DROP TABLE IF EXISTS clause_locations CASCADE"))
                    await conn.commit()
                    logger.info("PostgreSQL: dropped incomplete tables, will recreate...")
                else:
                    #  tenants 存在，只是 users 缺少 name 列
                    await conn.execute(text("ALTER TABLE users ADD COLUMN name VARCHAR(100)"))
                    await conn.commit()
                    logger.info("PostgreSQL: added 'name' column to users table")
    except Exception as e:
        logger.error(f"PostgreSQL schema fix failed: {e}")


async def recover_legacy_processing_contracts():
    """Mark pre-checkpoint processing jobs as recoverable instead of hiding them."""
    async with db.async_session_maker() as session:
        result = await session.execute(
            select(Contract).where(Contract.review_status == ReviewStatusEnum.processing)
        )
        changed = 0
        for contract in result.scalars().all():
            run_result = await session.execute(
                select(ReviewRun.id).where(ReviewRun.contract_id == contract.id).limit(1)
            )
            if run_result.scalar_one_or_none() is None:
                contract.review_status = ReviewStatusEnum.failed
                contract.review_error = "旧版审查任务已中断，请点击从断点继续重新执行"
                changed += 1
        if changed:
            await session.commit()
            logger.warning("Recovered %s legacy processing contracts", changed)


def create_app() -> FastAPI:
    app = FastAPI(
        title="法务 AI SaaS API",
        description="面向中小企业的轻量化合同审查服务",
        version="0.1.0",
        lifespan=lifespan,
    )

    # 全局异常处理器
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        """捕获所有未处理的异常并记录详细错误"""
        logger.error(f"Unhandled exception on {request.method} {request.url}: {exc}\n{traceback.format_exc()}")
        return JSONResponse(
            status_code=500,
            content={"detail": "服务器内部错误，请稍后重试"}
        )

    # CORS 配置
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # 注册路由
    app.include_router(api_router, prefix="/api/v1")

    # 健康检查端点（必须在静态文件路由之前）
    @app.get("/health")
    async def health_check():
        return {"status": "healthy"}

    # 服务前端静态文件（生产环境）
    static_path = Path("/app/static")
    if static_path.exists():
        # 挂载静态资源目录
        if (static_path / "assets").exists():
            app.mount("/assets", StaticFiles(directory=str(static_path / "assets")), name="assets")
        if (static_path / "fonts").exists():
            app.mount("/fonts", StaticFiles(directory=str(static_path / "fonts")), name="fonts")

        @app.get("/")
        async def serve_root():
            """Serve frontend index.html for root path"""
            index_path = static_path / "index.html"
            if index_path.exists():
                return FileResponse(index_path)
            return {"status": "frontend not built"}

        @app.get("/{full_path:path}")
        async def serve_frontend(full_path: str):
            """Serve frontend SPA for all non-API routes"""
            # 排除 API 和文档
            if full_path.startswith(("docs", "redoc", "openapi.json")):
                return FileResponse(str(static_path / "index.html"))
            index_path = static_path / "index.html"
            if index_path.exists():
                return FileResponse(index_path)
            return {"status": "frontend not built"}

    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
