"""
后端应用入口
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pathlib import Path

from app.core.config import settings
from app.api.v1 import api_router
from app.db.session import db


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时连接数据库并创建表
    db.connect()
    # 开发环境或 SQLite 生产环境自动创建表
    if settings.ENVIRONMENT == "development" or (settings.is_sqlite and settings.sqlite_path.startswith("/")):
        await db.create_all_tables()
    yield
    # 关闭时断开数据库连接
    await db.disconnect()


def create_app() -> FastAPI:
    app = FastAPI(
        title="法务 AI SaaS API",
        description="面向中小企业的轻量化合同审查服务",
        version="0.1.0",
        lifespan=lifespan,
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

    @app.get("/health")
    async def health_check():
        return {"status": "healthy"}

    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
