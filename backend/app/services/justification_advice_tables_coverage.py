from __future__ import annotations

from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from app.models import Client, ExistingProduct, NewProduct
from app.services.justification_advice_tables_rows import _is_normalized_gemel
from app.services import justification_advice_tables_coverage_helpers as _helpers


def _no_coverage_fields() -> Dict[str, Any]:
    return _helpers._no_coverage_fields()


def _coverage_product_name(fund_name: str | None, personal_number: str | None) -> str | None:
    return _helpers._coverage_product_name(fund_name, personal_number)


def _build_coverage_table_row(item: Any, recommendation: str) -> Dict[str, Any]:
    return _helpers._build_coverage_table_row(item, recommendation)


STATIC_ROWS_COVERAGE: List[Dict[str, Any]] = _helpers.STATIC_ROWS_COVERAGE


def _append_static_coverage_alternatives(rows: List[Dict[str, Any]]) -> None:
    return _helpers._append_static_coverage_alternatives(rows)


def build_coverage_table_rows(
    existing: Optional[ExistingProduct],
    new: Optional[NewProduct] = None,
    add_alternatives: bool = False,
) -> List[Dict[str, Any]]:
    return _helpers.build_coverage_table_rows(
        existing,
        new,
        add_alternatives=add_alternatives,
    )


def build_coverage_tables(
    db: Session,
    client: Client,
    tables: List[List[Dict[str, Any]]],
) -> List[List[Dict[str, Any]]]:
    return _helpers.build_coverage_tables(db, client, tables)
