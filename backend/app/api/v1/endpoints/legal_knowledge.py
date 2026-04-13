"""
法律知识库 API

管理法律知识、公司政策等，供 RAG 检索使用
"""
import asyncio
import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.db.session import get_db
from app.models.legal_knowledge import LegalKnowledge
from app.models.user import User as UserModel
from app.services.rag.retriever import retriever
from app.services.document.parser import document_parser
from app.core.config import settings
from app.api.v1.endpoints.auth import get_current_user

router = APIRouter()


@router.get("/types")
async def get_content_types():
    """
    获取支持的内容类型

    Returns:
        支持的类型列表
    """
    return {
        "types": [
            {"value": "law", "label": "法律法规", "description": "法律条文、司法解释等"},
            {"value": "case", "label": "典型案例", "description": "法院判例、案例分析等"},
            {"value": "template", "label": "合同模板", "description": "标准合同模板、条款范本等"},
            {"value": "rule", "label": "审查规则", "description": "审查标准、注意事项等"},
            {"value": "company_policy", "label": "公司政策", "description": "企业内部规章制度、政策文件等"},
        ]
    }


@router.post("")
async def create_knowledge(
    title: str = Form(...),
    content: str = Form(...),
    content_type: str = Form(...),
    metadata: Optional[str] = Form(None),
    current_user: UserModel = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    创建知识条目

    支持手动录入知识内容
    """
    # 验证内容类型
    valid_types = ["law", "case", "template", "rule", "company_policy"]
    if content_type not in valid_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"无效的内容类型，支持的类型: {valid_types}"
        )

    # 解析 metadata
    import json
    metadata_dict = {}
    if metadata:
        try:
            metadata_dict = json.loads(metadata)
        except json.JSONDecodeError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="metadata 必须是有效的 JSON 格式"
            )

    # 创建知识条目
    knowledge_id = await retriever.add_knowledge(
        title=title,
        content=content,
        content_type=content_type,
        metadata=metadata_dict,
        tenant_id=current_user.tenant_id
    )

    return {"id": knowledge_id, "message": "创建成功"}


@router.post("/upload")
async def upload_knowledge(
    file: UploadFile = File(...),
    content_type: str = Form(...),
    title: Optional[str] = Form(None),
    current_user: UserModel = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    上传文档并提取知识

    支持 PDF 和 Word 格式，自动解析文本内容
    """
    # 验证文件类型
    file_extension = file.filename.split(".")[-1].lower() if "." in file.filename else ""
    allowed_extensions = ["pdf", "docx"]
    if file_extension not in allowed_extensions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="不支持的文件格式，请上传 .pdf 或 .docx 格式"
        )

    # 验证内容类型
    valid_types = ["law", "case", "template", "rule", "company_policy"]
    if content_type not in valid_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"无效的内容类型，支持的类型: {valid_types}"
        )

    # 读取文件
    file_bytes = await file.read()

    # 解析文档
    if file_extension == "pdf":
        import tempfile
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            tmp.write(file_bytes)
            tmp_path = tmp.name
        parse_result = await document_parser.parse_pdf(tmp_path)
        content = parse_result.get("text", "")
    else:
        import tempfile
        with tempfile.NamedTemporaryFile(suffix=".docx", delete=False) as tmp:
            tmp.write(file_bytes)
            tmp_path = tmp.name
        parse_result = await document_parser.parse_word(tmp_path)
        content = parse_result.get("text", "")

    # 使用文件名作为标题（如果没有提供）
    if not title:
        title = file.filename.rsplit(".", 1)[0]

    # 创建知识条目
    import json
    metadata_dict = {
        "source_file": file.filename,
        "parse_status": "success" if content else "failed"
    }

    knowledge_id = await retriever.add_knowledge(
        title=title,
        content=content,
        content_type=content_type,
        metadata=metadata_dict,
        tenant_id=current_user.tenant_id
    )

    return {
        "id": knowledge_id,
        "title": title,
        "content_length": len(content),
        "message": "上传成功"
    }


