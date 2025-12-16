from __future__ import annotations

from typing import Any, Dict, List

from sqlalchemy.orm import Session

from app.models import Client, Snapshot
from app.services.sync_remote_utils import _coerce_float, _list_rows_for_client
from app.utils.strings import strip_or_empty as _strip_or_empty


def _snapshot_key(fund_number: Any, snapshot_date: Any, source: Any) -> tuple[str, str, str]:
    return (
        _strip_or_empty(fund_number),
        snapshot_date or "",
        source or "",
    )


def _sync_snapshots_for_client(db: Session, local_client: Client, remote_snapshots: List[Dict[str, Any]]) -> None:
    existing = _list_rows_for_client(db, Snapshot, local_client.id)
    index: Dict[tuple[str, str, str], Snapshot] = {}
    for s in existing:
        key = _snapshot_key(s.fund_number, s.snapshot_date, s.source)
        if key not in index:
            index[key] = s

    for item in remote_snapshots:
        key = _snapshot_key(item.get("fundNumber"), item.get("snapshotDate"), item.get("source"))
        fund_number, snapshot_date, source = key

        amount = _coerce_float(item.get("amount"), default=0.0)

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
