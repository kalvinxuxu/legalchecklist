from pathlib import Path
import os

import pytest


def test_docling_complex_layout_acceptance():
    if os.getenv("RUN_DOCLING_ACCEPTANCE") != "1":
        pytest.skip("Docling acceptance is opt-in; set RUN_DOCLING_ACCEPTANCE=1")
    pytest.importorskip("docling")
    fixture = Path(__file__).resolve().parents[3] / "output" / "pdf" / "docling_complex_layout_fixture.pdf"
    if not fixture.exists():
        pytest.skip("run backend/scripts/create_docling_fixture.py first")

    from app.services.document.docling_adapter import DoclingAdapter
    from app.services.document.evidence_resolver import resolve_quote

    assert DoclingAdapter.name == "docling"
    assert DoclingAdapter.version == "optional"

    adapter = DoclingAdapter()
    unified = adapter.parse(str(fixture), "docling-fixture", "docling-fixture-v1")
    markdown = adapter.last_markdown
    assert "COMMERCIAL SCHEDULE" in markdown.upper()
    assert "A-01" in markdown and "A-05" in markdown
    assert "5900" in markdown
    assert markdown.count("|") >= 10

    assert unified.text.strip()
    assert len(unified.pages) == 2
    assert sum(len(page.blocks) for page in unified.pages) >= 10
    assert any("5900" in block.text for page in unified.pages for block in page.blocks)
    locations, strategy, confidence = resolve_quote(unified, "5900")
    assert locations and strategy == "id_exact" and confidence == 1.0
