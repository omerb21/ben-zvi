from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Dict, Optional

from app.models import Client, NewProduct
from app.services.justification_b1 import _get_base_dir


KIT_ROOT = _get_base_dir() / "kits"

SUPPORTED_AUTO_FUND_TYPES = {"גמל", "גמל להשקעה", "השתלמות"}

FUND_TYPE_TEMPLATES: Dict[str, str] = {
    "גמל": "הצטרפות גמל קיט עצמאי מלא מוכן למערכת.pdf",
    "גמל להשקעה": "הצטרפות גמל להשקעה קיט עצמאי מלא מוכן למערכת.pdf",
    "השתלמות": "הצטרפות השתלמות קיט עצמאי מלא מוכן למערכת.pdf",
}

MOR_MINOR_INVESTMENT_TEMPLATE = "הצטרפות השתלמות קטין קיט עצמאי מלא מוכן למערכת.pdf"

COMPANY_FOLDER_MAP: Dict[str, str] = {
    "הפניקס": "fnx",
    "אנליסט": "anlyst",
    "אלטשולר שחם": "as",
    "מיטב-דש": "ds",
    "מיטב דש": "ds",
    "מיטב": "ds",
    "מור": "mor",
    "MOR": "mor",
    "אינפיניטי": "nfty",
    "ילין לפידות": "yl",
    "הראל": "harel",
}


def _normalize_company_name(value: str) -> str:
    if not value:
        return ""
    return (
        value.strip()
        .replace(" ", "")
        .replace("-", "")
        .replace("־", "")
        .replace("–", "")
        .replace("—", "")
    )


def _resolve_case_insensitive_dir(root: Path, folder_name: str) -> Optional[Path]:
    try:
        target = folder_name.casefold()
        for entry in root.iterdir():
            if entry.is_dir() and entry.name.casefold() == target:
                return entry
    except Exception:
        return None
    return None


def _kit_folder_for_company(company_name: str) -> Optional[Path]:
    if not company_name:
        return None

    folder_name = _folder_name_for_company(company_name)
    if folder_name is None:
        return None

    candidate = KIT_ROOT / folder_name
    if candidate.is_dir():
        return candidate
    return _resolve_case_insensitive_dir(KIT_ROOT, folder_name)


def _folder_name_for_company(company_name: str) -> Optional[str]:
    normalized_company = _normalize_company_name(company_name).casefold()
    for company_key, folder_name in COMPANY_FOLDER_MAP.items():
        normalized_key = _normalize_company_name(company_key).casefold()
        if normalized_key and normalized_key in normalized_company:
            return folder_name
    return None


def _kit_dir_for_product(np: NewProduct) -> Path:
    company_name = getattr(np, "company_name", "") or ""
    specific_folder = _kit_folder_for_company(company_name)
    if specific_folder is not None:
        return specific_folder
    return KIT_ROOT


def _is_minor(client: Client, today: date | None = None) -> bool:
    birth_date = getattr(client, "birth_date", None)
    if birth_date is None:
        return False

    reference_date = today or date.today()
    age = reference_date.year - birth_date.year
    if (reference_date.month, reference_date.day) < (birth_date.month, birth_date.day):
        age -= 1
    return age < 18


def _template_name_for_product(np: NewProduct, client: Client | None = None) -> Optional[str]:
    fund_type = (getattr(np, "fund_type", "") or "").strip()
    if fund_type not in SUPPORTED_AUTO_FUND_TYPES:
        return None

    company_name = (getattr(np, "company_name", "") or "").strip()
    company_folder_name = _folder_name_for_company(company_name)
    if (
        client is not None
        and fund_type == "גמל להשקעה"
        and company_folder_name == "mor"
        and _is_minor(client)
    ):
        return MOR_MINOR_INVESTMENT_TEMPLATE

    return FUND_TYPE_TEMPLATES.get(fund_type)


def _select_template_for_product(np: NewProduct, client: Client | None = None) -> Optional[Path]:
    fund_type = (getattr(np, "fund_type", "") or "").strip()
    if fund_type not in SUPPORTED_AUTO_FUND_TYPES:
        return None

    template_name = _template_name_for_product(np, client)
    if not template_name:
        return None

    kit_dir = _kit_dir_for_product(np)
    template_path = kit_dir / template_name
    if template_path.is_file():
        return template_path

    if kit_dir.is_dir():
        for entry in kit_dir.iterdir():
            if entry.suffix.lower() == ".pdf":
                return entry

    return None


def _get_template_path_or_raise(new_fund: NewProduct, client: Client | None = None) -> Path:
    template_path_obj = _select_template_for_product(new_fund, client)
    kit_dir = _kit_dir_for_product(new_fund)
    if not template_path_obj or not template_path_obj.is_file():
        raise ValueError(
            f"NO_TEMPLATE_FOUND in folder {kit_dir} for fund type {new_fund.fund_type}"
        )
    return template_path_obj
