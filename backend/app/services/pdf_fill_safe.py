from __future__ import annotations

from pathlib import Path
import os
import shutil
import tempfile
from typing import Any, Dict

from pypdf import PdfReader, PdfWriter
from pypdf.generic import BooleanObject, NameObject


def _fill_with_acroform(
    template_path: Path | str,
    field_data: Dict[str, Any],
    out_path: Path | str,
) -> Path:
    """Fill PDF form fields using pypdf AcroForm support and return out_path."""

    template_path = Path(template_path)
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    reader = PdfReader(str(template_path))
    writer = PdfWriter()
    writer.clone_document_from_reader(reader)

    acro = writer._root_object.get("/AcroForm")
    if acro is not None:
        acro.update({NameObject("/NeedAppearances"): BooleanObject(True)})

    for page in writer.pages:
        writer.update_page_form_field_values(page, field_data)

    fd, tmp_name = tempfile.mkstemp(suffix=".pdf")
    os.close(fd)
    tmp_path = Path(tmp_name)

    try:
        with open(str(tmp_path), "wb") as fh:
            writer.write(fh)

        shutil.move(str(tmp_path), str(out_path))
        return out_path
    except Exception:
        if tmp_path.exists():
            tmp_path.unlink()
        raise


def fill_form_safe(template_path: Path | str, field_data: Dict[str, Any], out_path: Path | str) -> Path:
    """Fill template_path into out_path safely and return out_path."""

    return _fill_with_acroform(template_path, field_data, out_path)


def fill_form_auto(template_path: Path | str, field_data: Dict[str, Any], out_path: Path | str) -> Path:
    """Fill PDF via AcroForm only (overlay logic disabled)."""

    return _fill_with_acroform(template_path, field_data, out_path)
