from __future__ import annotations

from datetime import date
from typing import List, Optional

from app.models import ExistingProduct


INTEREST_RATE = 0.03


def normalize_fund_type(value: str | None) -> str:
    text = (value or "").strip()
    if not text:
        return ""

    if text in {"גמל", "קופת גמל"}:
        return "גמל"
    if text in {"גמל להשקעה", "קופת גמל להשקעה"}:
        return "גמל להשקעה"
    if text in {"השתלמות", "קרן השתלמות"}:
        return "השתלמות"

    return text


def _is_normalized_gemel(value: str | None) -> bool:
    return normalize_fund_type(value) == "גמל"


def years_to_67(birth: date) -> int:
    return max(0, 67 - (date.today().year - birth.year))


def fv(balance: float | None, years: int, r: float = INTEREST_RATE) -> float:
    if balance is None or years <= 0:
        return 0.0
    return round(float(balance) * (1 + r) ** years, 2)


def fee_cost(balance: float | None, fee_pct: float | None, years: int) -> float:
    if balance is None or not fee_pct or years <= 0:
        return 0.0
    return round(float(balance) * float(fee_pct) * years, 2)


def has_replacement(existing_product: ExistingProduct) -> bool:
    existing_type = normalize_fund_type(existing_product.fund_type)
    return any(
        normalize_fund_type(new.fund_type) == existing_type
        for new in existing_product.new_products
    )


def _format_yield(value: float | None) -> str:
    if value is None:
        return "אין נתון"
    return f"{value or ''}%"


def _format_balance(value: float | None) -> str:
    return f"{value:,.0f}" if value else "לא רלוונטי"


def _append_personal_number_to_fund_name(
    fund_type: str | None,
    fund_name: str | None,
    personal_number: str | None,
) -> str | None:
    if (
        fund_type in ["גמל", "גמל להשקעה", "השתלמות"]
        and personal_number
    ):
        return f"{fund_name} (מס' קופה: {personal_number})"
    return fund_name


def _compute_share_amount(existing: ExistingProduct, new_list: List) -> Optional[float]:
    if existing.accumulated_amount is None or len(new_list) <= 1:
        return None
    total = existing.accumulated_amount or 0.0
    count = float(len(new_list))
    return total / count if count > 0 else 0.0


def _static_fee_pct_for_index(index: int) -> float:
    return 0.0044 if index == 2 else 0.0022
