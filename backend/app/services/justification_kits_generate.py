from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

from sqlalchemy.orm import Session

from app.models import Client, ExistingProduct, NewProduct
from app.services import justification_kits_payloads as _kits_payloads
from app.services import justification_kits_templates as _templates
from app.services.justification_b1 import _get_client_export_dir
from app.services.pdf_fill_safe import fill_form_auto


def _get_client_and_new_fund_or_raise(
    db: Session,
    client_id: int,
    new_product_id: int,
) -> Tuple[Client, NewProduct]:
    client = db.query(Client).filter(Client.id == client_id).first()
    if not client:
        raise ValueError("CLIENT_NOT_FOUND")

    new_fund = db.query(NewProduct).filter(NewProduct.id == new_product_id).first()
    if not new_fund:
        raise ValueError("NEW_PRODUCT_NOT_FOUND")

    if new_fund.client_id != client.id:
        raise ValueError("PRODUCT_DOES_NOT_BELONG_TO_CLIENT")

    if new_fund.fund_type not in _templates.SUPPORTED_AUTO_FUND_TYPES:
        raise ValueError("UNSUPPORTED_FUND_TYPE")

    return client, new_fund


def _get_old_fund_or_placeholder(
    db: Session,
    client: Client,
    new_fund: NewProduct,
) -> ExistingProduct:
    old_fund: Optional[ExistingProduct] = None
    if new_fund.existing_product_id is not None:
        old_fund = (
            db.query(ExistingProduct)
            .filter(ExistingProduct.id == new_fund.existing_product_id)
            .first()
        )

    if old_fund is None:
        old_fund = ExistingProduct(
            client_id=client.id,
            fund_type="",
            company_name="",
            fund_name="",
            fund_code="",
            personal_number="",
        )

    return old_fund


def _fill_pdf_to_bytes(
    template_path: Path,
    payload: Dict[str, Any],
    out_path: Path,
    field_name_prefix: str | None,
) -> bytes:
    pdf_path = fill_form_auto(
        str(template_path),
        payload,
        out_path,
        field_name_prefix=field_name_prefix,
    )
    return Path(pdf_path).read_bytes()


def _get_auto_kit_output_path(client: Client, client_id: int, new_product_id: int) -> tuple[Path, str, Path]:
    export_dir = _get_client_export_dir(client)
    output_filename = f"kit_{client_id}_{new_product_id}.pdf"
    out_path = export_dir / output_filename
    return export_dir, output_filename, out_path


def _get_overlay_kit_output_path(
    client: Client,
    new_fund: NewProduct,
    *,
    new_product_id: int,
) -> tuple[Path, str, Path]:
    fund_name = getattr(new_fund, "fund_name", f"fund_{new_product_id}") or ""
    safe_fund_name = _kits_payloads.sanitize_filename(fund_name)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_filename = f"{safe_fund_name}_{timestamp}_overlay.pdf"

    export_dir = _get_client_export_dir(client)
    out_path = export_dir / output_filename
    return export_dir, output_filename, out_path


def _load_kit_generation_context_or_raise(
    db: Session,
    client_id: int,
    new_product_id: int,
) -> Tuple[Client, NewProduct, ExistingProduct, Path]:
    client, new_fund = _get_client_and_new_fund_or_raise(db, client_id, new_product_id)
    old_fund = _get_old_fund_or_placeholder(db, client, new_fund)
    template_path_obj = _templates._get_template_path_or_raise(new_fund, client)
    return client, new_fund, old_fund, template_path_obj


def _generate_kit_pdf(db: Session, client_id: int, new_product_id: int, *, overlay: bool) -> Tuple[bytes, str]:
    client, new_fund, old_fund, template_path_obj = _load_kit_generation_context_or_raise(
        db, client_id, new_product_id
    )

    if overlay:
        _export_dir, output_filename, out_path = _get_overlay_kit_output_path(
            client,
            new_fund,
            new_product_id=new_product_id,
        )
        payload = _kits_payloads.build_full_payload_overlay(client, new_fund, old_fund)
        field_name_prefix = f"kit_{client_id}_{new_product_id}_"
    else:
        _export_dir, output_filename, out_path = _get_auto_kit_output_path(
            client,
            client_id,
            new_product_id,
        )
        payload = _kits_payloads.build_full_payload(client, new_fund, old_fund)
        field_name_prefix = None

    data = _fill_pdf_to_bytes(
        template_path_obj,
        payload,
        out_path,
        field_name_prefix=field_name_prefix,
    )
    return data, output_filename


def generate_kit_pdf_for_new_product(
    db: Session, client_id: int, new_product_id: int
) -> Tuple[bytes, str]:
    return _generate_kit_pdf(db, client_id, new_product_id, overlay=False)


def generate_kit_pdf_for_new_product_overlay(
    db: Session, client_id: int, new_product_id: int
) -> Tuple[bytes, str]:
    return _generate_kit_pdf(db, client_id, new_product_id, overlay=True)