@router.get("")
async def list_knowledge(
    content_type: Optional[str] = None,
    search: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    current_user: UserModel = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取知识列表

    支持按类型筛选和关键词搜索
    """
    # 构建查询
    conditions = []
    if content_type:
        conditions.append(LegalKnowledge.content_type == content_type)

    # 搜索（标题或内容）
    if search:
        from sqlalchemy import or_
        conditions.append(
            or_(
                LegalKnowledge.title.ilike(f"%{search}%"),
                LegalKnowledge.content.ilike(f"%{search}%")
            )
        )

    # 租户隔离（只看自己的）
    conditions.append(
        (LegalKnowledge.tenant_id == current_user.tenant_id) |
        (LegalKnowledge.tenant_id.is_(None))
    )

    # 查询总数
    count_query = select(func.count(LegalKnowledge.id)).where(*conditions)
    total_result = await db.execute(count_query)
    total = total_result.scalar()

    # 查询列表
    query = (
        select(LegalKnowledge)
        .where(*conditions)
        .order_by(LegalKnowledge.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    result = await db.execute(query)
    items = result.scalars().all()

    return {
        "total": total,
        "items": [
            {
                "id": item.id,
                "title": item.title,
                "content": item.content[:200] + "..." if len(item.content) > 200 else item.content,
                "content_type": item.content_type,
                "tenant_id": item.tenant_id,
                "is_public": item.tenant_id is None,
                "metadata": item.metadata_json,
                "created_at": item.created_at.isoformat() if item.created_at else None,
                "updated_at": item.updated_at.isoformat() if item.updated_at else None,
            }
            for item in items
        ]
    }


@router.get("/{knowledge_id}")
async def get_knowledge(
    knowledge_id: str,
    current_user: UserModel = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取知识详情
    """
    result = await db.execute(
        select(LegalKnowledge).where(LegalKnowledge.id == knowledge_id)
    )
    item = result.scalar_one_or_none()

    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="知识条目不存在"
        )

    # 检查权限
    if item.tenant_id and item.tenant_id != current_user.tenant_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权访问该知识"
        )

    return {
        "id": item.id,
        "title": item.title,
        "content": item.content,
        "content_type": item.content_type,
        "tenant_id": item.tenant_id,
        "is_public": item.tenant_id is None,
        "metadata": item.metadata_json,
        "created_at": item.created_at.isoformat() if item.created_at else None,
        "updated_at": item.updated_at.isoformat() if item.updated_at else None,
    }


@router.put("/{knowledge_id}")
async def update_knowledge(
    knowledge_id: str,
    title: str = Form(...),
    content: str = Form(...),
    content_type: str = Form(...),
    metadata: Optional[str] = Form(None),
    current_user: UserModel = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    更新知识条目
    """
    result = await db.execute(
        select(LegalKnowledge).where(LegalKnowledge.id == knowledge_id)
    )
    item = result.scalar_one_or_none()

    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="知识条目不存在"
        )

    # 检查权限（只能修改自己的）
    if item.tenant_id != current_user.tenant_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权修改该知识"
        )

    # 更新字段
    item.title = title
    item.content = content
    item.content_type = content_type

    import json
    if metadata:
        try:
            item.metadata_json = json.loads(metadata)
        except json.JSONDecodeError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="metadata 必须是有效的 JSON 格式"
            )

    await db.commit()

    return {"message": "更新成功"}


@router.delete("/{knowledge_id}")
async def delete_knowledge(
    knowledge_id: str,
    current_user: UserModel = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    删除知识条目
    """
    result = await db.execute(
        select(LegalKnowledge).where(LegalKnowledge.id == knowledge_id)
    )
    item = result.scalar_one_or_none()

    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="知识条目不存在"
        )

    # 检查权限（只能删除自己的）
    if item.tenant_id != current_user.tenant_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权删除该知识"
        )

    # TODO: 同时从 Chroma 中删除向量

    await db.delete(item)
    await db.commit()

    return {"message": "删除成功"}

