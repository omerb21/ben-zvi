from __future__ import annotations

from pathlib import Path
from typing import Dict, Optional

from app.models import NewProduct
from app.services.justification_b1 import _get_base_dir


KIT_ROOT = _get_base_dir() / "kits"

SUPPORTED_AUTO_FUND_TYPES = {"גמל", "גמל להשקעה", "השתלמות"}

FUND_TYPE_TEMPLATES: Dict[str, str] = {
    "גמל": "הצטרפות גמל קיט עצמאי מלא מוכן למערכת.pdf",
    "גמל להשקעה": "הצטרפות גמל להשקעה קיט עצמאי מלא מוכן למערכת.pdf",
    "השתלמות": "הצטרפות השתלמות קיט עצמאי מלא מוכן למערכת.pdf",
}

COMPANY_FOLDER_MAP: Dict[str, str] = {
    "הפניקס": "fnx",
    "אנליסט": "anlyst",
    "אלטשולר שחם": "as",
    "מיטב-דש": "ds",
    "מיטב דש": "ds",
    "מיטב": "ds",
    "מור": "mor",
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

    normalized_company = _normalize_company_name(company_name)

    for heb_name, folder_name in COMPANY_FOLDER_MAP.items():
        if not heb_name:
            continue
        normalized_key = _normalize_company_name(heb_name)
        if normalized_key and normalized_key in normalized_company:
            candidate = KIT_ROOT / folder_name
            if candidate.is_dir():
                return candidate
            resolved = _resolve_case_insensitive_dir(KIT_ROOT, folder_name)
            if resolved is not None:
                return resolved

    return None


def _kit_dir_for_product(np: NewProduct) -> Path:
    company_name = getattr(np, "company_name", "") or ""
    specific_folder = _kit_folder_for_company(company_name)
    if specific_folder is not None:
        return specific_folder
    return KIT_ROOT


def _select_template_for_product(np: NewProduct) -> Optional[Path]:
    fund_type = (getattr(np, "fund_type", "") or "").strip()
    if fund_type not in SUPPORTED_AUTO_FUND_TYPES:
        return None

    template_name = FUND_TYPE_TEMPLATES.get(fund_type)
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


def _get_template_path_or_raise(new_fund: NewProduct) -> Path:
    template_path_obj = _select_template_for_product(new_fund)
    kit_dir = _kit_dir_for_product(new_fund)
    if not template_path_obj or not template_path_obj.is_file():
        raise ValueError(
            f"NO_TEMPLATE_FOUND in folder {kit_dir} for fund type {new_fund.fund_type}"
        )
    return template_path_obj
