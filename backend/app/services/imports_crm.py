from typing import Dict, Any, Optional
from pathlib import Path
import os
import sys

import pandas as pd
from sqlalchemy.orm import Session

from app.models import Client, Snapshot
from app.services import imports_crm_helpers as _helpers
from app.utils.id_normalization import normalize_id_number
from app.utils.strings import coerce_stripped as _coerce_stripped
from app.utils.strings import coerce_stripped_or_none as _coerce_stripped_or_none


def _snapshot_key(client_id: int, fund_number: Any, snapshot_date: str) -> tuple[int, str, str]:
    return _helpers._snapshot_key(client_id, fund_number, snapshot_date)


def _normalize_company_code(raw_code: str) -> str:
    return _helpers._normalize_company_code(raw_code)


def _ensure_legacy_mini_crm_on_sys_path() -> None:
    env_root = os.getenv("MINI_CRM_ROOT")
    candidates: list[Path] = []
    if env_root:
        candidates.append(Path(env_root))

    root = Path(__file__).resolve()
    workspace_dir = root.parents[4]
    candidates.extend(
        [
            workspace_dir / "mini_crm",
            workspace_dir / "גיבויים" / "mini_crm",
        ]
    )

    for candidate in candidates:
        legacy_root = candidate.resolve()
        if legacy_root.is_dir():
            legacy_path = str(legacy_root)
            if legacy_path not in sys.path:
                sys.path.append(legacy_path)
            return


def _load_legacy_transformer():
    _ensure_legacy_mini_crm_on_sys_path()
    try:
        from services.upload_service import UploadProcessingError, transform_uploaded_file
    except Exception as exc:  # pragma: no cover - defensive
        raise ValueError("Legacy CRM ingestion module is not available") from exc
    return UploadProcessingError, transform_uploaded_file


def _normalize_snapshot_month(snapshot_month: str) -> str:
    return _helpers._normalize_snapshot_month(snapshot_month)


def _snapshot_month_to_snapshot_date(normalized_snapshot_month: str) -> str:
    return _helpers._snapshot_month_to_snapshot_date(normalized_snapshot_month)


def _build_clients_by_id(db: Session) -> Dict[str, Client]:
    return _helpers._build_clients_by_id(db)


def _build_snapshot_index(db: Session, company: str) -> dict[tuple[int, str, str], Snapshot]:
    return _helpers._build_snapshot_index(db, company)


def _resolve_fund_code(raw_fund_code: Any, fund_number: str | None) -> str:
    return _helpers._resolve_fund_code(raw_fund_code, fund_number)


def _parse_positive_amount(value: Any) -> Optional[float]:
    return _helpers._parse_positive_amount(value)


def _get_or_create_client_for_import(
    db: Session,
    *,
    clients_by_id: Dict[str, Client],
    id_number: str,
    id_number_raw: str,
    full_name: str,
) -> tuple[Client, bool]:
    return _helpers._get_or_create_client_for_import(
        db,
        clients_by_id=clients_by_id,
        id_number=id_number,
        id_number_raw=id_number_raw,
        full_name=full_name,
    )


def _update_existing_snapshot_for_import(
    existing_snapshot: Snapshot,
    *,
    fund_code: str,
    fund_type: str | None,
    fund_name: str | None,
    fund_number: str | None,
    amount_value: float,
) -> None:
    return _helpers._update_existing_snapshot_for_import(
        existing_snapshot,
        fund_code=fund_code,
        fund_type=fund_type,
        fund_name=fund_name,
        fund_number=fund_number,
        amount_value=amount_value,
    )


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
    return _helpers._create_snapshot_for_import(
        client_id=client_id,
        fund_code=fund_code,
        fund_type=fund_type,
        fund_name=fund_name,
        fund_number=fund_number,
        company=company,
        amount_value=amount_value,
        snapshot_date=snapshot_date,
    )


def _read_excel_bytes_or_raise(file_bytes: bytes) -> pd.DataFrame:
    return _helpers._read_excel_bytes_or_raise(file_bytes)


def _transform_legacy_crm_excel_or_raise(
    df_raw: pd.DataFrame,
    *,
    filename: str | None,
    normalized_snapshot_month: str,
    transform_uploaded_file,
    UploadProcessingError,
):
    return _helpers._transform_legacy_crm_excel_or_raise(
        df_raw,
        filename=filename,
        normalized_snapshot_month=normalized_snapshot_month,
        transform_uploaded_file=transform_uploaded_file,
        UploadProcessingError=UploadProcessingError,
    )


