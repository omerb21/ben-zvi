from __future__ import annotations

from typing import Any, Dict, List

from sqlalchemy.orm import Session

from app.models import Client, ExistingProduct, NewProduct
from app.services import sync_remote_products_helpers as _helpers


def _sanitize_management_fee_balance(raw_fee: Any, raw_amount: Any):
    return _helpers._sanitize_management_fee_balance(raw_fee, raw_amount)


def _apply_common_product_fields(row: Any, item: Dict[str, Any]) -> None:
    _helpers._apply_common_product_fields(row, item)


def _existing_product_fund_key_from_parts(
    fund_code: str | None,
    company_name: str | None,
    fund_name: str | None,
) -> tuple[str, str, str] | None:
    return _helpers._existing_product_fund_key_from_parts(fund_code, company_name, fund_name)


def _find_local_existing_product_for_remote(
    remote_existing_product: Dict[str, Any],
    *,
    local_existing_by_personal: Dict[str, ExistingProduct],
    local_existing_by_fund_key: Dict[tuple[str, str, str], ExistingProduct],
) -> ExistingProduct | None:
    return _helpers._find_local_existing_product_for_remote(
        remote_existing_product,
        local_existing_by_personal=local_existing_by_personal,
        local_existing_by_fund_key=local_existing_by_fund_key,
    )


def _sync_existing_products_for_client(db: Session, local_client: Client, remote_products: List[Dict[str, Any]]) -> None:
    _helpers._sync_existing_products_for_client(db, local_client, remote_products)


def _new_product_key(data: Dict[str, Any]) -> str:
    return _helpers._new_product_key(data)


def _sync_new_products_for_client(
    db: Session,
    local_client: Client,
    remote_existing_products: List[Dict[str, Any]],
    remote_new_products: List[Dict[str, Any]],
) -> None:
    _helpers._sync_new_products_for_client(
        db,
        local_client,
        remote_existing_products,
        remote_new_products,
    )
