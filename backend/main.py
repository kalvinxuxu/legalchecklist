"""
后端应用入口
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.api.v1 import api_router


def create_app() -> FastAPI:
    app = FastAPI(
        title="法务 AI SaaS API",
        description="面向中小企业的轻量化合同审查服务",
        version="0.1.0",
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

    @app.get("/health")
    async def health_check():
        return {"status": "healthy"}

    return app


app = create_app()
