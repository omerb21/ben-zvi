from __future__ import annotations

from typing import Any, Dict, List, Tuple

from app.models import Client, ExistingProduct, NewProduct
from app.services.justification_advice_tables_rows import (
    normalize_fund_type,
    _is_normalized_gemel,
    _build_existing_row_with_fund_code,
    _build_new_row_with_fund_code,
    _build_new_rows_with_fund_code,
    _build_recommendation_row,
    _compute_share_amount,
    build_static_rows,
)


def filter_pairs(client: Client) -> List[Tuple[ExistingProduct, List[NewProduct]]]:
    result: List[Tuple[ExistingProduct, List[NewProduct]]] = []

    for existing in client.existing_products:
        existing_type = normalize_fund_type(existing.fund_type)
        new_products = [
            np
            for np in client.new_products
            if np.existing_product_id == existing.id
            and normalize_fund_type(np.fund_type) == existing_type
        ]
        result.append((existing, new_products))

    return result


def build_tables(client: Client) -> List[List[Dict[str, Any]]]:
    tables: List[List[Dict[str, Any]]] = []
    pairs = filter_pairs(client)

    standalone_new_products = [
        np for np in client.new_products if np.existing_product_id is None
    ]

    for standalone_new in standalone_new_products:
        standalone_row = _build_new_row_with_fund_code(client, standalone_new)

        alternatives_rows: List[Dict[str, Any]] = []
        if _is_normalized_gemel(standalone_new.fund_type):
            temp_existing = type(
                "obj",
                (object,),
                {
                    "accumulated_amount": standalone_new.accumulated_amount or 0,
                    "fund_code": standalone_new.fund_code,
                },
            )
            alternatives_rows = build_static_rows(client, temp_existing)  # type: ignore[arg-type]

        table = [standalone_row] + alternatives_rows + [_build_recommendation_row()]
        tables.append(table)

    for ex, new_list in pairs:
        share_amount = _compute_share_amount(ex, new_list)

        if _is_normalized_gemel(ex.fund_type):
            if new_list:
                existing_row = _build_existing_row_with_fund_code(client, ex)

                new_rows = _build_new_rows_with_fund_code(client, new_list, share_amount)

                alternatives_rows = build_static_rows(client, ex)

                table = [existing_row] + new_rows + alternatives_rows + [_build_recommendation_row()]
            else:
                existing_row = _build_existing_row_with_fund_code(client, ex)
                table = [existing_row]
        else:
            if new_list:
                existing_row = _build_existing_row_with_fund_code(client, ex)

                new_rows = _build_new_rows_with_fund_code(client, new_list, share_amount)

                table = [existing_row] + new_rows + [_build_recommendation_row()]
            else:
                existing_row = _build_existing_row_with_fund_code(client, ex)
                table = [existing_row]

        tables.append(table)

    return tables
