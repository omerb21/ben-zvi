from typing import Dict
from pathlib import Path
from datetime import date, datetime

import pandas as pd
from sqlalchemy.orm import Session

from app.models import Client, Snapshot
from app.migration.legacy_mini_crm import MiniCrmClient, MiniCrmSnapshot, get_mini_crm_session
from app.utils.id_normalization import normalize_id_number


def migrate_mini_crm(db: Session, mini_crm_url: str | None = None) -> Dict[str, int]:
    source_session = get_mini_crm_session(mini_crm_url)
    created_clients = 0
    reused_clients = 0
    created_snapshots = 0

    try:
        clients_by_id: Dict[str, Client] = {}
        for existing in db.query(Client).all():
            key_source = existing.id_number or existing.id_number_raw
            key = normalize_id_number(key_source)
            if not key:
                continue
            if key not in clients_by_id:
                clients_by_id[key] = existing

        legacy_clients = source_session.query(MiniCrmClient).all()

        for legacy_client in legacy_clients:
            id_number_raw = legacy_client.id_canon
            id_number = normalize_id_number(id_number_raw)
            if not id_number:
                continue

            full_name = legacy_client.name

            client = clients_by_id.get(id_number)

            if client is None:
                client = Client(
                    id_number_raw=id_number_raw,
                    id_number=id_number,
                    full_name=full_name,
                )
                db.add(client)
                db.flush()
                clients_by_id[id_number] = client
                created_clients += 1
            else:
                reused_clients += 1

            legacy_snapshots = (
                source_session.query(MiniCrmSnapshot)
                .filter(MiniCrmSnapshot.client_id == legacy_client.id)
                .all()
            )

            for legacy_snapshot in legacy_snapshots:
                snapshot = Snapshot(
                    client_id=client.id,
                    fund_code=legacy_snapshot.fund_code,
                    fund_type=legacy_snapshot.fund_type,
                    fund_name=legacy_snapshot.fund_name,
                    fund_number=getattr(legacy_snapshot, "fund_number", None),
                    source=getattr(legacy_snapshot, "source", None),
                    amount=legacy_snapshot.amount,
                    snapshot_date=legacy_snapshot.snapshot_date,
                    is_active=bool(getattr(legacy_snapshot, "is_active", True)),
                )
                db.add(snapshot)
                created_snapshots += 1

        db.commit()

        return {
            "created_clients": created_clients,
            "reused_clients": reused_clients,
            "created_snapshots": created_snapshots,
        }
    finally:
        source_session.close()


