from __future__ import annotations

import logging
import time
from pathlib import Path
from typing import List, Tuple

from sqlalchemy.orm import Session
from pypdf import PdfWriter, PdfReader

from app.models import Client
from app.utils.fs import ensure_dir as _ensure_dir
from app.services import justification_packet_parts as _packet_parts
from app.services import justification_packet_paths as _packet_paths
from app.services.justification_packet_fields import (
    make_packet_field_names_unique_in_file as _make_packet_field_names_unique_in_file_impl,
)


logger = logging.getLogger("app.services.justification_packet")


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
    start_time = time.time()
    export_dir = _packet_paths._get_export_dir(client)
    _ensure_dir(export_dir)

    parts: List[Path] = []

    _packet_parts._maybe_add_advice_part(db, client, parts=parts, generate_missing=generate_missing)
    _packet_parts._maybe_add_b1_part(client, parts=parts, generate_missing=generate_missing)

    kit_paths = _packet_parts._get_kit_pdf_paths_for_client(db, client, generate_missing=generate_missing)
    parts.extend(kit_paths)

    if not parts:
        raise ValueError("NO_PDFS_FOR_CLIENT_PACKET")

    packet_path, _edited_packet_path = _packet_paths._get_packet_paths(export_dir, client.id)
    packet_filename = packet_path.name

    writer = PdfWriter()
    has_pages = _packet_parts._append_parts_to_writer(writer, parts)

    if not has_pages:
        raise ValueError("NO_PAGES_IN_CLIENT_PACKET")

    try:
        writer.write(str(packet_path))
    except Exception as exc:
        raise ValueError(f"FAILED_TO_WRITE_PACKET:{exc}")

    _debug_dump_packet_fields(packet_path)

    data = packet_path.read_bytes()
    elapsed = time.time() - start_time
    logger.info(f"[PDF-TIMING] Packet generated in {elapsed:.2f}s, parts={len(parts)}, size={len(data)} bytes")
    return data, packet_filename


def _make_packet_field_names_unique_in_file(packet_path: Path) -> None:
    _make_packet_field_names_unique_in_file_impl(packet_path)


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
    pass
