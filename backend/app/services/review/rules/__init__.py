"""
审查规则库模块
"""
from app.services.review.rules.nda import NDA_REVIEW_RULES
from app.services.review.rules.labor import LABOR_CONTRACT_REVIEW_RULES

__all__ = ["NDA_REVIEW_RULES", "LABOR_CONTRACT_REVIEW_RULES"]
