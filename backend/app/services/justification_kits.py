from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

import pytz
from sqlalchemy.orm import Session

from app.models import Client, ExistingProduct, NewProduct
from app.services.justification_b1 import _get_client_export_dir, _get_base_dir
from app.services.pdf_fill_safe import fill_form_auto


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
    "מור": "mor",
    "אינפיניטי": "nfty",
    "ילין לפידות": "yl",
}


def _rb(condition: bool) -> str:
    return "/Yes" if condition else "/Off"


def _contains_hebrew(text: str) -> bool:
    for ch in text:
        if "\u0590" <= ch <= "\u05FF":
            return True
    return False


def _normalize_hebrew_value(value: Any) -> Any:
    if not isinstance(value, str):
        return value
    # For kits we keep Hebrew text in logical order and let the PDF viewer
    # handle right-to-left layout, without reversing or adding marks.
    return value


def _normalize_hebrew_payload(payload: Dict[str, Any]) -> Dict[str, Any]:
    for key, val in list(payload.items()):
        payload[key] = _normalize_hebrew_value(val)
    return payload


def _normalize_hebrew_value_reversed(value: Any) -> Any:
    if not isinstance(value, str):
        return value
    if not value:
        return value
    if _contains_hebrew(value):
        return value[::-1]
    return value


def _normalize_hebrew_payload_reversed(payload: Dict[str, Any]) -> Dict[str, Any]:
    for key, val in list(payload.items()):
        payload[key] = _normalize_hebrew_value_reversed(val)
    return payload


def _kit_folder_for_company(company_name: str) -> Optional[Path]:
    if not company_name:
        return None

    for heb_name, folder_name in COMPANY_FOLDER_MAP.items():
        if heb_name in company_name:
            candidate = KIT_ROOT / folder_name
            if candidate.is_dir():
                return candidate

    return None


def _kit_dir_for_product(np: NewProduct) -> Path:
    company_name = getattr(np, "company_name", "") or ""
    specific_folder = _kit_folder_for_company(company_name)
    if specific_folder is not None:
        return specific_folder
    return KIT_ROOT


def _select_template_for_product(np: NewProduct) -> Optional[Path]:
    if np.fund_type not in SUPPORTED_AUTO_FUND_TYPES:
        return None

    template_name = FUND_TYPE_TEMPLATES.get(np.fund_type)
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


def sanitize_filename(filename: str) -> str:
    invalid_chars = '<>:"\\/|?*'
    for char in invalid_chars:
        filename = filename.replace(char, "_")
    return filename.strip(". ")


def _fmt_date(dt: Any) -> str:
    if not dt:
        return ""
    try:
        return dt.strftime("%d/%m/%Y")
    except Exception:
        return str(dt)


