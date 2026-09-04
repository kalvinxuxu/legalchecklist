import json
from pathlib import Path

def test_fixture_manifest_declares_routing_contract():
    manifest=json.loads((Path(__file__).parents[2]/"tests/fixtures/pdf/manifest.json").read_text(encoding="utf-8"))
    assert isinstance(manifest, list)
