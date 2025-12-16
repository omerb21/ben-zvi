from __future__ import annotations

from datetime import date
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy.orm import Session

from app.models import Client, ExistingProduct, NewProduct
from app.services import justification_advice_tables_coverage as _coverage
from app.services import justification_advice_tables_rows as _rows
from app.services import justification_advice_tables_tables as _tables


INTEREST_RATE = 0.03


def normalize_fund_type(value: str | None) -> str:
    return _rows.normalize_fund_type(value)


def _is_normalized_gemel(value: str | None) -> bool:
    return _rows._is_normalized_gemel(value)


def years_to_67(birth: date) -> int:
    return _rows.years_to_67(birth)


def fv(balance: float | None, years: int, r: float = INTEREST_RATE) -> float:
    return _rows.fv(balance=balance, years=years, r=r)


def fee_cost(balance: float | None, fee_pct: float | None, years: int) -> float:
    return _rows.fee_cost(balance=balance, fee_pct=fee_pct, years=years)


def has_replacement(existing_product: ExistingProduct) -> bool:
    return _rows.has_replacement(existing_product)


def _format_yield(value: float | None) -> str:
    return _rows._format_yield(value)


def _format_balance(value: float | None) -> str:
    return _rows._format_balance(value)


def _append_personal_number_to_fund_name(
    fund_type: str | None,
    fund_name: str | None,
    personal_number: str | None,
) -> str | None:
    return _rows._append_personal_number_to_fund_name(
        fund_type,
        fund_name,
        personal_number,
    )


_RECOMMENDATION_TEXT = (
    "שיקולים לבחירת הקופה: 1. רמת שירות גבוהה של הגוף המוסדי. 2. רמת תפעול גבוהה של הגוף המוסדי. 3. רמת ניהול השקעות גבוהה של הגוף המוסדי."
)


def _build_recommendation_row() -> Dict[str, Any]:
    return _rows._build_recommendation_row()


def _append_fund_code_to_track_name(row: Dict[str, Any], fund_code: str | None) -> Dict[str, Any]:
    return _rows._append_fund_code_to_track_name(row, fund_code)


def _build_existing_row_with_fund_code(client: Client, existing: ExistingProduct) -> Dict[str, Any]:
    return _rows._build_existing_row_with_fund_code(client, existing)


def _build_new_row_with_fund_code(
    client: Client,
    new: NewProduct,
    accumulated_override: Optional[float] = None,
) -> Dict[str, Any]:
    return _rows._build_new_row_with_fund_code(client, new, accumulated_override)


def _build_new_rows_with_fund_code(
    client: Client,
    new_list: List[NewProduct],
    accumulated_override: Optional[float],
) -> List[Dict[str, Any]]:
    return _rows._build_new_rows_with_fund_code(client, new_list, accumulated_override)


def _no_coverage_fields() -> Dict[str, Any]:
    return _coverage._no_coverage_fields()


def _build_coverage_table_row(item: Any, recommendation: str) -> Dict[str, Any]:
    return _coverage._build_coverage_table_row(item, recommendation)


def _compute_share_amount(existing: ExistingProduct, new_list: List[NewProduct]) -> Optional[float]:
    return _rows._compute_share_amount(existing, new_list)


def _static_fee_pct_for_index(index: int) -> float:
    return _rows._static_fee_pct_for_index(index)


def _coverage_product_name(fund_name: str | None, personal_number: str | None) -> str | None:
    return _coverage._coverage_product_name(fund_name, personal_number)


def build_existing_row(client: Client, ex: ExistingProduct) -> Dict[str, Any]:
    return _rows.build_existing_row(client, ex)


def build_new_row(
    client: Client,
    new: NewProduct,
    accumulated_override: Optional[float] = None,
) -> Dict[str, Any]:
    return _rows.build_new_row(client, new, accumulated_override)


STATIC_ROWS_COMPARISON: List[Dict[str, Any]] = [row.copy() for row in _rows.STATIC_ROWS_COMPARISON]


def _append_static_coverage_alternatives(rows: List[Dict[str, Any]]) -> None:
    _coverage._append_static_coverage_alternatives(rows)


def build_static_rows(client: Client, existing: ExistingProduct) -> List[Dict[str, Any]]:
    return _rows.build_static_rows(client, existing)


def filter_pairs(client: Client) -> List[Tuple[ExistingProduct, List[NewProduct]]]:
    return _tables.filter_pairs(client)


def build_tables(client: Client) -> List[List[Dict[str, Any]]]:
    return _tables.build_tables(client)


STATIC_ROWS_COVERAGE: List[Dict[str, Any]] = [row.copy() for row in _coverage.STATIC_ROWS_COVERAGE]


def build_coverage_table_rows(
    existing: Optional[ExistingProduct],
    new: Optional[NewProduct] = None,
    add_alternatives: bool = False,
) -> List[Dict[str, Any]]:
    return _coverage.build_coverage_table_rows(
        existing,
        new,
        add_alternatives=add_alternatives,
    )


def build_coverage_tables(
    db: Session,
    client: Client,
    tables: List[List[Dict[str, Any]]],
) -> List[List[Dict[str, Any]]]:
    return _coverage.build_coverage_tables(db, client, tables)
