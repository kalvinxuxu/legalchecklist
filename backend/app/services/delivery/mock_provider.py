import uuid


class MockMailProvider:
    """Local provider; records no outbound send operation."""
    drafts: dict[str, dict] = {}

    async def save_draft(self, *, sender_email, recipients, subject, body_text, body_html=None, attachments=None, remote_id=None) -> str:
        draft_id = remote_id or f"mock-{uuid.uuid4().hex}"
        self.drafts[draft_id] = {"from": sender_email, "to": recipients, "subject": subject, "body": body_text,
                                 "attachments": [item.filename for item in (attachments or [])]}
        return draft_id
