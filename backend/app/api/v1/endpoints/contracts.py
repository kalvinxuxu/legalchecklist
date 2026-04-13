"""
合同管理 API

使用租户隔离中间件确保所有操作都在当前租户范围内。
"""
import asyncio
import uuid
import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.session import get_db, db
from app.schemas import ContractResponse, ContractCreate, ReviewStatus, ContractType
from app.api.v1.endpoints.auth import get_current_user
from app.middleware.tenant_isolation import verify_contract_access, verify_workspace_access
from app.models.contract import Contract, ContractType as ContractTypeEnum, ReviewStatus as ReviewStatusEnum
from app.models.workspace import Workspace
from app.models.user import User as UserModel
from app.core.config import settings
from app.services.document.parser import document_parser
from app.services.review import review_service

# Celery 任务导入（条件导入）
if settings.USE_CELERY:
    from app.services.review.tasks import process_contract_review_task

router = APIRouter()


# 创建一个独立的 security scheme 用于公开端点
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
optional_security = HTTPBearer(auto_error=False)


def resolve_contract_file_path(file_path: str) -> Path:
    """
    解析合同文件路径，支持相对路径和绝对路径

    相对路径：相对于 STORAGE_PATH
    绝对路径：直接使用
    """
    path_obj = Path(file_path)
    if path_obj.is_absolute():
        return path_obj

    # 检查是否已经包含 STORAGE_PATH（避免双重路径）
    normalized_path = path_obj.as_posix() if hasattr(path_obj, 'as_posix') else str(path_obj)
    storage_posix = Path(settings.STORAGE_PATH).as_posix()

    if normalized_path.startswith(storage_posix):
        # 路径已经包含 STORAGE_PATH，直接返回
        return path_obj

    return Path(settings.STORAGE_PATH) / file_path


@router.get("/test-llm", dependencies=[])
async def test_llm_connection():
    """
    测试 LLM API 连接（无需认证）

    用于诊断审查报告无法生成的问题
    """
    from app.services.llm.client import zhipu_llm

    try:
        # 简单的测试 prompt
        result = await zhipu_llm.chat_with_json_output([
            {"role": "user", "content": '请以 JSON 格式回复：{"status": "ok", "message": "LLM 连接正常"}'}
        ])
        return {
            "status": "success",
            "message": "LLM API 连接正常",
            "result": result
        }
    except Exception as e:
        import traceback
        return {
            "status": "error",
            "message": f"LLM API 调用失败: {str(e)}",
            "traceback": traceback.format_exc()
        }


def calculate_file_hash(file_bytes: bytes) -> str:
    """计算文件哈希值（用于去重）"""
    return hashlib.sha256(file_bytes).hexdigest()


def trigger_contract_review(contract_id: str, file_path: str) -> None:
    """
    触发合同审查任务

    根据配置使用 Celery 或 asyncio 后台任务
    """
    import logging
    import asyncio
    logger = logging.getLogger(__name__)

    if settings.USE_CELERY:
        # 使用 Celery 异步任务
        process_contract_review_task.delay(contract_id, file_path)
        logger.info(f"[Review] Contract {contract_id} submitted to Celery queue")
    else:
        # 检查是否已经在 event loop 中
        try:
            loop = asyncio.get_running_loop()
            # 已在 event loop 中，直接创建 task
            loop.create_task(process_contract_upload(contract_id, file_path))
            logger.info(f"[Review] Contract {contract_id} review triggered (in existing loop)")
        except RuntimeError:
            # 不在 event loop 中，可以使用 asyncio.run
            asyncio.run(process_contract_upload(contract_id, file_path))
            logger.info(f"[Review] Contract {contract_id} review triggered")


