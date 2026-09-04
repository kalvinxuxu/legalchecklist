from app.services.document.parser_router import ParserRouter

def test_router_contract_exposes_parser_and_ocr_decision(monkeypatch):
    from app.services.document import parser_router
    monkeypatch.setattr(parser_router, "inspect_pdf", lambda _: [type("M", (), {"page":0,"classification":"scan","text_chars":0,"image_area_ratio":1.0,"has_fonts":False})()])
    route=ParserRouter().route("ignored.pdf")[0]
    assert route["parser"] == "ocr" and route["ocr_required"] is True
