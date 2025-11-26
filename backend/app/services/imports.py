from io import BytesIO
from typing import Dict
from pathlib import Path
import sys

import pandas as pd
from sqlalchemy.orm import Session
from xml.etree import ElementTree as ET

from app.models import Client, Snapshot, SavingProduct
from app.utils.source_names import get_source_display_name
from app.utils.id_normalization import normalize_id_number


def _normalize_company_code(raw_code: str) -> str:
    code = (raw_code or "").strip().lower()
    mapping = {
        "fnx": "FNX",
        "as": "AS",
        "ds": "DASH",
        "dash": "DASH",
        "anlst": "ANLST",
        "yl": "YL",
        "mor": "MOR",
        "nfty": "NFTY",
    }
    return mapping.get(code, (raw_code or "").strip().upper())


def import_crm_from_excel(
    db: Session,
    company_code: str,
    file_bytes: bytes,
    snapshot_month: str | None = None,
    filename: str | None = None,
) -> Dict[str, int | str]:
    """Import CRM balances from Excel using the exact legacy Mini‑CRM logic.

    The function delegates Excel parsing and normalization to the old
    `mini_crm` ingestion pipeline (per‑provider loaders) and then maps the
    resulting rows into the unified SQLAlchemy models.
    """
    from datetime import datetime

    # Locate legacy mini_crm project relative to this backend and ensure it
    # is importable, without modifying any of its files.
    root = Path(__file__).resolve()
    dev_dir = root.parents[4]
    legacy_root = dev_dir / "mini_crm"
    if legacy_root.is_dir():
        legacy_path = str(legacy_root)
        if legacy_path not in sys.path:
            sys.path.append(legacy_path)

    try:
        from services.upload_service import UploadProcessingError, transform_uploaded_file
    except Exception as exc:  # pragma: no cover - defensive
        raise ValueError("Legacy CRM ingestion module is not available") from exc

    buffer = BytesIO(file_bytes)
    df_raw = pd.read_excel(buffer, dtype=str)
    if df_raw is None or df_raw.empty:
        raise ValueError("Excel file is empty")

    if not snapshot_month:
        raise ValueError("חסר תאריך סנפשוט")

    # Let the legacy service choose the correct loader by filename and
    # perform all column mapping / cleaning per provider (FNX, AS, YL, MOR,
    # ANLST, DASH, NFTY).
    try:
        df, file_type = transform_uploaded_file(df_raw, filename or "", snapshot_month)
    except UploadProcessingError as exc:
        raise ValueError(exc.user_message) from exc

    # Aggregate by client + fund number exactly like legacy insert_rows.
    if "id_canon" in df.columns and "fund_number" in df.columns:
        agg_dict: Dict[str, str] = {"accumulated_amount": "sum"}
        for col in ("client_name", "fund_type", "fund_code", "fund_name"):
            if col in df.columns:
                agg_dict[col] = "first"
        df = (
            df.groupby(["id_canon", "fund_number"], dropna=False)
            .agg(agg_dict)
            .reset_index()
        )

    # Normalize snapshot date to first day of month (legacy behavior).
    try:
        snap_dt = datetime.strptime(snapshot_month, "%Y-%m-%d")
    except ValueError:
        # Fallback: accept YYYY-MM and treat as first day of month
        snap_dt = datetime.strptime(snapshot_month + "-01", "%Y-%m-%d")
    snapshot_date = snap_dt.replace(day=1).strftime("%Y-%m-%d")

    company = (file_type or "").upper()

    clients_by_id: Dict[str, Client] = {}
    for client in db.query(Client).all():
        key_source = client.id_number or client.id_number_raw
        key = normalize_id_number(key_source)
        if not key:
            continue
        if key not in clients_by_id:
            clients_by_id[key] = client

    existing_snapshots = (
        db.query(Snapshot)
        .filter(Snapshot.source == company)
        .all()
    )
    # Use the same logical key as the legacy Mini-CRM unique index:
    # (client_id, fund_number, snapshot_date, source). In the unified
    # schema we key by (client_id, fund_number, snapshot_date) per
    # company/source and update existing rows instead of creating
    # duplicates when importing the same file/month again.
    snapshot_by_key: dict[tuple[int, str, str], Snapshot] = {}
    for s in existing_snapshots:
        key = (s.client_id, (s.fund_number or "").strip(), s.snapshot_date)
        snapshot_by_key[key] = s

    created_clients = 0
    reused_clients = 0
    created_snapshots = 0
    duplicates_skipped = 0
    rows_processed = 0

    for _, row in df.iterrows():
        rows_processed += 1

        id_number_raw = str(row.get("id_canon", "")).strip()
        if not id_number_raw:
            continue

        id_number = normalize_id_number(id_number_raw)
        if not id_number:
            continue

        full_name = str(row.get("client_name", "")).strip() or id_number_raw

        fund_number = str(row.get("fund_number", "")).strip() or None
        fund_name = str(row.get("fund_name", "")).strip() or None

        raw_fund_code = row.get("fund_code")
        if raw_fund_code is None or str(raw_fund_code).strip() == "":
            fund_code = (fund_number or "").strip() if fund_number else ""
        else:
            fund_code = str(raw_fund_code).strip()

        fund_type = str(row.get("fund_type", "")).strip() or None

        try:
            amount_value = float(row.get("accumulated_amount", 0) or 0)
        except Exception:
            continue
        if amount_value <= 0:
            continue

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

        key = (client.id, (fund_number or "").strip(), snapshot_date)
        existing_snapshot = snapshot_by_key.get(key)
        if existing_snapshot is not None:
            # Overwrite previous data for the same client+fund+month+source,
            # mirroring the legacy INSERT OR REPLACE behavior so repeated
            # imports for the same file/month do not create double balances.
            existing_snapshot.fund_code = fund_code
            existing_snapshot.fund_type = fund_type
            existing_snapshot.fund_name = fund_name
            existing_snapshot.fund_number = fund_number
            existing_snapshot.amount = amount_value
            existing_snapshot.is_active = True
            duplicates_skipped += 1
            continue

        snapshot = Snapshot(
            client_id=client.id,
            fund_code=fund_code,
            fund_type=fund_type,
            fund_name=fund_name,
            fund_number=fund_number,
            source=company,
            amount=amount_value,
            snapshot_date=snapshot_date,
            is_active=True,
        )
        db.add(snapshot)
        snapshot_by_key[key] = snapshot
        created_snapshots += 1

    db.commit()

    return {
        "companyCode": company,
        "createdClients": created_clients,
        "reusedClients": reused_clients,
        "createdSnapshots": created_snapshots,
        "rowsProcessed": rows_processed,
        "duplicatesSkipped": duplicates_skipped,
    }


