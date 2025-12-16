from __future__ import annotations

import os
from typing import Any, Dict, List

import requests
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models import Client, ExistingProduct, NewProduct, Snapshot
from app.schemas.crm import ClientBeneficiaryUpdate, ClientCreate, ClientUpdate
from app.services import crm as crm_service
from app.utils.strings import coerce_stripped as _coerce_stripped
from app.utils.strings import strip_or_empty as _strip_or_empty

from app.services import sync_remote_clients as _sync_clients
from app.services import sync_remote_fetch as _sync_fetch
from app.services import sync_remote_products as _sync_products
from app.services import sync_remote_snapshots as _sync_snapshots
from app.services import sync_remote_utils as _sync_utils


def _normalize_base_url(base_url: str) -> str:
    return _sync_fetch._normalize_base_url(base_url)


def _get_json(url: str) -> Any:
    return _sync_fetch._get_json(url)


def _safe_get_json(url: str) -> Any:
    return _sync_fetch._safe_get_json(url)


def _safe_get_json_list(url: str) -> List[Dict[str, Any]]:
    return _sync_fetch._safe_get_json_list(url)


def _build_client_resource_urls(base_url: str, remote_client_id: int) -> tuple[str, str, str]:
    return _sync_fetch._build_client_resource_urls(base_url, remote_client_id)


def _fetch_remote_client_payloads(
    base_url: str,
    remote_client_id: int,
) -> tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]]]:
    return _sync_fetch._fetch_remote_client_payloads(base_url, remote_client_id)


def _coerce_float(value: Any, default: float = 0.0) -> float:
    return _sync_utils._coerce_float(value, default=default)


def _list_rows_for_client(db: Session, model: Any, client_id: int):
    return _sync_utils._list_rows_for_client(db, model, client_id)


def _snapshot_key(fund_number: Any, snapshot_date: Any, source: Any) -> tuple[str, str, str]:
    return _sync_snapshots._snapshot_key(fund_number, snapshot_date, source)


def _sanitize_management_fee_balance(raw_fee: Any, raw_amount: Any):
    return _sync_products._sanitize_management_fee_balance(raw_fee, raw_amount)


def _apply_common_product_fields(row: Any, item: Dict[str, Any]) -> None:
    _sync_products._apply_common_product_fields(row, item)


def _find_local_existing_product_for_remote(
    remote_existing_product: Dict[str, Any],
    *,
    local_existing_by_personal: Dict[str, ExistingProduct],
    local_existing_by_fund_key: Dict[tuple[str, str, str], ExistingProduct],
) -> ExistingProduct | None:
    return _sync_products._find_local_existing_product_for_remote(
        remote_existing_product,
        local_existing_by_personal=local_existing_by_personal,
        local_existing_by_fund_key=local_existing_by_fund_key,
    )


def _build_client_create(remote_client: Dict[str, Any]) -> ClientCreate:
    return _sync_clients._build_client_create(remote_client)


def _existing_product_fund_key_from_parts(
    fund_code: str | None,
    company_name: str | None,
    fund_name: str | None,
) -> tuple[str, str, str] | None:
    return _sync_products._existing_product_fund_key_from_parts(fund_code, company_name, fund_name)


def _to_beneficiary_update_or_none(raw: Any) -> ClientBeneficiaryUpdate | None:
    return _sync_clients._to_beneficiary_update_or_none(raw)


def _build_client_update(remote_client: Dict[str, Any]) -> ClientUpdate:
    return _sync_clients._build_client_update(remote_client)


def _get_or_create_local_client(db: Session, remote_client: Dict[str, Any]) -> Client:
    return _sync_clients._get_or_create_local_client(db, remote_client)


def _sync_snapshots_for_client(db: Session, local_client: Client, remote_snapshots: List[Dict[str, Any]]) -> None:
    _sync_snapshots._sync_snapshots_for_client(db, local_client, remote_snapshots)


def _sync_existing_products_for_client(db: Session, local_client: Client, remote_products: List[Dict[str, Any]]) -> None:
    _sync_products._sync_existing_products_for_client(db, local_client, remote_products)


def _new_product_key(data: Dict[str, Any]) -> str:
    return _sync_products._new_product_key(data)


def _sync_new_products_for_client(
    db: Session,
    local_client: Client,
    remote_existing_products: List[Dict[str, Any]],
    remote_new_products: List[Dict[str, Any]],
) -> None:
    _sync_products._sync_new_products_for_client(
        db,
        local_client,
        remote_existing_products,
        remote_new_products,
    )


def sync_all_clients_from_remote(base_url: str | None = None) -> None:
    base_url = _normalize_base_url(base_url or os.getenv("REMOTE_BASE_URL", ""))
    if not base_url:
        raise ValueError("REMOTE_BASE_URL is not set and base_url argument was not provided")

    db: Session = SessionLocal()
    try:
        clients_url = f"{base_url}/api/v1/crm/clients"
        remote_clients = _get_json(clients_url) or []

        for remote_client in remote_clients:
            local_client = _get_or_create_local_client(db, remote_client)
            remote_id = remote_client.get("id")
            if remote_id is None:
                continue

            remote_snapshots, remote_existing, remote_new = _fetch_remote_client_payloads(base_url, remote_id)

            _sync_snapshots_for_client(db, local_client, remote_snapshots)
            _sync_existing_products_for_client(db, local_client, remote_existing)
            _sync_new_products_for_client(db, local_client, remote_existing, remote_new)

        db.commit()
    finally:
        db.close()
