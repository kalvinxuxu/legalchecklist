from app.services.document.identity import version_id

def test_parser_version_changes_version_identity():
    assert version_id("d", "p", "1") != version_id("d", "p", "2")
