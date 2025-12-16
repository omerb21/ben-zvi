from __future__ import annotations

from pathlib import Path
from typing import Any, Callable, Dict, Optional, Tuple

from sqlalchemy.orm import Session

from app.models import Client, ExistingProduct, NewProduct
from app.services import justification_kits_generate as _kits_generate
from app.services import justification_kits_payloads as _kits_payloads
from app.services import justification_kits_templates as _kits_templates


KIT_ROOT = _kits_templates.KIT_ROOT

SUPPORTED_AUTO_FUND_TYPES = _kits_templates.SUPPORTED_AUTO_FUND_TYPES

FUND_TYPE_TEMPLATES: Dict[str, str] = _kits_templates.FUND_TYPE_TEMPLATES

COMPANY_FOLDER_MAP: Dict[str, str] = _kits_templates.COMPANY_FOLDER_MAP


def _rb(condition: bool) -> str:
    return _kits_payloads._rb(condition)


def _normalize_hebrew_value(value: Any) -> Any:
    if not isinstance(value, str):
        return _kits_payloads._normalize_hebrew_value(value)
    # For kits we keep Hebrew text in logical order and let the PDF viewer
    # handle right-to-left layout, without reversing or adding marks.
    return _kits_payloads._normalize_hebrew_value(value)


def _normalize_payload(
    payload: Dict[str, Any],
    normalize_value_fn: Callable[[Any], Any],
) -> Dict[str, Any]:
    return _kits_payloads._normalize_payload(payload, normalize_value_fn)


def _normalize_hebrew_payload(payload: Dict[str, Any]) -> Dict[str, Any]:
    return _kits_payloads._normalize_hebrew_payload(payload)


def _normalize_hebrew_value_reversed(value: Any) -> Any:
    return _kits_payloads._normalize_hebrew_value_reversed(value)


def _normalize_hebrew_payload_reversed(payload: Dict[str, Any]) -> Dict[str, Any]:
    return _kits_payloads._normalize_hebrew_payload_reversed(payload)


def _kit_folder_for_company(company_name: str) -> Optional[Path]:
    return _kits_templates._kit_folder_for_company(company_name)


def _kit_dir_for_product(np: NewProduct) -> Path:
    return _kits_templates._kit_dir_for_product(np)


def _select_template_for_product(np: NewProduct) -> Optional[Path]:
    return _kits_templates._select_template_for_product(np)


def sanitize_filename(filename: str) -> str:
    return _kits_payloads.sanitize_filename(filename)


def _fmt_date(dt: Any) -> str:
    return _kits_payloads._fmt_date(dt)


def build_common_fields(client: Client) -> Dict[str, Any]:
    return _kits_payloads.build_common_fields(client)


def build_fund_fields(new_fund: NewProduct, old_fund: Optional[ExistingProduct] = None) -> Dict[str, Any]:
    return _kits_payloads.build_fund_fields(new_fund, old_fund)


def build_full_payload(client: Client, new_fund: NewProduct, old_fund: Optional[ExistingProduct] = None) -> Dict[str, Any]:
    return _kits_payloads.build_full_payload(client, new_fund, old_fund)


def build_full_payload_overlay(
    client: Client, new_fund: NewProduct, old_fund: Optional[ExistingProduct] = None
) -> Dict[str, Any]:
    return _kits_payloads.build_full_payload_overlay(client, new_fund, old_fund)


def _build_full_payload_with_normalizer(
    client: Client,
    new_fund: NewProduct,
    old_fund: Optional[ExistingProduct],
    normalize_payload_fn: Callable[[Dict[str, Any]], Dict[str, Any]],
) -> Dict[str, Any]:
    return _kits_payloads._build_full_payload_with_normalizer(
        client,
        new_fund,
        old_fund,
        normalize_payload_fn,
    )


def _get_client_and_new_fund_or_raise(
    db: Session,
    client_id: int,
    new_product_id: int,
) -> Tuple[Client, NewProduct]:
    return _kits_generate._get_client_and_new_fund_or_raise(db, client_id, new_product_id)


def _get_old_fund_or_placeholder(
    db: Session,
    client: Client,
    new_fund: NewProduct,
) -> ExistingProduct:
    return _kits_generate._get_old_fund_or_placeholder(db, client, new_fund)


def _get_template_path_or_raise(new_fund: NewProduct) -> Path:
    return _kits_templates._get_template_path_or_raise(new_fund)


def _fill_pdf_to_bytes(
    template_path: Path,
    payload: Dict[str, Any],
    out_path: Path,
    field_name_prefix: str | None,
) -> bytes:
    return _kits_generate._fill_pdf_to_bytes(template_path, payload, out_path, field_name_prefix)


def _get_auto_kit_output_path(client: Client, client_id: int, new_product_id: int) -> tuple[Path, str, Path]:
    return _kits_generate._get_auto_kit_output_path(client, client_id, new_product_id)


def _get_overlay_kit_output_path(
    client: Client,
    new_fund: NewProduct,
    *,
    new_product_id: int,
) -> tuple[Path, str, Path]:
    return _kits_generate._get_overlay_kit_output_path(
        client,
        new_fund,
        new_product_id=new_product_id,
    )


def _load_kit_generation_context_or_raise(
    db: Session,
    client_id: int,
    new_product_id: int,
) -> Tuple[Client, NewProduct, ExistingProduct, Path]:
    return _kits_generate._load_kit_generation_context_or_raise(db, client_id, new_product_id)


def _generate_kit_pdf(db: Session, client_id: int, new_product_id: int, *, overlay: bool) -> Tuple[bytes, str]:
    return _kits_generate._generate_kit_pdf(db, client_id, new_product_id, overlay=overlay)


def generate_kit_pdf_for_new_product(
    db: Session, client_id: int, new_product_id: int
) -> Tuple[bytes, str]:
    return _kits_generate.generate_kit_pdf_for_new_product(db, client_id, new_product_id)


def generate_kit_pdf_for_new_product_overlay(
    db: Session, client_id: int, new_product_id: int
) -> Tuple[bytes, str]:
    return _kits_generate.generate_kit_pdf_for_new_product_overlay(db, client_id, new_product_id)