async def process_contract_upload(
    contract_id: str,
    file_path: str
):
    """
    处理合同上传：解析和审查

    后续将迁移到 Celery 异步任务
    """
    import logging
    logger = logging.getLogger(__name__)

    # 解析文件路径（使用公共函数）
    file_path = str(resolve_contract_file_path(file_path))
    logger.info(f"[Review] Resolved path to: {file_path}")

    logger.info(f"[Review] Starting review for contract {contract_id}")

    # 确保数据库连接已初始化
    if db.async_session_maker is None:
        db.connect()

    contract = None  # 预先声明，避免作用域问题

    # 创建新的数据库会话
    async with db.async_session_maker() as session:
        try:
            # 查询合同
            result = await session.execute(
                select(Contract).where(Contract.id == contract_id)
            )
            contract = result.scalar_one_or_none()

            if not contract:
                logger.error(f"[Review] Contract {contract_id} not found")
                return

            # 1. 更新状态为 processing
            contract.review_status = ReviewStatusEnum.processing
            await session.commit()

            logger.info(f"[Review] Parsing document for contract {contract_id}")

            # 2. 解析文档
            if file_path.endswith(".pdf"):
                parse_result = await document_parser.parse_pdf(file_path)
            else:
                parse_result = await document_parser.parse_word(file_path)

            extracted_text = parse_result.get("text", "")
            logger.info(f"[Review] Extracted {len(extracted_text)} characters for contract {contract_id}")

            if not extracted_text or len(extracted_text.strip()) < 50:
                logger.warning(f"[Review] Insufficient text extracted from contract {contract_id}, text length: {len(extracted_text)}")

            # 3. 更新合同内容
            contract.content_text = extracted_text

            # 4. 自动检测合同类型（如果未设置或为"其他"）
            original_type = contract.contract_type.value if contract.contract_type else "其他"
            if original_type == "其他":
                detected_type = detect_contract_type(contract.content_text)
                from app.models.contract import ContractType as ContractTypeEnum
                contract.contract_type = ContractTypeEnum(detected_type)
                contract_type_str = detected_type
            else:
                contract_type_str = original_type

            logger.info(f"[Review] Contract type: {contract_type_str} for contract {contract_id}")

            await session.commit()

            # 获取 tenant_id 用于检索公司政策
            workspace_result = await session.execute(
                select(Workspace).where(Workspace.id == contract.workspace_id)
            )
            workspace = workspace_result.scalar_one_or_none()
            tenant_id = workspace.tenant_id if workspace else None
            logger.info(f"[Review] Using tenant_id: {tenant_id} for contract {contract_id}")

            # 5. 合同理解分析（第一步）- 在审查之前执行，即使审查失败也能展示理解结果
            logger.info(f"[Review] Starting contract understanding analysis for {contract_id}")
            from app.services.analysis.understanding import understanding_service
            try:
                await understanding_service.generate_understanding(
                    contract_id=contract_id,
                    contract_text=contract.content_text,
                    contract_type=contract_type_str,
                    review_result=None  # 先不传审查结果，独立生成
                )
                logger.info(f"[Review] Understanding analysis completed for contract {contract_id}")
            except Exception as understanding_error:
                # 理解分析失败不应该阻止后续流程
                logger.error(f"[Review] Understanding analysis failed for contract {contract_id}: {understanding_error}")

            # 6. 执行审查（第二步，传递 tenant_id 以检索公司政策库）
            logger.info(f"[Review] Running LLM review for contract {contract_id}")
            review_result = await review_service.review_contract(
                contract_text=contract.content_text,
                contract_type=contract_type_str,
                tenant_id=tenant_id
            )
            logger.info(f"[Review] Review completed for contract {contract_id}")

            # 7. 更新理解分析（补充审查结果）
            try:
                await understanding_service.generate_understanding(
                    contract_id=contract_id,
                    contract_text=contract.content_text,
                    contract_type=contract_type_str,
                    review_result=review_result  # 带上审查结果完善理解
                )
                logger.info(f"[Review] Understanding analysis updated with review results for contract {contract_id}")
            except Exception as understanding_error:
                logger.error(f"[Review] Understanding analysis update failed for contract {contract_id}: {understanding_error}")

            # 8. 确定风险等级
            risk_clauses = review_result.get("risk_clauses", [])
            if any(c.get("risk_level") == "high" for c in risk_clauses):
                risk_level = "high"
            elif any(c.get("risk_level") == "medium" for c in risk_clauses):
                risk_level = "medium"
            else:
                risk_level = "low"

            # 9. 保存审查结果
            contract.review_result = review_result
            contract.risk_level = risk_level
            contract.review_status = ReviewStatusEnum.completed

            await session.commit()

            logger.info(f"[Review] Successfully completed review for contract {contract_id}, risk_level: {risk_level}")

            # 10. PDF 条款定位（仅 PDF 文件，且审查有风险条款）
            if file_path.endswith(".pdf") and risk_clauses:
                from app.services.review.tasks import _locate_clauses_in_pdf
                try:
                    await _locate_clauses_in_pdf(contract_id, file_path, risk_clauses)
                    logger.info(f"[Review] Clause location completed for contract {contract_id}")
                except Exception as locate_error:
                    logger.error(f"[Review] Clause location failed for contract {contract_id}: {locate_error}")

        except Exception as e:
            # 处理失败
            logger.error(f"[Review] Review failed for contract {contract_id}: {e}")
            import traceback
            traceback.print_exc()

            if contract:
                contract.review_status = ReviewStatusEnum.failed
                contract.review_error = str(e)
                await session.commit()
            raise e


