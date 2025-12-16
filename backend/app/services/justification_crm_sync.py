from typing import List, Dict, Any

from sqlalchemy.orm import Session

from app.models import SavingProduct, ExistingProduct, Snapshot
from app.services import justification_crm_sync_helpers as _helpers
from app.utils.source_names import get_source_display_name
from app.utils.strings import strip_or_empty as _strip_or_empty
from app.utils.numbers import coerce_amount as _coerce_amount


def _canonicalize_personal_number(value: str) -> str:
    return _helpers._canonicalize_personal_number(value)


def _snapshot_hash_part(
    fund_code: str,
    fund_number: str,
    fund_name: str,
    fund_type: str,
) -> str:
    return _helpers._snapshot_hash_part(
        fund_code,
        fund_number,
        fund_name,
        fund_type,
    )


def _normalize_company_for_match(value: str) -> str:
    return _helpers._normalize_company_for_match(value)


def _select_latest_snapshots_by_key(snapshots: List[Snapshot]) -> Dict[tuple[str, str], Snapshot]:
    return _helpers._select_latest_snapshots_by_key(snapshots)


def _index_saving_products_by_code(saving_products: List[SavingProduct]) -> Dict[str, SavingProduct]:
    return _helpers._index_saving_products_by_code(saving_products)


def _match_saving_product_for_snapshot(
    snap: Snapshot,
    *,
    saving_products: List[SavingProduct],
    saving_by_code: Dict[str, SavingProduct],
) -> SavingProduct | None:
    return _helpers._match_saving_product_for_snapshot(
        snap,
        saving_products=saving_products,
        saving_by_code=saving_by_code,
    )


def sync_client_products_from_crm(db: Session, client_id: int) -> int:
    """Sync CRM snapshots to existing products for a client.

    This takes the latest snapshots, groups them by personal number (canonicalization),
    matches them with market products, and then upserts them into the ExistingProduct table.
    """
    return _helpers.sync_client_products_from_crm(db, client_id)
    # 1. Fetch active snapshots for client
    snapshots = (
        db.query(Snapshot)
        .filter(Snapshot.client_id == client_id, Snapshot.is_active.is_(True))
        .all()
    )
    if not snapshots:
        return 0

    # 2. Keep latest snapshot per (fund_code, fund_number)
    latest_by_key = _select_latest_snapshots_by_key(snapshots)

    if not latest_by_key:
        return 0

    # 3. Load saving products for matching
    saving_products = db.query(SavingProduct).all()
    saving_by_code = _index_saving_products_by_code(saving_products)

    # 4. Create intermediate items
    items: List[Dict[str, Any]] = []
    for (fund_code, fund_number), snap in latest_by_key.items():
        # Match logic (copied from list_existing_products_view_for_client)
        sp = _match_saving_product_for_snapshot(
            snap,
            saving_products=saving_products,
            saving_by_code=saving_by_code,
        )

        fund_type = (snap.fund_type or (sp.fund_type if sp else "")) or ""
        fund_name = (snap.fund_name or (sp.fund_name if sp else "")) or ""
        company_name = (sp.company_name if sp else get_source_display_name(snap.source or "")) or ""

        if not fund_name and not company_name and not fund_type:
            continue

        # Use fund_code as personal_number basis if fund_number is missing, but prefer original raw value
        personal_number = fund_number or fund_code
        # Fallback for missing or placeholder personal numbers to avoid uniqueness constraint violations
        if not personal_number or personal_number.strip() in ["לא זמין", "לא ידוע", "-"]:
             # Create a deterministic synthetic ID based on the snapshot key properties
             hash_part = _snapshot_hash_part(fund_code, fund_number, fund_name, fund_type)
             personal_number = f"CRM-{client_id}-{hash_part}"

        amount = _coerce_amount(snap.amount)

        items.append({
            "fund_type": fund_type,
            "company_name": company_name,
            "fund_name": fund_name,
            "fund_code": (sp.fund_code if sp and sp.fund_code else (fund_code or fund_number or "")),
            "yield_1yr": sp.yield_1yr if sp else None,
            "yield_3yr": sp.yield_3yr if sp else None,
            "personal_number": personal_number,
            "accumulated_amount": amount,
            "management_fee_balance": None,
            "management_fee_contributions": None,
            "employment_status": None,
            "has_regular_contributions": None,
            "raw_fund_code": fund_code, # Keep for matching
        })

    # 5. Group by canonical personal number
    by_personal: Dict[str, List[Dict[str, Any]]] = {}
    for item in items:
        raw_personal = _strip_or_empty(item.get("personal_number"))
        if not raw_personal:
            continue

        canonical = _canonicalize_personal_number(raw_personal)
        if not canonical:
            continue

        if canonical not in by_personal:
            by_personal[canonical] = []
        by_personal[canonical].append(item)

    count_updated = 0

    existing_products = (
        db.query(ExistingProduct)
        .filter(ExistingProduct.client_id == client_id)
        .order_by(ExistingProduct.company_name, ExistingProduct.fund_name)
        .all()
    )
    existing_by_canonical: Dict[str, ExistingProduct] = {}
    for ep in existing_products:
        ep_canonical = _canonicalize_personal_number(ep.personal_number or "")
        if ep_canonical and ep_canonical not in existing_by_canonical:
            existing_by_canonical[ep_canonical] = ep

    # 6. Upsert into DB
    for personal_key, bucket in by_personal.items():
        if not bucket:
            continue

        # Aggregate amounts
        total_amount = sum(_coerce_amount(it.get("accumulated_amount")) for it in bucket)

        # Pick best item for metadata (one with highest amount)
        best_item = max(bucket, key=lambda x: _coerce_amount(x.get("accumulated_amount")))

        target_product = existing_by_canonical.get(personal_key)

        if target_product:
            # Update
            target_product.accumulated_amount = total_amount
            # target_product.management_fee_balance = total_amount

            # Self-healing: fix data corruption from previous sync bug where fee was set to amount.
            # If fee is suspiciously large (> 100) or equals the amount, reset it to None.
            current_fee = target_product.management_fee_balance or 0.0
            if current_fee > 100 and (current_fee == total_amount or current_fee == target_product.accumulated_amount):
                target_product.management_fee_balance = None

            # Only update other fields if they are seemingly valid in the new data
            if best_item["company_name"]: target_product.company_name = best_item["company_name"]
            if best_item["fund_name"]: target_product.fund_name = best_item["fund_name"]
            if best_item["fund_type"]: target_product.fund_type = best_item["fund_type"]
            if best_item["fund_code"]: target_product.fund_code = best_item["fund_code"]
            if best_item["yield_1yr"]: target_product.yield_1yr = best_item["yield_1yr"]
            if best_item["yield_3yr"]: target_product.yield_3yr = best_item["yield_3yr"]

        else:
            # Create
            target_product = ExistingProduct(
                client_id=client_id,
                fund_type=best_item["fund_type"],
                company_name=best_item["company_name"],
                fund_name=best_item["fund_name"],
                fund_code=best_item["fund_code"],
                yield_1yr=best_item["yield_1yr"],
                yield_3yr=best_item["yield_3yr"],
                personal_number=best_item["personal_number"], # Use the raw one from the best item
                management_fee_balance=None,
                management_fee_contributions=best_item["management_fee_contributions"],
                accumulated_amount=total_amount,
                employment_status=best_item["employment_status"],
                has_regular_contributions=best_item["has_regular_contributions"],
            )
            db.add(target_product)
            existing_by_canonical[personal_key] = target_product

        count_updated += 1

    db.commit()
    return count_updated
