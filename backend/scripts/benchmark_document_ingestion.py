"""Print a small, dependency-light parser benchmark for fixture PDFs."""
import json, sys, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.services.document.parser_router import ParserRouter
from app.services.document.pymupdf_adapter import PyMuPDFAdapter

root = Path(__file__).resolve().parents[1] / "tests" / "fixtures" / "pdf"
manifest = root / "manifest.json"
items = json.loads(manifest.read_text(encoding="utf-8")) if manifest.exists() else []
rows = []
for item in items:
    path = Path(item.get("source_path", item.get("file", "")))
    if not path.is_absolute():
        path = Path(__file__).resolve().parents[2] / path
    started = time.perf_counter()
    try:
        route = ParserRouter().route(str(path))
        ast = PyMuPDFAdapter().parse(str(path), "benchmark", "benchmark")
        rows.append({"file": item.get("name", item.get("file")), "pages": len(ast.pages), "chars": len(ast.text),
                     "route": route, "seconds": round(time.perf_counter() - started, 3)})
    except Exception as exc:
        rows.append({"file": item.get("name", item.get("file")), "error": str(exc)})
print(json.dumps(rows, ensure_ascii=False, indent=2))
