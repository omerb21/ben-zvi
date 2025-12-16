from __future__ import annotations

import base64
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, select_autoescape

from app.models import Client
from app.services import justification_b1 as justification_b1_service


def to_hebrew_marital_status(value: str | None) -> str:
    text = (value or "").strip()
    if not text:
        return ""

    lowered = text.lower()
    if lowered in {"single", "unmarried"}:
        return "רווק/ה"
    if lowered == "married":
        return "נשוי/ה"
    if lowered == "divorced":
        return "גרוש/ה"
    if lowered in {"widowed", "widow", "widower"}:
        return "אלמן/ה"

    return text


def derive_employment_status_he(client: Client, logger) -> str:
    try:
        if getattr(client, "self_employed", False):
            return "עצמאי"
        if getattr(client, "current_employer_exists", False):
            return "שכיר"
    except Exception:
        logger.exception(
            "[ADVICE] Failed to derive employment status for client_id=%s",
            getattr(client, "id", None),
        )
        return ""

    return ""


def derive_insurance_needs_he(_client: Client) -> str:
    return ""


def get_client_export_dir(client: Client) -> Path:
    return justification_b1_service._get_client_export_dir(client)


def encode_file_as_data_url(path: Path, mime_type: str) -> str:
    if not path.is_file():
        return ""

    data = path.read_bytes()
    b64 = base64.b64encode(data).decode("ascii")
    return f"data:{mime_type};base64,{b64}"


def safe_encode_file_as_data_url(path: Path, mime_type: str, *, logger, log_message: str) -> str:
    try:
        return encode_file_as_data_url(path, mime_type)
    except Exception:
        logger.exception(log_message)
        return ""


def build_templates_env(base_dir: Path) -> Environment:
    templates_dir = base_dir / "templates"
    env = Environment(
        loader=FileSystemLoader(str(templates_dir)),
        autoescape=select_autoescape(["html", "xml"]),
    )

    def _url_for(endpoint: str, filename: str) -> str:
        if endpoint == "static":
            return f"/static/{filename}"
        return filename

    env.globals["url_for"] = _url_for
    return env


def load_static_resources(base_dir: Path, *, logger) -> tuple[str, str]:
    logo_path = base_dir / "static" / "logo.png"
    logo_data_url = safe_encode_file_as_data_url(
        logo_path,
        "image/png",
        logger=logger,
        log_message="[ADVICE] Failed to load logo image for advice templates",
    )

    primary_sign_path = base_dir / "static" / "signature.jpg"
    fallback_sign_path = base_dir / "static" / "sign.jpg"
    sign_path = primary_sign_path if primary_sign_path.is_file() else fallback_sign_path

    signature_data_url = safe_encode_file_as_data_url(
        sign_path,
        "image/jpeg",
        logger=logger,
        log_message="[ADVICE] Failed to load signature image for advice templates",
    )

    return logo_data_url or "", signature_data_url or ""


def load_client_signature_data_url(client: Client) -> str:
    try:
        export_dir = get_client_export_dir(client)
        client_sig_path = export_dir / "client_signature.png"
        return encode_file_as_data_url(client_sig_path, "image/png")
    except Exception:
        return ""

    return ""


def get_replaced_existing_ids(existing_products_list, new_products_list) -> set:
    replaced_existing_ids = set()

    for np in new_products_list:
        ep_id = np.existing_product_id
        if ep_id is not None:
            replaced_existing_ids.add(ep_id)

    for ex in existing_products_list:
        if hasattr(ex, "new_products") and ex.new_products:
            replaced_existing_ids.add(ex.id)

    return replaced_existing_ids
