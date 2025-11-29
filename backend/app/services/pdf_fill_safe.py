from __future__ import annotations

from pathlib import Path
import os
import shutil
import tempfile
from typing import Any, Dict

from pypdf import PdfReader, PdfWriter
from pypdf.generic import BooleanObject, NameObject, TextStringObject


def _fill_with_acroform(
    template_path: Path | str,
    field_data: Dict[str, Any],
    out_path: Path | str,
    field_name_prefix: str | None = None,
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

    if acro is not None and field_name_prefix:
        fields = acro.get("/Fields")

        def _rename_fields(field_array):  # type: ignore[no-redef]
            for field_ref in field_array:
                field = field_ref.get_object()
                name_obj = field.get("/T")
                if name_obj is not None:
                    name_str = str(name_obj)
                    if not name_str.startswith(field_name_prefix):
                        new_name = TextStringObject(f"{field_name_prefix}{name_str}")
                        field.update({NameObject("/T"): new_name})
                kids = field.get("/Kids")
                if kids:
                    _rename_fields(kids)

        if fields:
            try:
                _rename_fields(fields)
            except Exception:
                # If renaming fails for any reason, keep the filled PDF as-is.
                pass

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
    return _fill_with_acroform(template_path, field_data, out_path, field_name_prefix=None)


def fill_form_auto(
    template_path: Path | str,
    field_data: Dict[str, Any],
    out_path: Path | str,
    field_name_prefix: str | None = None,
) -> Path:
    """Fill PDF via AcroForm only (overlay logic disabled)."""

    return _fill_with_acroform(
        template_path,
        field_data,
        out_path,
        field_name_prefix=field_name_prefix,
    )
