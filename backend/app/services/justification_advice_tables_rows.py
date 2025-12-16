from __future__ import annotations

from datetime import date
from typing import Any, Dict, List, Optional

from app.models import Client, ExistingProduct, NewProduct
from app.services import justification_advice_tables_rows_builders as _builders
from app.services import justification_advice_tables_rows_utils as _utils


INTEREST_RATE = _utils.INTEREST_RATE


def normalize_fund_type(value: str | None) -> str:
    return _utils.normalize_fund_type(value)


def _is_normalized_gemel(value: str | None) -> bool:
    return _utils._is_normalized_gemel(value)


def years_to_67(birth: date) -> int:
    return _utils.years_to_67(birth)


def fv(balance: float | None, years: int, r: float = INTEREST_RATE) -> float:
    return _utils.fv(balance=balance, years=years, r=r)


def fee_cost(balance: float | None, fee_pct: float | None, years: int) -> float:
    return _utils.fee_cost(balance=balance, fee_pct=fee_pct, years=years)


def has_replacement(existing_product: ExistingProduct) -> bool:
    return _utils.has_replacement(existing_product)


def _format_yield(value: float | None) -> str:
    return _utils._format_yield(value)


def _format_balance(value: float | None) -> str:
    return _utils._format_balance(value)


def _append_personal_number_to_fund_name(
    fund_type: str | None,
    fund_name: str | None,
    personal_number: str | None,
) -> str | None:
    return _utils._append_personal_number_to_fund_name(
        fund_type,
        fund_name,
        personal_number,
    )


_RECOMMENDATION_TEXT = _builders._RECOMMENDATION_TEXT


def _build_recommendation_row() -> Dict[str, Any]:
    return _builders._build_recommendation_row()


def _append_fund_code_to_track_name(row: Dict[str, Any], fund_code: str | None) -> Dict[str, Any]:
    return _builders._append_fund_code_to_track_name(row, fund_code)


def _build_existing_row_with_fund_code(client: Client, existing: ExistingProduct) -> Dict[str, Any]:
    return _builders._build_existing_row_with_fund_code(client, existing)


def _build_new_row_with_fund_code(
    client: Client,
    new: NewProduct,
    accumulated_override: Optional[float] = None,
) -> Dict[str, Any]:
    return _builders._build_new_row_with_fund_code(client, new, accumulated_override)


def _build_new_rows_with_fund_code(
    client: Client,
    new_list: List[NewProduct],
    accumulated_override: Optional[float],
) -> List[Dict[str, Any]]:
    return _builders._build_new_rows_with_fund_code(client, new_list, accumulated_override)


def _compute_share_amount(existing: ExistingProduct, new_list: List[NewProduct]) -> Optional[float]:
    return _utils._compute_share_amount(existing, new_list)


def _static_fee_pct_for_index(index: int) -> float:
    return _utils._static_fee_pct_for_index(index)


def build_existing_row(client: Client, ex: ExistingProduct) -> Dict[str, Any]:
    return _builders.build_existing_row(client, ex)


def build_new_row(
    client: Client,
    new: NewProduct,
    accumulated_override: Optional[float] = None,
) -> Dict[str, Any]:
    return _builders.build_new_row(client, new, accumulated_override)


STATIC_ROWS_COMPARISON: List[Dict[str, Any]] = _builders.STATIC_ROWS_COMPARISON


def build_static_rows(client: Client, existing: ExistingProduct) -> List[Dict[str, Any]]:
    return _builders.build_static_rows(client, existing)