def build_common_fields(client: Client) -> Dict[str, Any]:
    tz = pytz.timezone("Asia/Jerusalem")

    payload: Dict[str, Any] = {}

    payload.update(
        {
            "today": datetime.now(tz).strftime("%d/%m/%Y"),
            "Date": datetime.now(tz).strftime("%d/%m/%Y"),
            "Today": datetime.now(tz).strftime("%d/%m/%Y"),
        }
    )

    payload.update(
        {
            "first_name": client.first_name,
            "last_name": client.last_name,
            "full_name": f"{client.first_name or ''} {client.last_name or ''}",
            "ClientFirstName": client.first_name,
            "ClientLastName": client.last_name,
            "client_last_name": client.last_name,
            "client_full_name": f"{client.first_name or ''} {client.last_name or ''}",
        }
    )

    id_number = client.id_number or ""
    payload.update(
        {
            "id": id_number,
            "national_id": id_number,
            "text_3ueyg": id_number,
            "client_id": id_number,
            "ClientId": id_number,
            "ClientID": id_number,
            "ID": id_number,
            "id_number": id_number,
            "ClientBdate": _fmt_date(client.birth_date),
            "birth_date": _fmt_date(client.birth_date),
        }
    )

    payload.update(
        {
            "phone": client.phone,
            "mobile": client.phone,
            "Clientphone": client.phone,
            "email": client.email,
            "clientemail": client.email,
            "Clientemail": client.email,
        }
    )

    payload.update(
        {
            "male": _rb(client.gender == "זכר"),
            "Male": _rb(client.gender == "זכר"),
            "female": _rb(client.gender == "נקבה"),
            "Female": _rb(client.gender == "נקבה"),
            "client_gender_male": _rb(client.gender == "זכר"),
            "client_gender_female": _rb(client.gender == "נקבה"),
        }
    )

    payload.update(
        {
            "single": _rb(client.marital_status in ("רווק", "רווקה")),
            "Single": _rb(client.marital_status in ("רווק", "רווקה")),
            "married": _rb(client.marital_status == "נשוי"),
            "Married": _rb(client.marital_status == "נשוי"),
            "divorced": _rb(client.marital_status == "גרוש"),
            "Divorced": _rb(client.marital_status == "גרוש"),
            "widowed": _rb(client.marital_status == "אלמן"),
            "client_married": _rb(client.marital_status == "נשוי"),
            "client_single": _rb(client.marital_status == "רווק"),
        }
    )

    city = client.address_city or ""
    street = client.address_street or ""
    house_number = client.address_house_number or ""
    apartment = client.address_apartment or ""
    zip_code = client.address_postal_code or ""

    payload.update(
        {
            "city": city,
            "client_city": city,
            "clientcity": city,
            "Clientcity": city,
            "street": street,
            "clientstreet": street,
            "house_number": house_number,
            "clienthousenbr": house_number,
            "Clienthousenbr": house_number,
            "apartment": apartment,
            "clientflatnbr": apartment,
            "Clientflatnbr": apartment,
            "zip_code": zip_code,
            "clientzipcode": zip_code,
        }
    )

    payload.update(
        {
            "Clientemployer": client.employer_name,
            "Clientemployeraddress": client.employer_address,
            "Clientemployerhp": client.employer_hp,
            "Clientemployerphone": client.employer_phone,
            "employer_name": client.employer_name,
            "TaxId": client.employer_hp,
            "employer_tax_id": client.employer_hp,
            "employer_address": client.employer_address,
            "employerphone": client.employer_phone,
        }
    )

    return payload


def build_fund_fields(new_fund: NewProduct, old_fund: Optional[ExistingProduct] = None) -> Dict[str, Any]:
    def rb(condition: bool) -> str:
        return "/Yes" if condition else "/Off"

    payload: Dict[str, Any] = {}

    emp = (
        getattr(new_fund, "employment_status", None)
        or getattr(new_fund, "employment_type", None)
        or ""
    )

    payload.update(
        {
            "employ": rb(emp == "שכיר"),
            "indipendent": rb(emp == "עצמאי"),
            "baalshlita": rb(emp == "שכיר בעל שליטה"),
            "indiploy": rb(emp == "עצמאי באמצעות מעסיק"),
            "known": "Yes",
        }
    )

    payload.update(
        {
            "management_fee": getattr(new_fund, "management_fee_balance", ""),
            "management_fee_balance": getattr(new_fund, "management_fee_balance", ""),
            "dmnsum": str(getattr(new_fund, "management_fee_balance", "")),
            "EmploymentType": emp,
            "new_fund_type": new_fund.fund_type,
            "new_fund_company": new_fund.company_name,
            "new_fund_name": new_fund.fund_name,
            "new_fund_code": new_fund.fund_code,
            "new_personal_number": new_fund.personal_number,
            "yield_1yr": new_fund.yield_1yr,
            "yield_3yr": new_fund.yield_3yr,
            "ProductName": new_fund.fund_name,
            "ProductType": new_fund.fund_type,
            "ProductCode": new_fund.fund_code,
        }
    )

    if old_fund:
        payload.update(
            {
                "fund_type": old_fund.fund_type,
                "fund_company": old_fund.company_name,
                "fund_name": old_fund.fund_name,
                "fund_code": old_fund.fund_code,
                "personal_number": old_fund.personal_number,
                "company_name": old_fund.company_name,
                "existing_fund_type": old_fund.fund_type,
                "existing_fund_company": old_fund.company_name,
                "existing_fund_name": old_fund.fund_name,
                "existing_fund_code": old_fund.fund_code,
                "existing_management_fee": getattr(old_fund, "management_fee_balance", ""),
            }
        )

        if hasattr(old_fund, "has_regular_contributions"):
            dep_field = "depyes" if old_fund.has_regular_contributions else "depno"
            for cb in {"depyes", "depno"}:
                payload[cb] = "/Yes" if cb == dep_field else "/Off"

    deposit_status = getattr(new_fund, "deposit_status", "")
    if deposit_status:
        payload.update(
            {
                "one_time": rb(deposit_status == "חד פעמי"),
                "monthly": rb(deposit_status == "חודשי"),
                "deposit_amount": getattr(new_fund, "deposit_amount", ""),
            }
        )

    return payload


