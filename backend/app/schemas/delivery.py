from pydantic import BaseModel, Field


class OpinionExportOptions(BaseModel):
    format: str = Field(default="html", pattern="^(html|json)$")
    include_risk_clauses: bool = True
    include_missing_clauses: bool = True
    include_recommendations: bool = True
    include_evidence: bool = True


class EmailDraftRequest(BaseModel):
    from_email: str | None = None
    to: list[str] = Field(default_factory=list)
    subject: str = "合同审查意见"
    body_text: str = Field(min_length=1, max_length=100000)
    body_html: str | None = None
    provider: str | None = None
    idempotency_key: str = Field(min_length=8, max_length=128)
