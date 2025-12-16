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
from app.services import justification_packet_paths as _packet_paths
from app.services.justification_packet_fields import rename_kit_specific_fields as _rename_kit_specific_fields


logger = logging.getLogger("app.services.justification_packet")


def _try_pdf_reader(pdf_path: Path) -> Optional[PdfReader]:
    try:
        return PdfReader(str(pdf_path))
    except Exception:
        return None


def _try_generate_missing(generate_fn, *, log_message: str, log_args: tuple) -> None:
    try:
        generate_fn()
    except Exception:
        logger.exception(log_message, *log_args)


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

    export_dir = _packet_paths._get_export_dir(client)

    new_products = justification_service.list_new_products_for_client(db, client.id)
    sorted_products = sorted(new_products, key=lambda p: getattr(p, "id", 0))

    seen_existing_ids = set()
    target_products = []

    for product in sorted_products:
        existing_id = getattr(product, "existing_product_id", None)
        if existing_id is not None:
            if existing_id in seen_existing_ids:
                continue
            seen_existing_ids.add(existing_id)
            target_products.append(product)
        else:
            target_products.append(product)

    kit_paths: List[Path] = []

    for product in target_products:
        new_product_id = product.id
        edited_path, auto_path = _packet_paths._get_kit_paths(export_dir, client.id, new_product_id)

        if generate_missing and not edited_path.is_file() and not auto_path.is_file():
            _try_generate_missing(
                lambda: justification_kits_service.generate_kit_pdf_for_new_product(
                    db,
                    client.id,
                    new_product_id,
                ),
                log_message="[PACKET] Failed to auto-generate kit PDF for client_id=%s new_product_id=%s",
                log_args=(getattr(client, "id", None), new_product_id),
            )

        if edited_path.is_file():
            kit_paths.append(edited_path)
        elif auto_path.is_file():
            kit_paths.append(auto_path)

    return kit_paths


def _maybe_add_advice_part(
    db: Session,
    client: Client,
    *,
    parts: List[Path],
    generate_missing: bool,
) -> None:
    advice_path = _packet_paths._get_advice_pdf_path(client)
    if advice_path.is_file():
        parts.append(advice_path)
        return

    if not generate_missing:
        return

    _try_generate_missing(
        lambda: justification_advice_service.save_advice_pdf_for_client(db, client),
        log_message="[PACKET] Failed to generate advice PDF for client_id=%s while building packet",
        log_args=(getattr(client, "id", None),),
    )

    if advice_path.is_file():
        parts.append(advice_path)


def _maybe_add_b1_part(
    client: Client,
    *,
    parts: List[Path],
    generate_missing: bool,
) -> None:
    b1_candidates = _packet_paths._get_b1_pdf_candidates(client)
    if not b1_candidates and generate_missing:
        _try_generate_missing(
            lambda: justification_b1_service.generate_b1_pdf_for_client(client),
            log_message="[PACKET] Failed to generate B1 PDF for client_id=%s while building packet",
            log_args=(getattr(client, "id", None),),
        )
        b1_candidates = _packet_paths._get_b1_pdf_candidates(client)

    if b1_candidates:
        parts.append(b1_candidates[0])


def _append_parts_to_writer(writer: PdfWriter, parts: List[Path]) -> bool:
    has_pages = False
    kit_index = 1

    for pdf_path in parts:
        reader = _try_pdf_reader(pdf_path)
        if reader is None:
            continue

        if pdf_path.name.startswith("kit_"):
            try:
                _rename_kit_specific_fields(reader, f"kit{kit_index}_")
            except Exception:
                pass
            kit_index += 1

        try:
            writer.append(reader)
            has_pages = True
        except Exception:
            continue

    return has_pages
