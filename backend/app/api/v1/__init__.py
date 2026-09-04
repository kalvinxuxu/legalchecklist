"""
API 路由汇总
"""
from fastapi import APIRouter

from app.api.v1.endpoints import auth, contracts, contracts_stream, workspaces, legal_knowledge, documents, delivery

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["认证"])
api_router.include_router(workspaces.router, prefix="/workspaces", tags=["工作区"])
api_router.include_router(contracts.router, prefix="/contracts", tags=["合同"])
api_router.include_router(contracts_stream.router, prefix="/contracts", tags=["合同-流式"])
api_router.include_router(legal_knowledge.router, prefix="/knowledge", tags=["知识库"])
api_router.include_router(documents.router, prefix="/documents", tags=["文档摄取"])
api_router.include_router(delivery.router, prefix="/contracts", tags=["合同-交付"])
