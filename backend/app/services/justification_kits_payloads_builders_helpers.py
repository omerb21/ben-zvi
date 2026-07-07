from __future__ import annotations

from datetime import datetime
from typing import Any, Callable, Dict, Optional

import pytz

from app.models import Client, ExistingProduct, NewProduct
from app.services import justification_kits_payloads_utils as _utils


REPLACEMENT_FUND_FIELD_PREFIX_BY_TYPE = {
    "גמל": "mekabeletg",
    "גמל להשקעה": "mekabeletgh",
    "השתלמות": "mekabeleth",
}
DEPOSIT_CHECKBOX_YES_VALUE = "/Yes_yyfg"


def _add_replacement_fund_fields(payload: Dict[str, Any], new_fund: NewProduct) -> None:
    prefix = REPLACEMENT_FUND_FIELD_PREFIX_BY_TYPE.get((new_fund.fund_type or "").strip())
    if not prefix:
        return

    payload[f"{prefix}_name"] = new_fund.fund_name
    payload[f"{prefix}_number"] = new_fund.fund_code


def _regular_contributions_value(
    new_fund: NewProduct,
    old_fund: Optional[ExistingProduct],
) -> Optional[bool]:
    new_value = getattr(new_fund, "has_regular_contributions", None)
    if new_value is not None:
        return bool(new_value)

    old_value = getattr(old_fund, "has_regular_contributions", None) if old_fund else None
    if old_value is not None:
        return bool(old_value)

    return None


def _add_regular_contributions_fields(
    payload: Dict[str, Any],
    new_fund: NewProduct,
    old_fund: Optional[ExistingProduct],
) -> None:
    has_regular_contributions = _regular_contributions_value(new_fund, old_fund)
    if has_regular_contributions is None:
        return

    dep_field = "depyes" if has_regular_contributions else "depno"
    for cb in {"depyes", "depno"}:
        payload[cb] = DEPOSIT_CHECKBOX_YES_VALUE if cb == dep_field else "/Off"


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
            "ClientBdate": _utils._fmt_date(client.birth_date),
            "birth_date": _utils._fmt_date(client.birth_date),
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

    gender_raw = (getattr(client, "gender", None) or "").strip()
    gender_lower = gender_raw.lower()
    is_male = gender_raw == "זכר" or gender_lower in {"male", "m"}
    is_female = gender_raw == "נקבה" or gender_lower in {"female", "f"}

    payload.update(
        {
            "male": _utils._rb(is_male),
            "Male": _utils._rb(is_male),
            "female": _utils._rb(is_female),
            "Female": _utils._rb(is_female),
            "client_gender_male": _utils._rb(is_male),
            "client_gender_female": _utils._rb(is_female),
        }
    )

    ms_raw = (getattr(client, "marital_status", None) or "").strip()
    ms_lower = ms_raw.lower()
    is_single = ms_raw in {"רווק", "רווקה"} or ms_lower in {"single", "unmarried"}
    is_married = ms_raw in {"נשוי", "נשוי/ה", "נשוי/אה"} or ms_lower == "married"
    is_divorced = ms_raw in {"גרוש", "גרושה"} or ms_lower == "divorced"
    is_widowed = ms_raw in {"אלמן", "אלמנה"} or ms_lower in {"widowed", "widow", "widower"}

    payload.update(
        {
            "single": _utils._rb(is_single),
            "Single": _utils._rb(is_single),
            "married": _utils._rb(is_married),
            "Married": _utils._rb(is_married),
            "divorced": _utils._rb(is_divorced),
            "Divorced": _utils._rb(is_divorced),
            "widowed": _utils._rb(is_widowed),
            "client_married": _utils._rb(is_married),
            "client_single": _utils._rb(is_single),
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
    beneficiaries = getattr(client, "beneficiaries", None) or []
    by_index = {}
    for b in beneficiaries:
        try:
            idx = int(getattr(b, "index", 0) or 0)
        except (TypeError, ValueError):
            continue
        if idx < 1 or idx > 4:
            continue
        by_index[idx] = b

    for idx in range(1, 5):
        b = by_index.get(idx)
        if not b:
            continue

        prefix = f"motav{idx}"
        payload[f"{prefix}name"] = getattr(b, "first_name", "") or ""
        payload[f"{prefix}lastname"] = getattr(b, "last_name", "") or ""
        payload[f"{prefix}id"] = getattr(b, "id_number", "") or ""
        payload[f"{prefix}ads"] = getattr(b, "address", "") or ""
        payload[f"{prefix}rel"] = getattr(b, "relation", "") or ""

        percentage_value = getattr(b, "percentage", None)
        if percentage_value is None:
            payload[f"{prefix}per"] = ""
        else:
            payload[f"{prefix}per"] = str(percentage_value)

        payload[f"{prefix}Bdate"] = _utils._fmt_date(getattr(b, "birth_date", None))

    return payload


def build_fund_fields(new_fund: NewProduct, old_fund: Optional[ExistingProduct] = None) -> Dict[str, Any]:
    payload: Dict[str, Any] = {}

    emp = (
        getattr(new_fund, "employment_status", None)
        or getattr(new_fund, "employment_type", None)
        or ""
    )

    payload.update(
        {
            "employ": _utils._rb(emp == "שכיר"),
            "indipendent": _utils._rb(emp == "עצמאי"),
            "baalshlita": _utils._rb(emp == "שכיר בעל שליטה"),
            "indiploy": _utils._rb(emp == "עצמאי באמצעות מעסיק"),
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
    _add_replacement_fund_fields(payload, new_fund)
    _add_regular_contributions_fields(payload, new_fund, old_fund)

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

    deposit_status = getattr(new_fund, "deposit_status", "")
    if deposit_status:
        payload.update(
            {
                "one_time": _utils._rb(deposit_status == "חד פעמי"),
                "monthly": _utils._rb(deposit_status == "חודשי"),
                "deposit_amount": getattr(new_fund, "deposit_amount", ""),
            }
        )

    return payload


def _build_full_payload_with_normalizer(
    client: Client,
    new_fund: NewProduct,
    old_fund: Optional[ExistingProduct],
    normalize_payload_fn: Callable[[Dict[str, Any]], Dict[str, Any]],
) -> Dict[str, Any]:
    payload = build_common_fields(client)
    fund_fields = build_fund_fields(new_fund, old_fund)
    payload.update(fund_fields)
    return normalize_payload_fn(payload)


def build_full_payload(
    client: Client,
    new_fund: NewProduct,
    old_fund: Optional[ExistingProduct] = None,
) -> Dict[str, Any]:
    return _build_full_payload_with_normalizer(client, new_fund, old_fund, _utils._normalize_hebrew_payload)


def build_full_payload_overlay(
    client: Client,
    new_fund: NewProduct,
    old_fund: Optional[ExistingProduct] = None,
) -> Dict[str, Any]:
    return _build_full_payload_with_normalizer(
        client,
        new_fund,
        old_fund,
        _utils._normalize_hebrew_payload_reversed,
    )