def _aggregate_crm_balances_like_legacy(df: pd.DataFrame) -> pd.DataFrame:
    return _helpers._aggregate_crm_balances_like_legacy(df)


def import_crm_from_excel(
    db: Session,
    company_code: str,
    file_bytes: bytes,
    snapshot_month: str | None = None,
    filename: str | None = None,
) -> Dict[str, int | str]:
    df_raw = _read_excel_bytes_or_raise(file_bytes)

    if not snapshot_month:
        raise ValueError("חסר תאריך סנפשוט")

    # Normalize the snapshot month string so that both YYYY-MM-DD and
    # YYYY-MM (from <input type="month">) are accepted. The legacy
    # Mini-CRM loaders expect a full date string.
    normalized_snapshot_month = _normalize_snapshot_month(snapshot_month)

    UploadProcessingError = None
    transform_uploaded_file = None
    use_legacy_transformer = True
    try:
        UploadProcessingError, transform_uploaded_file = _load_legacy_transformer()
    except ValueError as exc:
        use_legacy_transformer = False

    if use_legacy_transformer:
        # Let the legacy service choose the correct loader by filename and
        # perform all column mapping / cleaning per provider (FNX, AS, YL, MOR,
        # ANLST, DASH, NFTY).
        df, file_type = _transform_legacy_crm_excel_or_raise(
            df_raw,
            filename=filename,
            normalized_snapshot_month=normalized_snapshot_month,
            transform_uploaded_file=transform_uploaded_file,
            UploadProcessingError=UploadProcessingError,
        )
    else:
        # Fallback: allow importing a normalized Excel file without depending on
        # the legacy mini_crm package.
        df, file_type = _helpers._transform_fallback_crm_excel_or_raise(
            df_raw,
            filename=filename,
            company_code=company_code,
        )

    # Aggregate by client + fund number exactly like legacy insert_rows.
    df = _aggregate_crm_balances_like_legacy(df)

    # Normalize snapshot date to first day of month (legacy behavior).
    snapshot_date = _snapshot_month_to_snapshot_date(normalized_snapshot_month)

    company = (file_type or "").upper()

    clients_by_id = _build_clients_by_id(db)
    # Use the same logical key as the legacy Mini-CRM unique index:
    # (client_id, fund_number, snapshot_date, source). In the unified
    # schema we key by (client_id, fund_number, snapshot_date) per
    # company/source and update existing rows instead of creating
    # duplicates when importing the same file/month again.
    snapshot_by_key = _build_snapshot_index(db, company)

    created_clients = 0
    reused_clients = 0
    created_snapshots = 0
    duplicates_skipped = 0
    rows_processed = 0

    for _, row in df.iterrows():
        rows_processed += 1

        id_number_raw = _coerce_stripped(row.get("id_canon", ""))
        if not id_number_raw:
            continue

        id_number = normalize_id_number(id_number_raw)
        if not id_number:
            continue

        full_name = _coerce_stripped(row.get("client_name", "")) or id_number_raw

        fund_number = _coerce_stripped_or_none(row.get("fund_number", ""))
        fund_name = _coerce_stripped_or_none(row.get("fund_name", ""))

        fund_code = _resolve_fund_code(row.get("fund_code"), fund_number)

        fund_type = _coerce_stripped_or_none(row.get("fund_type", ""))

        amount_value = _parse_positive_amount(row.get("accumulated_amount", 0))
        if amount_value is None:
            continue

        client, created_client = _get_or_create_client_for_import(
            db,
            clients_by_id=clients_by_id,
            id_number=id_number,
            id_number_raw=id_number_raw,
            full_name=full_name,
        )
        if created_client:
            created_clients += 1
        else:
            reused_clients += 1

        key = _snapshot_key(client.id, fund_number, snapshot_date)
        existing_snapshot = snapshot_by_key.get(key)
        if existing_snapshot is not None:
            # Overwrite previous data for the same client+fund+month+source,
            # mirroring the legacy INSERT OR REPLACE behavior so repeated
            # imports for the same file/month do not create double balances.
            _update_existing_snapshot_for_import(
                existing_snapshot,
                fund_code=fund_code,
                fund_type=fund_type,
                fund_name=fund_name,
                fund_number=fund_number,
                amount_value=amount_value,
            )
            duplicates_skipped += 1
            continue

        snapshot = _create_snapshot_for_import(
            client_id=client.id,
            fund_code=fund_code,
            fund_type=fund_type,
            fund_name=fund_name,
            fund_number=fund_number,
            company=company,
            amount_value=amount_value,
            snapshot_date=snapshot_date,
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
