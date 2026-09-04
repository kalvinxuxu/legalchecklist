"""Compatibility exports for integrations that still import the old module.

Review execution is owned by ``review_worker.py`` and LangGraph. No Celery
review task or duplicate parser lives here anymore.
"""
from app.services.review.evidence_locator import locate_clauses_in_pdf

_locate_clauses_in_pdf = locate_clauses_in_pdf

__all__ = ["locate_clauses_in_pdf", "_locate_clauses_in_pdf"]