def detect_contract_type(text: str) -> str:
    """
    从合同文本中自动检测合同类型
    """
    if not text:
        return "其他"

    text_lower = text.lower()

    # NDA/保密协议 检测
    nda_keywords = ["保密协议", "保密条款", "nda", "non-disclosure", "confidential", "保密义务", "商业秘密", "竞业限制"]
    if any(kw in text_lower for kw in nda_keywords):
        return "NDA"

    # 劳动合同 检测
    labor_keywords = ["劳动合同", "聘用合同", "雇佣合同", "员工", "雇主", "工资", "社会保险", "加班费", "年假", "试用期", "劳动合同法"]
    if any(kw in text_lower for kw in labor_keywords):
        return "劳动合同"

    # 采购合同 检测
    purchase_keywords = ["采购合同", "采购协议", "供货合同", "供货商", "货物买卖", "采购方", "供货方", "交货", "验收标准"]
    if any(kw in text_lower for kw in purchase_keywords):
        return "采购合同"

    # 销售合同 检测
    sales_keywords = ["销售合同", "销售协议", "买卖合同", "销售方", "购买方", "商品", "销售渠道", "代理商"]
    if any(kw in text_lower for kw in sales_keywords):
        return "销售合同"

    # 服务合同 检测
    service_keywords = ["服务合同", "服务协议", "咨询服务", "委托合同", "代理合同", "服务费", "服务内容", "服务质量"]
    if any(kw in text_lower for kw in service_keywords):
        return "服务合同"

    # 租赁合同 检测
    rental_keywords = ["租赁合同", "租赁协议", "房租", "租金", "出租人", "承租人", "租赁物", "押金"]
    if any(kw in text_lower for kw in rental_keywords):
        return "租赁合同"

    # 借款合同 检测
    loan_keywords = ["借款合同", "借款协议", "贷款合同", "借款人", "贷款人", "利息", "还款", "本金", "利率"]
    if any(kw in text_lower for kw in loan_keywords):
        return "借款合同"

    # 投资合同 检测
    investment_keywords = ["投资合同", "投资协议", "股权投资", "股权转让", "合伙人", "分红", "投资收益", "退出机制"]
    if any(kw in text_lower for kw in investment_keywords):
        return "投资合同"

    # 合作协议 检测
    cooperation_keywords = ["合作协议", "合作合同", "联合体", "合作方", "合作关系", "合作项目", "合作协议书"]
    if any(kw in text_lower for kw in cooperation_keywords):
        return "合作协议"

    return "其他"


