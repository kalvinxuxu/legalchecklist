from typing import Protocol
from dataclasses import dataclass


@dataclass(frozen=True)
class MailAttachment:
    filename: str
    content_type: str
    content: bytes


class MailDraftProvider(Protocol):
    async def save_draft(self, *, sender_email: str, recipients: list[str], subject: str, body_text: str, body_html: str | None, attachments: list[MailAttachment], remote_id: str | None = None) -> str: ...
