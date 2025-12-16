from __future__ import annotations

import logging
from pathlib import Path
from typing import List, Tuple, Optional

from sqlalchemy.orm import Session
from pypdf import PdfWriter, PdfReader

from app.models import Client
from app.services import justification as justification_service
from app.services import justification_advice as justification_advice_service
from app.services import justification_b1 as justification_b1_service
from app.services import justification_kits as justification_kits_service
from app.services import justification_packet_parts_helpers as _helpers
from app.services import justification_packet_paths as _packet_paths
from app.services.justification_packet_fields import rename_kit_specific_fields as _rename_kit_specific_fields


logger = logging.getLogger("app.services.justification_packet")


def _try_pdf_reader(pdf_path: Path) -> Optional[PdfReader]:
    return _helpers._try_pdf_reader(pdf_path)


def _try_generate_missing(generate_fn, *, log_message: str, log_args: tuple) -> None:
    return _helpers._try_generate_missing(
        generate_fn,
        log_message=log_message,
        log_args=log_args,
    )


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

    return _helpers._get_kit_pdf_paths_for_client(db, client, generate_missing=generate_missing)


def _maybe_add_advice_part(
    db: Session,
    client: Client,
    *,
    parts: List[Path],
    generate_missing: bool,
) -> None:
    return _helpers._maybe_add_advice_part(
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
    return _helpers._maybe_add_b1_part(
        client,
        parts=parts,
        generate_missing=generate_missing,
    )


def _append_parts_to_writer(writer: PdfWriter, parts: List[Path]) -> bool:
    return _helpers._append_parts_to_writer(writer, parts)