def build_full_payload(client: Client, new_fund: NewProduct, old_fund: Optional[ExistingProduct] = None) -> Dict[str, Any]:
    payload = build_common_fields(client)
    fund_fields = build_fund_fields(new_fund, old_fund)
    payload.update(fund_fields)
    payload = _normalize_hebrew_payload(payload)
    return payload


def build_full_payload_overlay(
    client: Client, new_fund: NewProduct, old_fund: Optional[ExistingProduct] = None
) -> Dict[str, Any]:
    payload = build_common_fields(client)
    fund_fields = build_fund_fields(new_fund, old_fund)
    payload.update(fund_fields)
    payload = _normalize_hebrew_payload_reversed(payload)
    return payload


def generate_kit_pdf_for_new_product(
    db: Session, client_id: int, new_product_id: int
) -> Tuple[bytes, str]:
    client = db.query(Client).filter(Client.id == client_id).first()
    if not client:
        raise ValueError("CLIENT_NOT_FOUND")

    new_fund = db.query(NewProduct).filter(NewProduct.id == new_product_id).first()
    if not new_fund:
        raise ValueError("NEW_PRODUCT_NOT_FOUND")

    if new_fund.client_id != client.id:
        raise ValueError("PRODUCT_DOES_NOT_BELONG_TO_CLIENT")

    if new_fund.fund_type not in SUPPORTED_AUTO_FUND_TYPES:
        raise ValueError("UNSUPPORTED_FUND_TYPE")

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

    template_path_obj = _select_template_for_product(new_fund)
    kit_dir = _kit_dir_for_product(new_fund)

    if not template_path_obj or not template_path_obj.is_file():
        raise ValueError(
            f"NO_TEMPLATE_FOUND in folder {kit_dir} for fund type {new_fund.fund_type}"
        )

    export_dir = _get_client_export_dir(client)
    output_filename = f"kit_{client_id}_{new_product_id}.pdf"
    out_path = export_dir / output_filename

    payload = build_full_payload(client, new_fund, old_fund)

    pdf_path = fill_form_auto(str(template_path_obj), payload, out_path)
    data = Path(pdf_path).read_bytes()

    return data, output_filename


def generate_kit_pdf_for_new_product_overlay(
    db: Session, client_id: int, new_product_id: int
) -> Tuple[bytes, str]:
    client = db.query(Client).filter(Client.id == client_id).first()
    if not client:
        raise ValueError("CLIENT_NOT_FOUND")

    new_fund = db.query(NewProduct).filter(NewProduct.id == new_product_id).first()
    if not new_fund:
        raise ValueError("NEW_PRODUCT_NOT_FOUND")

    if new_fund.client_id != client.id:
        raise ValueError("PRODUCT_DOES_NOT_BELONG_TO_CLIENT")

    if new_fund.fund_type not in SUPPORTED_AUTO_FUND_TYPES:
        raise ValueError("UNSUPPORTED_FUND_TYPE")

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

    template_path_obj = _select_template_for_product(new_fund)
    kit_dir = _kit_dir_for_product(new_fund)

    if not template_path_obj or not template_path_obj.is_file():
        raise ValueError(
            f"NO_TEMPLATE_FOUND in folder {kit_dir} for fund type {new_fund.fund_type}"
        )

    fund_name = getattr(new_fund, "fund_name", f"fund_{new_product_id}") or ""
    safe_fund_name = sanitize_filename(fund_name)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_filename = f"{safe_fund_name}_{timestamp}_overlay.pdf"

    export_dir = _get_client_export_dir(client)
    out_path = export_dir / output_filename

    payload = build_full_payload_overlay(client, new_fund, old_fund)

    pdf_path = fill_form_auto(str(template_path_obj), payload, out_path)
    data = Path(pdf_path).read_bytes()

    return data, output_filename
