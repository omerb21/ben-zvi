from __future__ import annotations

from typing import Any, Dict, List

from sqlalchemy.orm import Session

from app.models import Client, ExistingProduct, NewProduct
from app.services.sync_remote_utils import _list_rows_for_client
from app.utils.strings import coerce_stripped as _coerce_stripped
from app.utils.strings import strip_or_empty as _strip_or_empty


def _sanitize_management_fee_balance(raw_fee: Any, raw_amount: Any):
    if raw_fee is not None and raw_amount is not None and raw_fee > 100 and abs(raw_fee - raw_amount) < 1.0:
        return None
    return raw_fee


def _apply_common_product_fields(row: Any, item: Dict[str, Any]) -> None:
    row.fund_type = item.get("fundType") or ""
    row.company_name = item.get("companyName") or ""
    row.fund_name = item.get("fundName") or ""
    row.fund_code = item.get("fundCode") or ""
    row.yield_1yr = item.get("yield1yr")
    row.yield_3yr = item.get("yield3yr")
    row.management_fee_contributions = item.get("managementFeeContributions")
    row.accumulated_amount = item.get("accumulatedAmount")
    row.employment_status = item.get("employmentStatus")
    row.has_regular_contributions = item.get("hasRegularContributions")


def _existing_product_fund_key_from_parts(
    fund_code: str | None,
    company_name: str | None,
    fund_name: str | None,
) -> tuple[str, str, str] | None:
    fund_code_value = _strip_or_empty(fund_code)
    company_value = _strip_or_empty(company_name)
    fund_name_value = _strip_or_empty(fund_name)
    if not fund_code_value or not company_value:
        return None
    return (fund_code_value, company_value, fund_name_value)


def _find_local_existing_product_for_remote(
    remote_existing_product: Dict[str, Any],
    *,
    local_existing_by_personal: Dict[str, ExistingProduct],
    local_existing_by_fund_key: Dict[tuple[str, str, str], ExistingProduct],
) -> ExistingProduct | None:
    personal_number_ep = _strip_or_empty(remote_existing_product.get("personalNumber"))
    if personal_number_ep:
        local_ep = local_existing_by_personal.get(personal_number_ep)
        if local_ep is not None:
            return local_ep

    fund_key = _existing_product_fund_key_from_parts(
        remote_existing_product.get("fundCode"),
        remote_existing_product.get("companyName"),
        remote_existing_product.get("fundName"),
    )
    if fund_key is not None:
        return local_existing_by_fund_key.get(fund_key)
    return None


def _sync_existing_products_for_client(db: Session, local_client: Client, remote_products: List[Dict[str, Any]]) -> None:
    existing_rows = _list_rows_for_client(db, ExistingProduct, local_client.id)
    by_personal: Dict[str, ExistingProduct] = {}
    for row in existing_rows:
        if row.personal_number:
            by_personal[row.personal_number] = row

    for item in remote_products:
        if item.get("isVirtual"):
            continue

        personal_number = _strip_or_empty(item.get("personalNumber"))
        if not personal_number:
            continue

        row = by_personal.get(personal_number)
        if row is None:
            row = ExistingProduct(client_id=local_client.id, personal_number=personal_number)
            db.add(row)
            by_personal[personal_number] = row

        _apply_common_product_fields(row, item)

        raw_fee = item.get("managementFeeBalance")
        raw_amount = item.get("accumulatedAmount")
        row.management_fee_balance = _sanitize_management_fee_balance(raw_fee, raw_amount)


def _new_product_key(data: Dict[str, Any]) -> str:
    personal = _coerce_stripped(data.get("personalNumber"))
    if personal:
        return f"PN:{personal}"
    fund_code = _coerce_stripped(data.get("fundCode"))
    company = _coerce_stripped(data.get("companyName"))
    fund_name = _coerce_stripped(data.get("fundName"))
    return f"F:{fund_code}|C:{company}|N:{fund_name}"


def _sync_new_products_for_client(
    db: Session,
    local_client: Client,
    remote_existing_products: List[Dict[str, Any]],
    remote_new_products: List[Dict[str, Any]],
) -> None:
    local_existing = _list_rows_for_client(db, ExistingProduct, local_client.id)
    local_existing_by_personal: Dict[str, ExistingProduct] = {}
    local_existing_by_fund_key: Dict[tuple[str, str, str], ExistingProduct] = {}
    for ep in local_existing:
        personal = _strip_or_empty(ep.personal_number)
        if personal and personal not in local_existing_by_personal:
            local_existing_by_personal[personal] = ep

        fund_key = _existing_product_fund_key_from_parts(
            ep.fund_code,
            ep.company_name,
            ep.fund_name,
        )
        if fund_key is not None and fund_key not in local_existing_by_fund_key:
            local_existing_by_fund_key[fund_key] = ep

    existing_rows = _list_rows_for_client(db, NewProduct, local_client.id)
    by_key: Dict[str, NewProduct] = {}
    for row in existing_rows:
        data = {
            "personalNumber": row.personal_number,
            "fundCode": row.fund_code,
            "companyName": row.company_name,
            "fundName": row.fund_name,
        }
        key = _new_product_key(data)
        if key and key not in by_key:
            by_key[key] = row

    remote_existing_by_id: Dict[int, Dict[str, Any]] = {}
    for item in remote_existing_products:
        if item.get("isVirtual"):
            continue
        try:
            remote_id = int(item.get("id"))
        except (TypeError, ValueError):
            continue
        remote_existing_by_id[remote_id] = item

    for item in remote_new_products:
        key = _new_product_key(item)
        if not key:
            continue

        row = by_key.get(key)
        if row is None:
            row = NewProduct(client_id=local_client.id)
            db.add(row)
            by_key[key] = row

        _apply_common_product_fields(row, item)
        row.personal_number = _strip_or_empty(item.get("personalNumber")) or None
        row.management_fee_balance = item.get("managementFeeBalance")

        existing_product_id = item.get("existingProductId")
        if isinstance(existing_product_id, int):
            remote_ep = remote_existing_by_id.get(existing_product_id)
            if remote_ep is not None:
                local_ep = _find_local_existing_product_for_remote(
                    remote_ep,
                    local_existing_by_personal=local_existing_by_personal,
                    local_existing_by_fund_key=local_existing_by_fund_key,
                )

                if local_ep is not None:
                    row.existing_product_id = local_ep.id
