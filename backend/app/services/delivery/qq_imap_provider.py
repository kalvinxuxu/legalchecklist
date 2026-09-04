"""QQ Mail IMAP draft adapter. It appends/updates drafts and never calls SMTP send."""
import asyncio
import email.utils
import imaplib
import re
import base64
from datetime import datetime, timezone
from email.message import EmailMessage
from app.core.config import settings
from .mail_provider import MailAttachment


class QQImapProvider:
    async def save_draft(self, *, sender_email, recipients, subject, body_text, body_html=None, attachments=None, remote_id=None) -> str:
        return await asyncio.to_thread(self._save, sender_email, recipients, subject, body_text, body_html, attachments or [])

    def _save(self, sender_email, recipients, subject, body_text, body_html, attachments: list[MailAttachment]):
        if not settings.QQ_MAIL_USERNAME or not settings.QQ_MAIL_APP_PASSWORD:
            raise RuntimeError("QQ Mail IMAP credentials are not configured")
        message = EmailMessage()
        message["From"] = sender_email or settings.QQ_MAIL_USERNAME
        message["To"] = ", ".join(recipients)
        message["Subject"] = subject
        message["Date"] = email.utils.formatdate(localtime=True)
        message.set_content(body_text)
        for attachment in attachments:
            maintype, subtype = attachment.content_type.split("/", 1)
            message.add_attachment(attachment.content, maintype=maintype, subtype=subtype, filename=attachment.filename)
        with imaplib.IMAP4_SSL(settings.QQ_IMAP_HOST, settings.QQ_IMAP_PORT) as client:
            client.login(settings.QQ_MAIL_USERNAME, settings.QQ_MAIL_APP_PASSWORD)
            drafts_folder = self._resolve_drafts_folder(client)
            status, _ = client.append(drafts_folder, "(\\Draft)", imaplib.Time2Internaldate(datetime.now(timezone.utc)), message.as_bytes())
            if status != "OK":
                raise RuntimeError("QQ Mail draft append failed")
        return "qq-imap-draft"

    @staticmethod
    def _resolve_drafts_folder(client):
        """QQ returns English mailbox names even for Chinese accounts."""
        configured = settings.QQ_MAIL_DRAFTS_FOLDER
        status, rows = client.list()
        if status == "OK":
            names = [row.decode("utf-8", "replace") if isinstance(row, bytes) else str(row) for row in rows or []]
            for name in names:
                if re.search(r'"(?:Drafts|草稿箱)"\s*$', name, re.IGNORECASE):
                    return name.rsplit('"', 2)[-2]
        return self._encode_mailbox_name(configured)

    @staticmethod
    def _encode_mailbox_name(name: str) -> str:
        """Encode an IMAP mailbox name using modified UTF-7 (RFC 3501)."""
        output = []
        pending = []
        def flush():
            if pending:
                encoded = base64.b64encode("".join(pending).encode("utf-16-be")).decode("ascii").rstrip("=").replace("/", ",")
                output.append("&" + encoded + "-")
                pending.clear()
        for char in name:
            if "\x20" <= char <= "\x7e":
                flush()
                output.append("&-" if char == "&" else char)
            else:
                pending.append(char)
        flush()
        return "".join(output)