def migrate_legacy_crm_clients_from_excel(
    db: Session,
    excel_path: str | None = None,
) -> Dict[str, int]:
    """Import or back-fill client personal details from legacy Clients.xlsx.

    This helper:
    - Loads the legacy Clients.xlsx from dev/mini_crm/uploads by default.
    - Uses the same ID canonicalization as other migrations.
    - Creates Client rows when missing.
    - Back-fills missing personal fields on existing Client rows without
      overwriting populated values.
    """

    if excel_path is None:
        root = Path(__file__).resolve()
        dev_dir = root.parents[4]
        excel_file = dev_dir / "mini_crm" / "uploads" / "Clients.xlsx"
    else:
        excel_file = Path(excel_path)

    if not excel_file.is_file():
        raise ValueError(f"Legacy CRM clients Excel not found at {excel_file}")

    df = pd.read_excel(excel_file, dtype=str)
    if df is None or df.empty:
        raise ValueError("Legacy CRM clients Excel is empty")

    df.columns = [str(c).strip() for c in df.columns]

    # Map existing clients by canonical ID number
    clients_by_id: Dict[str, Client] = {}
    for existing in db.query(Client).all():
        key_source = existing.id_number or existing.id_number_raw
        key = normalize_id_number(key_source)
        if not key:
            continue
        if key not in clients_by_id:
            clients_by_id[key] = existing

    created_clients = 0
    updated_clients = 0
    reused_clients = 0
    rows_processed = 0

    col_first = "פרטי"
    col_last = "משפחה"
    col_id = "תז"
    col_phone = "טלפון"
    col_email = "דואל"
    col_city = "עיר"
    col_street = "רחוב"
    col_house = "מספר"
    col_gender = "מין"
    col_status = "סטטוס"
    col_birth_date = "ת לידה"
    birth_date_candidates = [
        "ת לידה",
        "תאריך לידה",
        "ת. לידה",
        "ת.לידה",
    ]
    for name in birth_date_candidates:
        if name in df.columns:
            col_birth_date = name
            break
    col_birth_country = "ארץ לידה"
    col_employer_name = "מעסיק"
    col_employer_hp = "חפ מעסיק"
    col_employer_address = "כתובת מעסיק"
    col_employer_phone = "טלפון מעסיק"

    for _, row in df.iterrows():
        rows_processed += 1

        raw_id = str(row.get(col_id, "") or "").strip()
        if not raw_id:
            continue
        id_number = normalize_id_number(raw_id)
        if not id_number:
            continue

        first_name = str(row.get(col_first, "") or "").strip() or None
        last_name = str(row.get(col_last, "") or "").strip() or None
        name_parts = [p for p in [first_name, last_name] if p]
        full_name = " ".join(name_parts) if name_parts else id_number

        phone = str(row.get(col_phone, "") or "").strip() or None
        email = str(row.get(col_email, "") or "").strip() or None
        city = str(row.get(col_city, "") or "").strip() or None
        street_name = str(row.get(col_street, "") or "").strip()

        raw_house = row.get(col_house, "") or ""
        house_text = str(raw_house).strip()
        if not house_text or house_text.lower() == "nan":
            house_number = None
        else:
            house_number = house_text

        if street_name and house_number:
            street = f"{street_name} {house_number}"
        else:
            street = street_name or None
        gender = str(row.get(col_gender, "") or "").strip() or None
        marital_status = str(row.get(col_status, "") or "").strip() or None

        raw_birth_date = str(row.get(col_birth_date, "") or "").strip()
        birth_date: date | None = None
        if raw_birth_date:
            for fmt in ("%d/%m/%Y", "%d-%m-%Y", "%Y-%m-%d", "%d.%m.%Y"):
                try:
                    birth_date = datetime.strptime(raw_birth_date, fmt).date()
                    break
                except ValueError:
                    continue
            if birth_date is None:
                try:
                    parsed = pd.to_datetime(raw_birth_date, dayfirst=True, errors="coerce")
                    if pd.notna(parsed):
                        birth_date = parsed.date()
                except Exception:
                    birth_date = None

        birth_country = str(row.get(col_birth_country, "") or "").strip() or None
        employer_name = str(row.get(col_employer_name, "") or "").strip() or None
        employer_hp = str(row.get(col_employer_hp, "") or "").strip() or None
        employer_address = str(row.get(col_employer_address, "") or "").strip() or None
        employer_phone = str(row.get(col_employer_phone, "") or "").strip() or None

        client = clients_by_id.get(id_number)

        if client is None:
            reused_clients += 1
            continue

        changed = False

        if not client.first_name and first_name:
            client.first_name = first_name
            changed = True
        if not client.last_name and last_name:
            client.last_name = last_name
            changed = True
        if not client.email and email:
            client.email = email
            changed = True
        if not client.phone and phone:
            client.phone = phone
            changed = True
        if not client.address_city and city:
            client.address_city = city
            changed = True
        if not client.address_street and street:
            client.address_street = street
            changed = True
        if (not client.address_house_number) and house_number:
            client.address_house_number = house_number
            changed = True
        if (not client.birth_date or client.birth_date == date(1970, 1, 1)) and birth_date:
            client.birth_date = birth_date
            changed = True
        if not client.gender and gender:
            client.gender = gender
            changed = True
        if not client.marital_status and marital_status:
            client.marital_status = marital_status
            changed = True
        if not client.birth_country and birth_country:
            client.birth_country = birth_country
            changed = True
        if not client.employer_name and employer_name:
            client.employer_name = employer_name
            changed = True
        if not client.employer_hp and employer_hp:
            client.employer_hp = employer_hp
            changed = True
        if not client.employer_address and employer_address:
            client.employer_address = employer_address
            changed = True
        if not client.employer_phone and employer_phone:
            client.employer_phone = employer_phone
            changed = True

        if (not client.full_name or client.full_name == client.id_number) and name_parts:
            client.full_name = full_name
            changed = True

        if changed:
            updated_clients += 1
        else:
            reused_clients += 1

    db.commit()

    return {
        "created_clients": created_clients,
        "updated_clients": updated_clients,
        "reused_clients": reused_clients,
        "rows_processed": rows_processed,
    }
