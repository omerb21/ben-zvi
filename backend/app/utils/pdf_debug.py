from __future__ import annotations

from pathlib import Path
from typing import Optional

from pypdf import PdfReader


def inspect_pdf(path: Path) -> None:
    print("=== PDF:", path)
    if not path.is_file():
        print("  EXISTS:", False)
        return

    print("  EXISTS:", True)
    reader = PdfReader(str(path))
    root = reader.trailer.get("/Root", {}) or {}
    acro = root.get("/AcroForm")
    print("  HAS_ACROFORM:", bool(acro))

    try:
        fields: Optional[dict] = reader.get_fields()
    except Exception as exc:  # pragma: no cover - debug helper
        print("  ERROR_READING_FIELDS:", exc)
        fields = None

    if fields is None:
        print("  FIELDS_COUNT:", 0)
    else:
        print("  FIELDS_COUNT:", len(fields))
        for name in list(fields.keys())[:20]:
            print("   - FIELD:", name)


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python -m app.utils.pdf_debug <pdf-path> [...]")
        raise SystemExit(1)

    for arg in sys.argv[1:]:
        inspect_pdf(Path(arg))
