from datetime import date
from app.services.rag.legal_rank_policy import authority_score, is_eligible


def test_authority_ordering():
    assert authority_score({"authority_level": "supreme_interpretation"}) > authority_score({"authority_level": "article"})


def test_effective_date_and_jurisdiction_are_hard_filters():
    assert not is_eligible({"effective_from": "2030-01-01"}, date(2026, 1, 1))
    assert not is_eligible({"jurisdiction": "上海"}, jurisdiction="北京")
    assert is_eligible({"effective_to": "2027-01-01"}, date(2026, 1, 1))