def import_saving_products_from_gemelnet_xml(db: Session, file_bytes: bytes) -> Dict[str, int]:
    root = ET.fromstring(file_bytes)

    existing = db.query(SavingProduct).all()
    index: dict[tuple[str, str, str, str], SavingProduct] = {}
    for sp in existing:
        key = (sp.fund_type or "", sp.company_name or "", sp.fund_name or "", sp.fund_code or "")
        index[key] = sp

    created = 0
    updated = 0
    rows_processed = 0
    duplicates_skipped = 0

    def _to_float(value: str | None) -> float | None:
        if value is None:
            return None
        text = str(value).strip().replace("%", "")
        if not text:
            return None
        try:
            return float(text)
        except Exception:
            return None

    for elem in root.findall(".//Row"):
        rows_processed += 1

        fund_code = (elem.findtext("ID") or "").strip()
        fund_name = (elem.findtext("SHM_KUPA") or "").strip()
        company_name = (elem.findtext("SHM_HEVRA_MENAHELET") or "").strip()

        if not fund_code or not fund_name or not company_name:
            continue

        # Yields: mirror the legacy justification logic
        yield_1yr = _to_float(elem.findtext("TSUA_MITZTABERET_LETKUFA"))
        yield_3yr = _to_float(elem.findtext("TSUA_MITZTABERET_36_HODASHIM"))

        if not yield_1yr:
            yield_1yr = _to_float(elem.findtext("TSUA_SHNATIT_MEMUZAAT_3_SHANIM"))
        if not yield_3yr:
            yield_3yr = _to_float(elem.findtext("TSUA_MEMUZAAT_36_HODASHIM"))

        # Fund type heuristics: default "גמל" with special handling for
        # "גמל להשקעה" ו"השתלמות" כמו במערכת ההנמקה הישנה.
        fund_type = "גמל"
        text_for_type = f"{fund_name} {company_name}"
        if "גמל להשקעה" in text_for_type:
            fund_type = "גמל להשקעה"
        elif (("חסכון פלוס" in (fund_name or "")) or ("חיסכון פלוס" in (fund_name or ""))) and (
            "אלטשולר" in (company_name or "")
        ):
            fund_type = "גמל להשקעה"
        elif "השתלמות" in text_for_type:
            fund_type = "השתלמות"

        risk_level = None
        guaranteed_return = None

        key = (fund_type, company_name, fund_name, fund_code)
        sp = index.get(key)
        if sp is None:
            sp = SavingProduct(
                fund_type=fund_type,
                company_name=company_name,
                fund_name=fund_name,
                fund_code=fund_code,
                yield_1yr=yield_1yr,
                yield_3yr=yield_3yr,
                risk_level=risk_level,
                guaranteed_return=guaranteed_return,
            )
            db.add(sp)
            index[key] = sp
            created += 1
        else:
            prev = (
                sp.yield_1yr,
                sp.yield_3yr,
                sp.risk_level,
                sp.guaranteed_return,
            )
            sp.yield_1yr = yield_1yr
            sp.yield_3yr = yield_3yr
            sp.risk_level = risk_level
            sp.guaranteed_return = guaranteed_return
            now = (
                sp.yield_1yr,
                sp.yield_3yr,
                sp.risk_level,
                sp.guaranteed_return,
            )
            if now != prev:
                updated += 1
            else:
                duplicates_skipped += 1

    db.commit()

    return {
        "createdSavingProducts": created,
        "updatedSavingProducts": updated,
        "rowsProcessed": rows_processed,
        "duplicatesSkipped": duplicates_skipped,
    }
