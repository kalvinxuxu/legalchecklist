import io
import json
from urllib.parse import quote
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse, JSONResponse
from sqlalchemy import select

from app.api.v1.endpoints.auth import get_current_user
from app.middleware.tenant_isolation import verify_contract_access
from app.core.config import settings
from app.db.session import db
from app.models.contract import Contract, ReviewStatus
from app.models.delivery import EmailDraft
from app.models.review_run import ReviewRun
from app.schemas.delivery import OpinionExportOptions, EmailDraftRequest
from app.services.delivery.opinion_service import build_opinion
from app.services.delivery.opinion_exporter import generate_opinion_html, generate_opinion_docx
from app.services.delivery.email_draft_service import save_draft
from app.services.delivery.email_draft_agent import draft_email
from app.services.delivery.mail_provider import MailAttachment

router = APIRouter()


def _completed_opinion(contract: Contract):
    if contract.review_status != ReviewStatus.completed or not contract.review_result:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="合同尚未完成审查")
    return build_opinion(contract.file_name, contract.review_result)


@router.post("/{contract_id}/export-opinion")
async def export_opinion(options: OpinionExportOptions, contract: Contract = Depends(verify_contract_access)):
    opinion = _completed_opinion(contract)
    if options.format == "json":
        return JSONResponse(opinion)
    payload = generate_opinion_html(opinion)
    filename = quote(f"审查意见_{contract.file_name.rsplit('.', 1)[0]}.html")
    return StreamingResponse(io.BytesIO(payload), media_type="text/html; charset=utf-8",
                             headers={"Content-Disposition": f"attachment; filename*=UTF-8''{filename}"})


@router.post("/{contract_id}/export-opinion-docx")
async def export_opinion_docx(contract: Contract = Depends(verify_contract_access)):
    opinion = _completed_opinion(contract)
    payload = generate_opinion_docx(opinion)
    filename = quote(f"审查意见_{contract.file_name.rsplit('.', 1)[0]}.docx")
    return StreamingResponse(io.BytesIO(payload), media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                             headers={"Content-Disposition": f"attachment; filename*=UTF-8''{filename}"})


@router.post("/{contract_id}/email-drafts")
async def create_email_draft(
    request: EmailDraftRequest,
    contract: Contract = Depends(verify_contract_access),
    current_user=Depends(get_current_user),
):
    if not request.to:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="请至少填写一个收件人")
    opinion = _completed_opinion(contract)
    attachment_name = f"审查意见_{contract.file_name.rsplit('.', 1)[0]}.docx"
    attachments = [MailAttachment(filename=attachment_name,
                                   content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                                   content=generate_opinion_docx(opinion))]
    draft = await save_draft(tenant_id=current_user.tenant_id, contract_id=contract.id,
                             sender_email=request.from_email or settings.QQ_MAIL_USERNAME or "kalvinxuxu@qq.com",
                             recipients=[str(address) for address in request.to], subject=request.subject,
                             body_text=request.body_text, body_html=request.body_html,
                             attachments=attachments,
                             idempotency_key=request.idempotency_key)
    return {"draft_id": draft.id, "from": draft.sender_email, "provider": draft.provider, "provider_draft_id": draft.provider_draft_id,
            "sync_status": draft.sync_status, "retry_count": draft.retry_count, "last_error": draft.last_error,
            "attachments": draft.attachments}


@router.post("/{contract_id}/email-draft-preview")
async def preview_email_draft(contract: Contract = Depends(verify_contract_access)):
    opinion = _completed_opinion(contract)
    content = await draft_email(contract.file_name, opinion)
    return {"from": settings.QQ_MAIL_USERNAME or "kalvinxuxu@qq.com", **content,
            "attachments": [{"filename": f"审查意见_{contract.file_name.rsplit('.', 1)[0]}.docx",
                             "content_type": "application/vnd.openxmlformats-officedocument.wordprocessingml.document"}]}


@router.get("/{contract_id}/email-drafts/{draft_id}")
async def get_email_draft(draft_id: str, contract: Contract = Depends(verify_contract_access), current_user=Depends(get_current_user)):
    async with db.async_session_maker() as session:
        draft = (await session.execute(select(EmailDraft).where(EmailDraft.id == draft_id,
                                                                    EmailDraft.contract_id == contract.id,
                                                                    EmailDraft.tenant_id == current_user.tenant_id))).scalar_one_or_none()
    if not draft:
        raise HTTPException(status_code=404, detail="邮件草稿不存在")
    return {"draft_id": draft.id, "from": draft.sender_email, "to": draft.recipients, "subject": draft.subject, "body_text": draft.body_text,
            "provider": draft.provider, "provider_draft_id": draft.provider_draft_id,
            "sync_status": draft.sync_status, "retry_count": draft.retry_count, "last_error": draft.last_error,
            "attachments": draft.attachments}
