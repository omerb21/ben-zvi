"""
sync_remote.py - One-way data synchronization from remote Render backend to local DB.

=== IMPORTANT: USAGE POLICY ===
This script is intended for ONE-TIME MIGRATION or DISASTER RECOVERY only.
It should NOT be used for regular daily synchronization.

When to use:
- Initial migration from Render to a new local/Neon database
- Disaster recovery to restore data from Render backup
- Development environment setup

When NOT to use:
- Regular daily sync (both environments should use the same Neon DB)
- Production data updates (use the API directly)

What it does:
- Reads all clients from remote: GET {REMOTE_BASE_URL}/api/v1/crm/clients
- For each client: creates or updates locally (including beneficiaries)
- Syncs snapshots, existing products, and new products per client
- Only adds/updates, NEVER deletes

How to run:
  1. Set environment variables:
     $env:REMOTE_BASE_URL = "https://your-render-backend.onrender.com"
     $env:DATABASE_URL = "postgresql://..."  # Target Neon DB
  2. Run: python -m app.services.sync_remote

=== END USAGE POLICY ===
"""
from __future__ import annotations

import os
from typing import Any, Dict, List

import requests
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models import Client, ExistingProduct, NewProduct, Snapshot
from app.schemas.crm import ClientCreate, ClientUpdate, ClientBeneficiaryUpdate
from app.services import crm as crm_service


def _normalize_base_url(base_url: str) -> str:
    base_url = (base_url or "").strip()
    if base_url.endswith("/"):
        base_url = base_url[:-1]
    return base_url


def _get_json(url: str) -> Any:
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    return response.json()


def _build_client_create(remote_client: Dict[str, Any]) -> ClientCreate:
    return ClientCreate(
        idNumber=remote_client.get("idNumber"),
        fullName=remote_client.get("fullName"),
        firstName=remote_client.get("firstName"),
        lastName=remote_client.get("lastName"),
        email=remote_client.get("email"),
        phone=remote_client.get("phone"),
        addressStreet=remote_client.get("addressStreet"),
        addressCity=remote_client.get("addressCity"),
        addressPostalCode=remote_client.get("addressPostalCode"),
        birthDate=remote_client.get("birthDate"),
        gender=remote_client.get("gender"),
        maritalStatus=remote_client.get("maritalStatus"),
        birthCountry=remote_client.get("birthCountry"),
        employerName=remote_client.get("employerName"),
        employerHp=remote_client.get("employerHp"),
        employerAddress=remote_client.get("employerAddress"),
        employerPhone=remote_client.get("employerPhone"),
        addressHouseNumber=remote_client.get("addressHouseNumber"),
        addressApartment=remote_client.get("addressApartment"),
    )


def _build_client_update(remote_client: Dict[str, Any]) -> ClientUpdate:
    raw_beneficiaries = remote_client.get("beneficiaries") or []
    beneficiaries: List[ClientBeneficiaryUpdate] = []
    for b in raw_beneficiaries:
        try:
            beneficiaries.append(
                ClientBeneficiaryUpdate(
                    index=b.get("index"),
                    firstName=b.get("firstName") or "",
                    lastName=b.get("lastName") or "",
                    idNumber=b.get("idNumber") or "",
                    birthDate=b.get("birthDate") or "",
                    address=b.get("address") or "",
                    relation=b.get("relation") or "",
                    percentage=b.get("percentage") or 0.0,
                )
            )
        except Exception:
            continue

    return ClientUpdate(
        firstName=remote_client.get("firstName"),
        lastName=remote_client.get("lastName"),
        email=remote_client.get("email"),
        phone=remote_client.get("phone"),
        addressStreet=remote_client.get("addressStreet"),
        addressCity=remote_client.get("addressCity"),
        addressPostalCode=remote_client.get("addressPostalCode"),
        birthDate=remote_client.get("birthDate"),
        gender=remote_client.get("gender"),
        maritalStatus=remote_client.get("maritalStatus"),
        birthCountry=remote_client.get("birthCountry"),
        employerName=remote_client.get("employerName"),
        employerHp=remote_client.get("employerHp"),
        employerAddress=remote_client.get("employerAddress"),
        employerPhone=remote_client.get("employerPhone"),
        addressHouseNumber=remote_client.get("addressHouseNumber"),
        addressApartment=remote_client.get("addressApartment"),
        beneficiaries=beneficiaries or None,
    )


def _get_or_create_local_client(db: Session, remote_client: Dict[str, Any]) -> Client:
    id_number = remote_client.get("idNumber")
    local_client: Client | None = None
    if id_number:
        local_client = db.query(Client).filter(Client.id_number == id_number).first()

    if local_client is None:
        create_payload = _build_client_create(remote_client)
        local_client = crm_service.create_client(db, create_payload)

    update_payload = _build_client_update(remote_client)
    updated = crm_service.update_client(db, local_client.id, update_payload)
    return updated or local_client


