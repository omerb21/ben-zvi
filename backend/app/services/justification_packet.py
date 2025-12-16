from __future__ import annotations

import logging
from pathlib import Path
from typing import List, Tuple, Optional

from sqlalchemy.orm import Session
from pypdf import PdfWriter, PdfReader

from app.models import Client
from app.utils.fs import ensure_dir as _ensure_dir
from app.services import justification_packet_generate as _packet_generate
from app.services import justification_packet_parts as _packet_parts
from app.services import justification_packet_paths as _packet_paths
from app.services import justification_packet_trim as _packet_trim
from app.services.justification_packet_fields import get_acroform_fields as _get_acroform_fields
from app.services.justification_packet_fields import walk_acroform_field_array as _walk_acroform_field_array
from app.services.justification_packet_fields import rename_kit_specific_fields as _rename_kit_specific_fields
from app.services.justification_packet_fields import (
    make_packet_field_names_unique_in_file as _make_packet_field_names_unique_in_file_impl,
)

logger = logging.getLogger(__name__)


def _get_export_dir(client: Client) -> Path:
    return _packet_paths._get_export_dir(client)


def _try_pdf_reader(pdf_path: Path) -> Optional[PdfReader]:
    return _packet_parts._try_pdf_reader(pdf_path)


def _try_generate_missing(generate_fn, *, log_message: str, log_args: tuple) -> None:
    return _packet_parts._try_generate_missing(
        generate_fn,
        log_message=log_message,
        log_args=log_args,
    )


def _get_packet_paths(export_dir: Path, client_id: int) -> Tuple[Path, Path]:
    return _packet_paths._get_packet_paths(export_dir, client_id)


def _get_kit_paths(export_dir: Path, client_id: int, new_product_id: int) -> Tuple[Path, Path]:
    return _packet_paths._get_kit_paths(export_dir, client_id, new_product_id)


def _get_advice_pdf_path(client: Client) -> Path:
    return _packet_paths._get_advice_pdf_path(client)


def _build_b1_base_filename(client: Client) -> str:
    return _packet_paths._build_b1_base_filename(client)


def _get_b1_pdf_candidates(client: Client) -> List[Path]:
    return _packet_paths._get_b1_pdf_candidates(client)


def _get_kit_pdf_paths_for_client(
    db: Session,
    client: Client,
    generate_missing: bool = False,
) -> List[Path]:
    """החזרת קובצי קיט קיימים ללקוח, אחד לכל קופה קיימת לכל היותר.

    הלוגיקה מקבילה ל-handleGenerateAllKits בפרונט: לכל existing_product_id
    ייבחר מוצר חדש אחד בלבד (לפי מזהה מוצר חדש קטן יותר), ומוצרים חדשים
    ללא existing_product_id ייכללו תמיד. עבור כל מוצר ננסה קודם קובץ ערוך,
    ואז קובץ אוטומטי, אם הם קיימים בתיקיית הלקוח.
    """

    return _packet_parts._get_kit_pdf_paths_for_client(db, client, generate_missing=generate_missing)


def _maybe_add_advice_part(
    db: Session,
    client: Client,
    *,
    parts: List[Path],
    generate_missing: bool,
) -> None:
    return _packet_parts._maybe_add_advice_part(
        db,
        client,
        parts=parts,
        generate_missing=generate_missing,
    )


def _maybe_add_b1_part(
    client: Client,
    *,
    parts: List[Path],
    generate_missing: bool,
) -> None:
    return _packet_parts._maybe_add_b1_part(
        client,
        parts=parts,
        generate_missing=generate_missing,
    )


def _append_parts_to_writer(writer: PdfWriter, parts: List[Path]) -> bool:
    return _packet_parts._append_parts_to_writer(writer, parts)


def _get_packet_source_path_or_raise(export_dir: Path, client_id: int) -> Path:
    return _packet_trim._get_packet_source_path_or_raise(export_dir, client_id)


def generate_client_packet_pdf(
    db: Session,
    client: Client,
    generate_missing: bool = True,
) -> Tuple[bytes, str]:
    """Generate a combined packet PDF for the client.

    The packet contains, בסדר הבא:
    1. מסמך הנמקה (אם קיים / הופק).
    2. טופס B1 (ערוך אם קיים, אחרת בסיסי אם קיים / הופק).
    3. כל קיטי ההצטרפות לפי סדר מזהה המוצר החדש, כשהעדפה ראשונה היא לגרסה ערוכה.

    כל הקבצים נלקחים מתיקיית הייצוא של הלקוח, ובמידת הצורך מופקים מחדש.
    התוצאה נכתבת לקובץ packet_<client_id>.pdf בתיקיית הייצוא ומוחזרת כ‑bytes.
    """
    return _packet_generate.generate_client_packet_pdf(
        db,
        client,
        generate_missing=generate_missing,
    )


def _make_packet_field_names_unique_in_file(packet_path: Path) -> None:
    return _packet_generate._make_packet_field_names_unique_in_file(packet_path)


def _debug_dump_packet_fields(packet_path: Path) -> None:
    # Disabled for performance - uncomment for debugging
    # try:
    #     reader = PdfReader(str(packet_path))
    #     fields = reader.get_fields()
    # except Exception:
    #     return
    # if not fields:
    #     return
    # debug_path = packet_path.with_name(f"{packet_path.stem}_debug_fields.txt")
    # try:
    #     lines = [str(name) for name in fields.keys()]
    #     debug_path.write_text("\n".join(lines), encoding="utf-8")
    # except Exception:
    #     return
    return _packet_generate._debug_dump_packet_fields(packet_path)


def trim_client_packet_pdf(client: Client, pages_to_remove: List[int]) -> Path:
    return _packet_trim.trim_client_packet_pdf(client, pages_to_remove)