@router.post("/upload", response_model=ContractResponse)
async def upload_contract(
    file: UploadFile = File(...),
    workspace_id: str = Form(...),
    contract_type: str | None = Form(None),
    current_user: UserModel = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """上传合同文件"""
    # 验证文件扩展名
    file_extension = file.filename.split(".")[-1].lower() if "." in file.filename else ""
    allowed_extensions = ["pdf", "docx"]
    if file_extension not in allowed_extensions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="不支持的文件格式，请上传 .pdf 或 .docx 格式文件（不支持 .doc 格式）"
        )

    # 验证文件 MIME 类型
    allowed_types = [
        "application/pdf",
        "application/msword",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    ]
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="不支持的文件类型，请上传 PDF 或 Word 文件"
        )

    # 验证工作区权限
    result = await db.execute(
        select(Workspace)
        .join(UserModel, UserModel.tenant_id == Workspace.tenant_id)
        .where(Workspace.id == workspace_id, UserModel.id == current_user.id)
    )
    workspace = result.scalar_one_or_none()

    if not workspace:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权访问该工作区"
        )

    # 读取文件内容
    file_bytes = await file.read()
    file_hash = calculate_file_hash(file_bytes)

    # 检查是否已存在相同文件
    result = await db.execute(
        select(Contract).where(
            Contract.file_hash == file_hash,
            Contract.workspace_id == workspace_id
        )
    )
    existing_contract = result.scalar_one_or_none()
    if existing_contract:
        # 如果旧合同未完成审查，重新启动审查
        if existing_contract.review_status != ReviewStatusEnum.completed:
            trigger_contract_review(existing_contract.id, existing_contract.file_path)
        return existing_contract

    # 保存文件（本地存储，生产环境使用 OSS）
    # 使用相对路径存储在数据库中，确保在不同环境下都能正确解析
    upload_dir = Path(settings.STORAGE_PATH) / workspace_id
    upload_dir.mkdir(parents=True, exist_ok=True)

    file_id = str(uuid.uuid4())
    file_extension = file.filename.split(".")[-1] if "." in file.filename else "pdf"
    file_path = upload_dir / f"{file_id}.{file_extension}"

    with open(file_path, "wb") as f:
        f.write(file_bytes)

    # 存储相对路径（相对于 STORAGE_PATH），便于跨环境迁移
    # 例如：workspace_id/file_id.ext
    relative_file_path = str(Path(workspace_id) / f"{file_id}.{file_extension}")

    # 解析合同类型
    contract_type_enum = None
    if contract_type:
        try:
            contract_type_enum = ContractTypeEnum(contract_type)
        except ValueError:
            contract_type_enum = ContractTypeEnum.other

    # 创建合同记录
    contract = Contract(
        id=str(uuid.uuid4()),
        workspace_id=workspace_id,
        user_id=current_user.id,
        file_name=file.filename,
        file_path=relative_file_path,  # 使用相对路径，便于跨环境迁移
        file_hash=file_hash,
        contract_type=contract_type_enum,
        review_status=ReviewStatusEnum.pending,
    )
    db.add(contract)
    await db.commit()
    await db.refresh(contract)

    # 同步处理合同（解析 + 审查）- 直接await而非后台任务
    # 后台任务在容器环境中会丢失，所以这里同步执行
    await process_contract_upload(contract.id, str(file_path))

    # 重新获取最新状态
    result = await db.execute(
        select(Contract).where(Contract.id == contract.id)
    )
    contract = result.scalar_one()

    return contract


