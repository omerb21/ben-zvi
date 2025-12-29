from __future__ import annotations

from datetime import datetime
from io import BytesIO
from typing import Any, Dict, Optional

import pandas as pd
from sqlalchemy.orm import Session

from app.models import Client, Snapshot
from app.utils.id_normalization import normalize_id_number
from app.utils.strings import strip_or_empty as _strip_or_empty
from app.utils.strings import coerce_stripped as _coerce_stripped
from app.utils.strings import coerce_stripped_or_none as _coerce_stripped_or_none


def _snapshot_key(client_id: int, fund_number: Any, snapshot_date: str) -> tuple[int, str, str]:
    return (client_id, _strip_or_empty(fund_number), snapshot_date)


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


def _normalize_snapshot_month(snapshot_month: str) -> str:
    snapshot_month = (snapshot_month or "").strip()
    if len(snapshot_month) == 7:
        return f"{snapshot_month}-01"
    return snapshot_month


def _snapshot_month_to_snapshot_date(normalized_snapshot_month: str) -> str:
    try:
        snap_dt = datetime.strptime(normalized_snapshot_month, "%Y-%m-%d")
    except ValueError as exc:
        raise ValueError("תאריך סנפשוט אינו בפורמט חוקי (YYYY-MM או YYYY-MM-DD)") from exc
    return snap_dt.replace(day=1).strftime("%Y-%m-%d")


def _build_clients_by_id(db: Session) -> Dict[str, Client]:
    clients_by_id: Dict[str, Client] = {}
    for client in db.query(Client).all():
        key_source = client.id_number or client.id_number_raw
        key = normalize_id_number(key_source)
        if not key:
            continue
        if key not in clients_by_id:
            clients_by_id[key] = client
    return clients_by_id


def _build_snapshot_index(db: Session, company: str) -> dict[tuple[int, str, str], Snapshot]:
    existing_snapshots = db.query(Snapshot).filter(Snapshot.source == company).all()
    snapshot_by_key: dict[tuple[int, str, str], Snapshot] = {}
    for s in existing_snapshots:
        key = _snapshot_key(s.client_id, s.fund_number, s.snapshot_date)
        snapshot_by_key[key] = s
    return snapshot_by_key


def _resolve_fund_code(raw_fund_code: Any, fund_number: str | None) -> str:
    if raw_fund_code is None or str(raw_fund_code).strip() == "":
        return _strip_or_empty(fund_number)
    return str(raw_fund_code).strip()


def _parse_positive_amount(value: Any) -> Optional[float]:
    try:
        amount_value = float(value or 0)
    except Exception:
        return None
    if amount_value <= 0:
        return None
    return amount_value


def _get_or_create_client_for_import(
    db: Session,
    *,
    clients_by_id: Dict[str, Client],
    id_number: str,
    id_number_raw: str,
    full_name: str,
) -> tuple[Client, bool]:
    client = clients_by_id.get(id_number)
    if client is not None:
        return client, False

    client = Client(
        id_number_raw=id_number_raw,
        id_number=id_number,
        full_name=full_name,
    )
    db.add(client)
    db.flush()
    clients_by_id[id_number] = client
    return client, True


def _update_existing_snapshot_for_import(
    existing_snapshot: Snapshot,
    *,
    fund_code: str,
    fund_type: str | None,
    fund_name: str | None,
    fund_number: str | None,
    amount_value: float,
) -> None:
    existing_snapshot.fund_code = fund_code
    existing_snapshot.fund_type = fund_type
    existing_snapshot.fund_name = fund_name
    existing_snapshot.fund_number = fund_number
    existing_snapshot.amount = amount_value
    existing_snapshot.is_active = True


def _create_snapshot_for_import(
    *,
    client_id: int,
    fund_code: str,
    fund_type: str | None,
    fund_name: str | None,
    fund_number: str | None,
    company: str,
    amount_value: float,
    snapshot_date: str,
) -> Snapshot:
    return Snapshot(
        client_id=client_id,
        fund_code=fund_code,
        fund_type=fund_type,
        fund_name=fund_name,
        fund_number=fund_number,
        source=company,
        amount=amount_value,
        snapshot_date=snapshot_date,
        is_active=True,
    )


def _read_excel_bytes_or_raise(file_bytes: bytes) -> pd.DataFrame:
    buffer = BytesIO(file_bytes)
    df_raw = pd.read_excel(buffer, dtype=str)
    if df_raw is None or df_raw.empty:
        raise ValueError("Excel file is empty")
    return df_raw


def _transform_legacy_crm_excel_or_raise(
    df_raw: pd.DataFrame,
    *,
    filename: str | None,
    normalized_snapshot_month: str,
    transform_uploaded_file,
    UploadProcessingError,
):
    try:
        return transform_uploaded_file(df_raw, filename or "", normalized_snapshot_month)
    except UploadProcessingError as exc:
        raise ValueError(exc.user_message) from exc


def _aggregate_crm_balances_like_legacy(df: pd.DataFrame) -> pd.DataFrame:
    if "id_canon" in df.columns and "fund_number" in df.columns:
        agg_dict: Dict[str, str] = {"accumulated_amount": "sum"}
        for col in ("client_name", "fund_type", "fund_code", "fund_name"):
            if col in df.columns:
                agg_dict[col] = "first"
        df = df.groupby(["id_canon", "fund_number"], dropna=False).agg(agg_dict).reset_index()
    return df


def _transform_fallback_crm_excel_or_raise(
    df_raw: pd.DataFrame,
    *,
    filename: str | None,
    company_code: str | None,
):
    """Fallback transformer when legacy mini_crm loader is unavailable.

    Accepts an Excel file that is already normalized to the columns expected by the
    unified import pipeline.
    """

    required = {"id_canon", "fund_number", "accumulated_amount"}
    missing = sorted(col for col in required if col not in df_raw.columns)
    if missing:
        raise ValueError(
            "Legacy CRM ingestion module is not available, and the uploaded Excel file does not contain the required columns: "
            + ", ".join(missing)
        )

    df = df_raw.copy()

    file_type = ""
    if company_code:
        file_type = (company_code or "").strip().upper()
    if not file_type and filename:
        base = filename.split("/")[-1].split("\\")[-1]
        prefix = base.split("_")[0].split("-")[0].strip()
        file_type = prefix.upper()

    return df, file_type
