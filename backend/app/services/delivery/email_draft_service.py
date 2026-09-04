from sqlalchemy import select
from app.core.config import settings
from app.db.session import db
from app.models.delivery import EmailDraft
from .mock_provider import MockMailProvider
from .qq_imap_provider import QQImapProvider
from .mail_provider import MailAttachment


def _provider():
    return QQImapProvider() if settings.MAIL_PROVIDER.lower() in {"qq", "qq_imap"} else MockMailProvider()


async def save_draft(*, tenant_id: str, contract_id: str, sender_email: str, recipients: list[str], subject: str, body_text: str, body_html: str | None, attachments: list[MailAttachment], idempotency_key: str) -> EmailDraft:
    async with db.async_session_maker() as session:
        draft = (await session.execute(select(EmailDraft).where(EmailDraft.tenant_id == tenant_id, EmailDraft.idempotency_key == idempotency_key))).scalar_one_or_none()
        if not draft:
            draft = EmailDraft(tenant_id=tenant_id, contract_id=contract_id, sender_email=sender_email, recipients=recipients, attachments=[{"filename": item.filename, "content_type": item.content_type, "size": len(item.content)} for item in attachments], subject=subject, body_text=body_text, body_html=body_html, provider=settings.MAIL_PROVIDER, idempotency_key=idempotency_key, sync_status="sync_pending")
            session.add(draft)
            await session.flush()
        elif not draft.sender_email:
            draft.sender_email = sender_email
        draft.attachments = [{"filename": item.filename, "content_type": item.content_type, "size": len(item.content)} for item in attachments]
        try:
            draft.provider_draft_id = await _provider().save_draft(sender_email=sender_email, recipients=recipients, subject=subject, body_text=body_text, body_html=body_html, attachments=attachments, remote_id=draft.provider_draft_id)
            draft.sync_status, draft.last_error = "synced", None
        except Exception as exc:
            draft.sync_status, draft.last_error = "sync_failed", str(exc)
            draft.retry_count = (draft.retry_count or 0) + 1
        await session.commit()
        await session.refresh(draft)
        return draft