@router.get("/", response_model=list[ContractResponse])
async def list_contracts(
    limit: int = 20,
    offset: int = 0,
    current_user: UserModel = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """获取当前租户下的所有合同"""
    result = await db.execute(
        select(Contract)
        .join(Workspace, Contract.workspace_id == Workspace.id)
        .where(
            Workspace.tenant_id == current_user.tenant_id
        )
        .order_by(Contract.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    contracts = result.scalars().all()
    return contracts


@router.get("/{contract_id}", response_model=ContractResponse)
async def get_contract(
    contract: Contract = Depends(verify_contract_access)
):
    """获取合同详情"""
    return contract


@router.get("/{contract_id}/file")
async def get_contract_file(
    contract: Contract = Depends(verify_contract_access)
):
    """获取合同原始文件（用于PDF预览）"""
    from fastapi.responses import FileResponse, StreamingResponse

    if not contract.file_path:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="文件不存在"
        )

    # 解析文件路径（使用公共函数）
    file_path = resolve_contract_file_path(contract.file_path)

    if not file_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"文件不存在: {file_path}"
        )

    # 根据文件扩展名确定 media type
    suffix = file_path.suffix.lower()
    media_types = {
        ".pdf": "application/pdf",
        ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        ".doc": "application/msword",
    }
    media_type = media_types.get(suffix, "application/octet-stream")

    return FileResponse(
        path=str(file_path),
        media_type=media_type,
        filename=contract.file_name
    )


@router.delete("/{contract_id}")
async def delete_contract(
    contract: Contract = Depends(verify_contract_access),
    db: AsyncSession = Depends(get_db)
):
    """删除合同"""
    await db.delete(contract)
    await db.commit()
    return {"message": "删除成功"}


@router.patch("/{contract_id}/type")
async def update_contract_type(
    contract: Contract = Depends(verify_contract_access),
    db: AsyncSession = Depends(get_db),
    contract_type: str = None
):
    """更新合同类型"""
    if contract_type is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="合同类型不能为空"
        )

    try:
        contract_type_enum = ContractTypeEnum(contract_type)
    except ValueError:
        # 如果不是预定义类型，设置为 other
        contract_type_enum = ContractTypeEnum.other

    contract.contract_type = contract_type_enum
    await db.commit()
    await db.refresh(contract)
    return {"message": "更新成功", "contract_type": contract.contract_type.value}


@router.get("/{contract_id}/review", response_model=dict)
async def get_review_result(
    contract: Contract = Depends(verify_contract_access)
):
    """获取合同审查结果"""
    if contract.review_status != ReviewStatusEnum.completed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"合同尚未完成审查，当前状态：{contract.review_status.value}"
        )

    if not contract.review_result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="未找到审查结果"
        )

    return contract.review_result


@router.get("/{contract_id}/review-status")
async def get_review_status(
    contract: Contract = Depends(verify_contract_access)
):
    """
    获取合同审查详细状态（用于调试）

    返回审查进度、错误信息等
    """
    return {
        "contract_id": contract.id,
        "file_name": contract.file_name,
        "file_path": contract.file_path,
        "review_status": contract.review_status.value,
        "risk_level": contract.risk_level.value if contract.risk_level else None,
        "content_text_length": len(contract.content_text) if contract.content_text else 0,
        "review_result_keys": list(contract.review_result.keys()) if contract.review_result else None,
        "review_error": contract.review_error,
        "contract_type": contract.contract_type.value if contract.contract_type else None,
    }


@router.get("/{contract_id}/understanding")
async def get_contract_understanding(
    contract: Contract = Depends(verify_contract_access)
):
    """获取合同理解分析结果"""
    if contract.review_status != ReviewStatusEnum.completed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"合同尚未完成审查，当前状态：{contract.review_status.value}"
        )

    from app.services.analysis.understanding import understanding_service
    understanding = await understanding_service.get_understanding(contract.id)

    if not understanding:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="未找到理解分析结果，请稍后重试"
        )

    return understanding


@router.get("/{contract_id}/clause-locations")
async def get_clause_locations(
    contract: Contract = Depends(verify_contract_access)
):
    """获取条款 PDF 定位信息"""
    if contract.review_status != ReviewStatusEnum.completed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"合同尚未完成审查，当前状态：{contract.review_status.value}"
        )

    from sqlalchemy import select
    from app.models.clause_location import ClauseLocation

    async with db.async_session_maker() as session:
        result = await session.execute(
            select(ClauseLocation)
            .where(ClauseLocation.contract_id == contract.id)
            .order_by(ClauseLocation.page_number)
        )
        locations = result.scalars().all()

        return [
            {
                "clause_title": loc.clause_title,
                "clause_text": loc.clause_text,
                "risk_level": loc.risk_level,
                "page": loc.page_number,
                "bbox": loc.bbox,
                "similarity": loc.similarity,
                "match_type": loc.match_type,
            }
            for loc in locations
        ]


