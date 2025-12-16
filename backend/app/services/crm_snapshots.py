from __future__ import annotations

from collections import defaultdict
from typing import Optional, List, Dict, Any

from sqlalchemy.orm import Session

from app.models import Client, Snapshot
from app.services import crm_snapshots_helpers as _helpers


def _extract_month(value: Optional[str]) -> Optional[str]:
    return _helpers._extract_month(value)


def _build_monthly_totals(snapshots: List[Snapshot]) -> Dict[str, float]:
    return _helpers._build_monthly_totals(snapshots)


def _empty_client_summary_row(client: Client) -> Dict[str, Any]:
    return _helpers._empty_client_summary_row(client)


def _init_client_summary_bucket(client: Client) -> Dict[str, Any]:
    return _helpers._init_client_summary_bucket(client)


def get_snapshot_summary(
    db: Session,
    month: Optional[str] = None,
) -> tuple[Optional[str], float, Dict[str, float], Dict[str, float]]:
    return _helpers.get_snapshot_summary(db, month=month)


def get_monthly_change(db: Session) -> List[Dict[str, Optional[float]]]:
    return _helpers.get_monthly_change(db)


def get_history(db: Session, client_id: Optional[int]) -> List[Dict[str, float]]:
    return _helpers.get_history(db, client_id)


def get_fund_history(
    db: Session,
    client_id: int,
    fund_number: str,
) -> List[Dict[str, Optional[float]]]:
    return _helpers.get_fund_history(db, client_id, fund_number)


def list_client_summaries(db: Session, month: Optional[str] = None) -> List[Dict[str, Any]]:
    return _helpers.list_client_summaries(db, month=month)
