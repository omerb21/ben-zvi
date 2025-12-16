from __future__ import annotations

from typing import Any, Dict, List, Optional

from app.models import Client, ExistingProduct, NewProduct
from app.services import justification_advice_tables_rows_builders_helpers as _helpers
from app.services import justification_advice_tables_rows_utils as _utils


_RECOMMENDATION_TEXT = (
    _helpers._RECOMMENDATION_TEXT
)


def _build_recommendation_row() -> Dict[str, Any]:
    return _helpers._build_recommendation_row()


def _append_fund_code_to_track_name(row: Dict[str, Any], fund_code: str | None) -> Dict[str, Any]:
    return _helpers._append_fund_code_to_track_name(row, fund_code)


def build_existing_row(client: Client, ex: ExistingProduct) -> Dict[str, Any]:
    return _helpers.build_existing_row(client, ex)


def build_new_row(
    client: Client,
    new: NewProduct,
    accumulated_override: Optional[float] = None,
) -> Dict[str, Any]:
    return _helpers.build_new_row(client, new, accumulated_override)


def _build_existing_row_with_fund_code(client: Client, existing: ExistingProduct) -> Dict[str, Any]:
    return _helpers._build_existing_row_with_fund_code(client, existing)


def _build_new_row_with_fund_code(
    client: Client,
    new: NewProduct,
    accumulated_override: Optional[float] = None,
) -> Dict[str, Any]:
    return _helpers._build_new_row_with_fund_code(client, new, accumulated_override)


def _build_new_rows_with_fund_code(
    client: Client,
    new_list: List[NewProduct],
    accumulated_override: Optional[float],
) -> List[Dict[str, Any]]:
    return _helpers._build_new_rows_with_fund_code(client, new_list, accumulated_override)


STATIC_ROWS_COMPARISON: List[Dict[str, Any]] = _helpers.STATIC_ROWS_COMPARISON


def build_static_rows(client: Client, existing: ExistingProduct) -> List[Dict[str, Any]]:
    return _helpers.build_static_rows(client, existing)