@router.get("/{contract_id}/pdf-positions")
async def get_pdf_text_positions(
    contract: Contract = Depends(verify_contract_access)
):
    """
    获取 PDF 文本位置信息（用于前端渲染高亮）

    返回:
    - text_positions: 文本位置列表
    - clause_locations: 条款高亮位置
    """
    if not contract.file_path.endswith(".pdf"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="仅支持 PDF 文件"
        )

    if contract.review_status != ReviewStatusEnum.completed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"合同尚未完成审查，当前状态：{contract.review_status.value}"
        )

    from app.services.pdf.reader import pdf_reader
    from sqlalchemy import select
    from app.models.clause_location import ClauseLocation

    # 解析文件路径（支持相对路径）
    resolved_file_path = str(resolve_contract_file_path(contract.file_path))

    # 提取 PDF 文本和位置
    pdf_data = pdf_reader.extract_text_with_positions(resolved_file_path)

    # 如果文本过少，尝试 OCR
    if pdf_data.get("needs_ocr"):
        pdf_data = await pdf_reader.extract_with_ocr(resolved_file_path)

    # 获取条款定位
    async with db.async_session_maker() as session:
        result = await session.execute(
            select(ClauseLocation)
            .where(ClauseLocation.contract_id == contract.id)
        )
        locations = result.scalars().all()

    return {
        "text_positions": pdf_data.get("text_positions", []),
        "pages": pdf_data.get("pages", 0),
        "has_text": pdf_data.get("has_text", False),
        "needs_ocr": pdf_data.get("needs_ocr", True),
        "source": pdf_data.get("source", "pymupdf"),
        "clause_locations": [
            {
                "clause_title": loc.clause_title,
                "clause_text": loc.clause_text,
                "risk_level": loc.risk_level,
                "page": loc.page_number,
                "bbox": loc.bbox,
            }
            for loc in locations
        ]
    }


@router.get("/{contract_id}/highlighted-pdf")
async def get_highlighted_pdf(
    contract: Contract = Depends(verify_contract_access)
):
    """
    获取高亮 PDF 文件流

    用于在线查看高亮后的 PDF
    """
    if not contract.file_path.endswith(".pdf"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="仅支持 PDF 文件"
        )

    if contract.review_status != ReviewStatusEnum.completed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"合同尚未完成审查，当前状态：{contract.review_status.value}"
        )

    from app.services.pdf.highlighter import pdf_highlighter
    from sqlalchemy import select
    from app.models.clause_location import ClauseLocation

    # 获取条款定位
    async with db.async_session_maker() as session:
        result = await session.execute(
            select(ClauseLocation)
            .where(ClauseLocation.contract_id == contract.id)
        )
        locations = result.scalars().all()

    # 构建高亮位置列表
    clause_positions = []
    for loc in locations:
        bbox = loc.bbox
        if bbox:
            clause_positions.append({
                "text": loc.clause_text,
                "page": loc.page_number,
                "bbox": bbox,
                "risk_level": loc.risk_level,
                "clause_id": loc.id,
            })

    # 生成高亮 PDF
    # 解析文件路径（支持相对路径）
    resolved_file_path = str(resolve_contract_file_path(contract.file_path))

    if clause_positions:
        pdf_bytes = pdf_highlighter.highlight_clauses(
            resolved_file_path,
            clause_positions
        )
    else:
        # 无定位信息，返回原始 PDF
        with open(resolved_file_path, "rb") as f:
            pdf_bytes = f.read()

    from fastapi.responses import StreamingResponse
    import io

    # 使用纯英文文件名避免编码问题
    safe_filename = "highlighted_contract.pdf"

    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"inline; filename={safe_filename}"
        }
    )


# ========== Word 辅助编辑 API ==========

