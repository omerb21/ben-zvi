from __future__ import annotations

import base64
import logging
from datetime import date
from pathlib import Path
from typing import Any, Dict, List, Optional

from jinja2 import Environment, FileSystemLoader, select_autoescape
from sqlalchemy.orm import Session

from app.models import Client
from app.services import justification_b1 as justification_b1_service
from app.services import justification_forms as justification_forms_service
from app.services import justification_advice_tables as advice_tables_service
from app.services import justification_advice_render_helpers as _helpers
from app.services.justification_kits import _fmt_date as _fmt_date_for_advice


logger = logging.getLogger("app.services.justification_advice")


_TEMPLATES_ENV: Optional[Environment] = None
_LOGO_DATA_URL: Optional[str] = None
_SIGNATURE_DATA_URL: Optional[str] = None
_STATIC_RESOURCES_LOADED = False


def _to_hebrew_marital_status(value: str | None) -> str:
    return _helpers.to_hebrew_marital_status(value)


def _derive_employment_status_he(client: Client) -> str:
    # Prefer explicit flags on the unified Client model. If none apply, return
    # an empty string so the template can show its Hebrew fallback.
    return _helpers.derive_employment_status_he(client, logger)


def _derive_insurance_needs_he(_client: Client) -> str:
    # Currently there is no structured field for insurance needs on Client.
    # Return an empty string so the template can substitute a Hebrew fallback
    # ("לא צוין").
    return _helpers.derive_insurance_needs_he(_client)


def _get_client_export_dir(client: Client) -> Path:
    return _helpers.get_client_export_dir(client)


def _encode_file_as_data_url(path: Path, mime_type: str) -> str:
    return _helpers.encode_file_as_data_url(path, mime_type)


def _safe_encode_file_as_data_url(path: Path, mime_type: str, *, log_message: str) -> str:
    return _helpers.safe_encode_file_as_data_url(
        path,
        mime_type,
        logger=logger,
        log_message=log_message,
    )


def _get_templates_env() -> Environment:
    global _TEMPLATES_ENV
    if _TEMPLATES_ENV is not None:
        return _TEMPLATES_ENV

    base_dir = justification_forms_service._get_app_base_dir()
    env = _helpers.build_templates_env(base_dir)
    _TEMPLATES_ENV = env
    return env


def _load_static_resources():
    """Load static resources (logo, signature) once and cache them."""
    global _LOGO_DATA_URL, _SIGNATURE_DATA_URL, _STATIC_RESOURCES_LOADED

    if _STATIC_RESOURCES_LOADED:
        return _LOGO_DATA_URL, _SIGNATURE_DATA_URL

    base_dir = justification_forms_service._get_app_base_dir()

    _LOGO_DATA_URL, _SIGNATURE_DATA_URL = _helpers.load_static_resources(base_dir, logger=logger)

    _STATIC_RESOURCES_LOADED = True
    return _LOGO_DATA_URL or "", _SIGNATURE_DATA_URL or ""


def _load_client_signature_data_url(client: Client) -> str:
    return _helpers.load_client_signature_data_url(client)


def _get_replaced_existing_ids(existing_products_list, new_products_list) -> set:
    return _helpers.get_replaced_existing_ids(existing_products_list, new_products_list)


def build_advice_html(db: Session, client: Client, include_print_button: bool = True) -> str:
    tables = advice_tables_service.build_tables(client)
    coverage_tables = advice_tables_service.build_coverage_tables(db, client, tables)

    marital_status_he = _to_hebrew_marital_status(getattr(client, "marital_status", None))
    employment_status_he = _derive_employment_status_he(client)
    insurance_needs_he = _derive_insurance_needs_he(client)

    existing_products_list = list(client.existing_products or [])
    new_products_list = list(client.new_products or [])

    # DEBUG: Log all products and their links
    logger.info(f"[ADVICE-DEBUG] Client {client.id}: {len(existing_products_list)} existing, {len(new_products_list)} new")
    for ex in existing_products_list:
        linked_new = getattr(ex, 'new_products', []) or []
        logger.info(f"[ADVICE-DEBUG] ExistingProduct id={ex.id} fund={ex.fund_name} has {len(linked_new)} linked new products")
    for np in new_products_list:
        logger.info(f"[ADVICE-DEBUG] NewProduct id={np.id} fund={np.fund_name} existing_product_id={np.existing_product_id}")

    # Existing products that remain in the "new" state (i.e. not replaced).
    # A product is considered "replaced" when there is at least one new
    # product that is explicitly linked to it via existing_product_id,
    # regardless of fund type.
    #
    # We use two methods to identify replaced products:
    # 1. Check existing_product_id on each new product
    # 2. Check the new_products relationship on each existing product
    replaced_existing_ids = _get_replaced_existing_ids(existing_products_list, new_products_list)

    logger.info(f"[ADVICE-DEBUG] Replaced existing IDs: {replaced_existing_ids}")

    remaining_existing_products = [
        ex
        for ex in existing_products_list
        if ex.id not in replaced_existing_ids
    ]

    logger.info(f"[ADVICE-DEBUG] Remaining (not replaced): {[ex.id for ex in remaining_existing_products]}")

    client_view: Dict[str, Any] = {
        "first_name": client.first_name or "",
        "last_name": client.last_name or "",
        "national_id": client.id_number or "",
        "date_of_birth": client.birth_date,
        "date_of_birth_text": _fmt_date_for_advice(client.birth_date),
        "retirement_income": None,
        "existing_products": existing_products_list,
        "new_products": new_products_list,
        "existing_products_state_new": remaining_existing_products,
    }

    if marital_status_he:
        client_view["marital_status"] = marital_status_he
    if employment_status_he:
        client_view["employment_status"] = employment_status_he
    if insurance_needs_he:
        client_view["insurance_needs"] = insurance_needs_he

    env = _get_templates_env()
    template = env.get_template("advice/print.html")
    now = date.today()

    # Use cached static resources
    logo_data_url, signature_data_url = _load_static_resources()

    # Client signature (from signing flow), if available as PNG in the
    # client's export directory. This is used to render the client's
    # signature image in the advice document at the designated locations.
    client_signature_data_url = _load_client_signature_data_url(client)

    html = template.render(
        client=client_view,
        tables=tables,
        coverage_tables=coverage_tables,
        now=now,
        logo_data_url=logo_data_url,
        signature_data_url=signature_data_url,
        client_signature_data_url=client_signature_data_url,
        show_print_button=include_print_button,
    )
    return html
