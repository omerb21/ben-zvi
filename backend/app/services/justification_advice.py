from __future__ import annotations

import logging
import time
from datetime import date
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import base64
import os

from jinja2 import Environment, FileSystemLoader, select_autoescape

logger = logging.getLogger(__name__)
from sqlalchemy.orm import Session

from app.models import Client, ExistingProduct, NewProduct
from app.services import justification_b1 as justification_b1_service
from app.services import justification_forms as justification_forms_service
from app.services import justification_advice_tables as advice_tables_service
from app.services import justification_advice_render as _advice_render
from app.services import justification_advice_pdf as _advice_pdf
from app.services.justification_kits import _fmt_date as _fmt_date_for_advice
from app.utils.filepaths import get_client_justification_filename
from app.utils.paths import get_backend_root as _get_backend_root
from app.utils.fs import ensure_dir as _ensure_dir


def _to_hebrew_marital_status(value: str | None) -> str:
    return _advice_render._to_hebrew_marital_status(value)


def _derive_employment_status_he(client: Client) -> str:
    return _advice_render._derive_employment_status_he(client)


def _derive_insurance_needs_he(_client: Client) -> str:
    return _advice_render._derive_insurance_needs_he(_client)


# Cache for static resources - loaded once at module level
_TEMPLATES_ENV: Optional[Environment] = None
_LOGO_DATA_URL: Optional[str] = None
_SIGNATURE_DATA_URL: Optional[str] = None
_STATIC_RESOURCES_LOADED = False
_WKHTMLTOPDF_CMD: Optional[str] = None
_WKHTMLTOPDF_CHECKED = False


def _get_client_export_dir(client: Client) -> Path:
    return _advice_render._get_client_export_dir(client)


def _get_advice_pdf_output_path(client: Client) -> Path:
    return _advice_pdf._get_advice_pdf_output_path(client)


def _encode_file_as_data_url(path: Path, mime_type: str) -> str:
    return _advice_render._encode_file_as_data_url(path, mime_type)


def _safe_encode_file_as_data_url(path: Path, mime_type: str, *, log_message: str) -> str:
    return _advice_render._safe_encode_file_as_data_url(path, mime_type, log_message=log_message)


def _get_templates_env() -> Environment:
    global _TEMPLATES_ENV
    env = _advice_render._get_templates_env()
    _TEMPLATES_ENV = env
    return env


def _load_static_resources():
    global _LOGO_DATA_URL, _SIGNATURE_DATA_URL, _STATIC_RESOURCES_LOADED
    logo, signature = _advice_render._load_static_resources()
    _LOGO_DATA_URL = _advice_render._LOGO_DATA_URL
    _SIGNATURE_DATA_URL = _advice_render._SIGNATURE_DATA_URL
    _STATIC_RESOURCES_LOADED = _advice_render._STATIC_RESOURCES_LOADED
    return logo, signature


def _load_client_signature_data_url(client: Client) -> str:
    return _advice_render._load_client_signature_data_url(client)


def _get_replaced_existing_ids(existing_products_list, new_products_list) -> set:
    return _advice_render._get_replaced_existing_ids(existing_products_list, new_products_list)


def build_advice_html(db: Session, client: Client, include_print_button: bool = True) -> str:
    return _advice_render.build_advice_html(db, client, include_print_button=include_print_button)


def _get_wkhtmltopdf_cmd() -> Optional[str]:
    global _WKHTMLTOPDF_CMD, _WKHTMLTOPDF_CHECKED
    cmd = _advice_pdf._get_wkhtmltopdf_cmd()
    _WKHTMLTOPDF_CMD = _advice_pdf._WKHTMLTOPDF_CMD
    _WKHTMLTOPDF_CHECKED = _advice_pdf._WKHTMLTOPDF_CHECKED
    return cmd


def _safe_unlink(path: Path) -> None:
    return _advice_pdf._safe_unlink(path)


def generate_advice_pdf(html: str) -> Optional[bytes]:
    return _advice_pdf.generate_advice_pdf(html)


def save_advice_pdf_for_client(db: Session, client: Client) -> None:
    """(Re)generate the advice PDF for a client and save it to the
    standard export path. If generation fails, this function does
    nothing and does not raise.

    Used after the client has signed, so that the advice PDF can
    include the client's signature image when available.
    """
    return _advice_pdf.save_advice_pdf_for_client(db, client)