@router.get("/{contract_id}/word-paragraphs")
async def get_word_paragraphs(
    contract: Contract = Depends(verify_contract_access)
):
    """
    获取 Word 文档的段落列表（带索引）

    用于前端渲染原文并进行风险高亮定位
    """
    if not contract.file_path.endswith(".docx"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="仅支持 Word (.docx) 文件"
        )

    if contract.review_status != ReviewStatusEnum.completed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"合同尚未完成审查，当前状态：{contract.review_status.value}"
        )

    from app.services.word import word_indexer

    # 解析文件路径（支持相对路径）
    resolved_file_path = str(resolve_contract_file_path(contract.file_path))

    result = await word_indexer.parse_word_paragraphs(
        resolved_file_path,
        contract.id
    )

    return result


@router.post("/{contract_id}/apply-suggestions")
async def apply_word_suggestions(
    suggestions: List[Dict[str, Any]],
    contract: Contract = Depends(verify_contract_access),
    db: AsyncSession = Depends(get_db)
):
    """
    采纳建议并生成修订后的 Word 文档

    Request Body:
        suggestions: 采纳的建议列表
            [{
                "paragraph_index": 5,
                "original_text": "原文本",
                "new_text": "修改后文本",
                "risk_description": "风险描述",
                "accepted": true
            }]

    Returns:
        生成后的修订 Word 文件字节流
    """
    if not contract.file_path.endswith(".docx"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="仅支持 Word (.docx) 文件"
        )

    # 过滤已采纳的建议
    accepted_suggestions = [
        s for s in suggestions if s.get("accepted", False)
    ]

    if not accepted_suggestions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="没有需要采纳的建议"
        )

    from app.services.word import revision_doc_generator

    # 解析文件路径（支持相对路径）
    resolved_file_path = str(resolve_contract_file_path(contract.file_path))

    # 生成修订文档
    revised_bytes = revision_doc_generator.apply_suggestions_to_document(
        resolved_file_path,
        accepted_suggestions
    )

    # 临时保存修订文档（可选，也可以直接返回）
    import uuid
    revised_file_name = f"revised_{uuid.uuid4().hex[:8]}_{contract.file_name}"
    revised_file_path = Path(settings.STORAGE_PATH) / "revisions" / revised_file_name
    revised_file_path.parent.mkdir(parents=True, exist_ok=True)

    with open(revised_file_path, "wb") as f:
        f.write(revised_bytes)

    # 更新合同记录修订文件路径（可选）
    # contract.revised_file_path = str(revised_file_path)
    # await db.commit()

    from fastapi.responses import StreamingResponse
    import io
    from urllib.parse import quote

    # URL-encode filename for Content-Disposition header
    encoded_filename = quote(revised_file_name)

    return StreamingResponse(
        io.BytesIO(revised_bytes),
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={
            "Content-Disposition": f"attachment; filename*=UTF-8''{encoded_filename}"
        }
    )


@router.get("/{contract_id}/revised-word")
async def get_revised_word(
    contract: Contract = Depends(verify_contract_access)
):
    """
    获取已生成的修订 Word 文档

    如果有已采纳的建议，返回修订后的文档流
    """
    if not contract.file_path.endswith(".docx"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="仅支持 Word (.docx) 文件"
        )

    # 检查是否存在修订文档
    revised_dir = Path(settings.STORAGE_PATH) / "revisions"
    revised_pattern = f"revised_*_{contract.file_name}"

    revised_files = list(revised_dir.glob(revised_pattern))

    if not revised_files:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="未找到修订文档，请先采纳建议并生成"
        )

    # 返回最新的修订文档
    latest_revised = max(revised_files, key=lambda p: p.stat().st_mtime)

    with open(latest_revised, "rb") as f:
        revised_bytes = f.read()

    from fastapi.responses import StreamingResponse
    import io

    revised_file_name = f"修订版_{contract.file_name}"

    from urllib.parse import quote
    encoded_filename = quote(revised_file_name)

    return StreamingResponse(
        io.BytesIO(revised_bytes),
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={
            "Content-Disposition": f"attachment; filename*=UTF-8''{encoded_filename}"
        }
    )