def _sync_snapshots_for_client(db: Session, local_client: Client, remote_snapshots: List[Dict[str, Any]]) -> None:
    existing = db.query(Snapshot).filter(Snapshot.client_id == local_client.id).all()
    index: Dict[tuple[str, str, str], Snapshot] = {}
    for s in existing:
        key = (
            (s.fund_number or "").strip(),
            s.snapshot_date or "",
            s.source or "",
        )
        if key not in index:
            index[key] = s

    for item in remote_snapshots:
        fund_number = (item.get("fundNumber") or "").strip()
        snapshot_date = item.get("snapshotDate") or ""
        source = item.get("source") or ""
        key = (fund_number, snapshot_date, source)

        amount_raw = item.get("amount")
        try:
            amount = float(amount_raw) if amount_raw is not None else 0.0
        except Exception:
            amount = 0.0

        if key in index:
            snap = index[key]
            snap.fund_code = item.get("fundCode") or snap.fund_code
            snap.fund_type = item.get("fundType")
            snap.fund_name = item.get("fundName")
            snap.fund_number = fund_number or None
            snap.source = source or None
            snap.amount = amount
            snap.snapshot_date = snapshot_date
            is_active = item.get("isActive")
            if is_active is not None:
                snap.is_active = bool(is_active)
        else:
            snap = Snapshot(
                client_id=local_client.id,
                fund_code=item.get("fundCode") or "",
                fund_type=item.get("fundType"),
                fund_name=item.get("fundName"),
                fund_number=fund_number or None,
                source=source or None,
                amount=amount,
                snapshot_date=snapshot_date,
                is_active=bool(item.get("isActive", True)),
            )
            db.add(snap)
            index[key] = snap


def _sync_existing_products_for_client(db: Session, local_client: Client, remote_products: List[Dict[str, Any]]) -> None:
    existing_rows = db.query(ExistingProduct).filter(ExistingProduct.client_id == local_client.id).all()
    by_personal: Dict[str, ExistingProduct] = {}
    for row in existing_rows:
        if row.personal_number:
            by_personal[row.personal_number] = row

    for item in remote_products:
        if item.get("isVirtual"):
            continue

        personal_number = (item.get("personalNumber") or "").strip()
        if not personal_number:
            continue

        row = by_personal.get(personal_number)
        if row is None:
            row = ExistingProduct(client_id=local_client.id, personal_number=personal_number)
            db.add(row)
            by_personal[personal_number] = row

        row.fund_type = item.get("fundType") or ""
        row.company_name = item.get("companyName") or ""
        row.fund_name = item.get("fundName") or ""
        row.fund_code = item.get("fundCode") or ""
        row.yield_1yr = item.get("yield1yr")
        row.yield_3yr = item.get("yield3yr")
        
        # Sanitize management fee: if it equals the accumulated amount (corruption), reset to None
        raw_fee = item.get("managementFeeBalance")
        raw_amount = item.get("accumulatedAmount")
        if raw_fee is not None and raw_amount is not None and raw_fee > 100 and abs(raw_fee - raw_amount) < 1.0:
             row.management_fee_balance = None
        else:
             row.management_fee_balance = raw_fee

        row.management_fee_contributions = item.get("managementFeeContributions")
        row.accumulated_amount = raw_amount
        row.employment_status = item.get("employmentStatus")
        row.has_regular_contributions = item.get("hasRegularContributions")


def _new_product_key(data: Dict[str, Any]) -> str:
    personal = (str(data.get("personalNumber") or "").strip())
    if personal:
        return f"PN:{personal}"
    fund_code = (str(data.get("fundCode") or "").strip())
    company = (str(data.get("companyName") or "").strip())
    fund_name = (str(data.get("fundName") or "").strip())
    return f"F:{fund_code}|C:{company}|N:{fund_name}"


def _sync_new_products_for_client(
    db: Session,
    local_client: Client,
    remote_existing_products: List[Dict[str, Any]],
    remote_new_products: List[Dict[str, Any]],
) -> None:
    existing_rows = db.query(NewProduct).filter(NewProduct.client_id == local_client.id).all()
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

        row.fund_type = item.get("fundType") or ""
        row.company_name = item.get("companyName") or ""
        row.fund_name = item.get("fundName") or ""
        row.fund_code = item.get("fundCode") or ""
        row.yield_1yr = item.get("yield1yr")
        row.yield_3yr = item.get("yield3yr")
        row.personal_number = (item.get("personalNumber") or "").strip() or None
        row.management_fee_balance = item.get("managementFeeBalance")
        row.management_fee_contributions = item.get("managementFeeContributions")
        row.accumulated_amount = item.get("accumulatedAmount")
        row.employment_status = item.get("employmentStatus")
        row.has_regular_contributions = item.get("hasRegularContributions")

        existing_product_id = item.get("existingProductId")
        if isinstance(existing_product_id, int):
            remote_ep = remote_existing_by_id.get(existing_product_id)
            if remote_ep is not None:
                personal_number_ep = (remote_ep.get("personalNumber") or "").strip()
                if personal_number_ep:
                    local_ep = (
                        db.query(ExistingProduct)
                        .filter(
                            ExistingProduct.client_id == local_client.id,
                            ExistingProduct.personal_number == personal_number_ep,
                        )
                        .first()
                    )
                    if local_ep is not None:
                        row.existing_product_id = local_ep.id


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

            snapshots_url = f"{base_url}/api/v1/crm/clients/{remote_id}/snapshots"
            existing_url = f"{base_url}/api/v1/justification/clients/{remote_id}/existing-products"
            new_products_url = f"{base_url}/api/v1/justification/clients/{remote_id}/new-products"

            try:
                remote_snapshots = _get_json(snapshots_url) or []
            except Exception:
                remote_snapshots = []
            try:
                remote_existing = _get_json(existing_url) or []
            except Exception:
                remote_existing = []
            try:
                remote_new = _get_json(new_products_url) or []
            except Exception:
                remote_new = []

            _sync_snapshots_for_client(db, local_client, remote_snapshots)
            _sync_existing_products_for_client(db, local_client, remote_existing)
            _sync_new_products_for_client(db, local_client, remote_existing, remote_new)

        db.commit()
    finally:
        db.close()


def main() -> None:
    sync_all_clients_from_remote()


if __name__ == "__main__":
    main()
