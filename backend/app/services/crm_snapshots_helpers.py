from __future__ import annotations

from collections import defaultdict
from typing import Optional, List, Dict, Any

from sqlalchemy.orm import Session

from app.models import Client, Snapshot
from app.utils.numbers import coerce_amount as _coerce_amount


def _extract_month(value: Optional[str]) -> Optional[str]:
    if not value or len(value) < 7:
        return None
    return value[:7]


def _build_monthly_totals(snapshots: List[Snapshot]) -> Dict[str, float]:
    totals: Dict[str, float] = defaultdict(float)
    for s in snapshots:
        ym = _extract_month(s.snapshot_date)
        if not ym:
            continue
        totals[ym] += _coerce_amount(s.amount)
    return totals


def _empty_client_summary_row(client: Client) -> Dict[str, Any]:
    return {
        "id": client.id,
        "full_name": client.full_name,
        "id_number": client.id_number,
        "total_amount": 0.0,
        "sources": [],
        "fund_numbers": set(),
        "last_update": None,
    }


def _init_client_summary_bucket(client: Client) -> Dict[str, Any]:
    return {
        "id": client.id,
        "full_name": client.full_name,
        "id_number": client.id_number,
        "total_amount": 0.0,
        "sources": set(),
        "fund_numbers": set(),
        "last_update": None,
    }


def get_snapshot_summary(
    db: Session,
    month: Optional[str] = None,
) -> tuple[Optional[str], float, Dict[str, float], Dict[str, float]]:
    snapshots = db.query(Snapshot).filter(Snapshot.is_active.is_(True)).all()

    if not snapshots:
        return month, 0.0, {}, {}

    months = sorted({m for m in (_extract_month(s.snapshot_date) for s in snapshots) if m})
    if not months:
        return month, 0.0, {}, {}

    target_month = month or months[-1]

    total = 0.0
    by_source: Dict[str, float] = defaultdict(float)
    by_type: Dict[str, float] = defaultdict(float)

    for s in snapshots:
        ym = _extract_month(s.snapshot_date)
        if ym != target_month:
            continue
        amount = _coerce_amount(s.amount)
        total += amount

        src = s.source or "לא ידוע"
        by_source[src] += amount

        ftype = s.fund_type or "לא זמין"
        by_type[ftype] += amount

    return target_month, round(total, 2), dict(by_source), dict(by_type)


def get_monthly_change(db: Session) -> List[Dict[str, Optional[float]]]:
    snapshots = db.query(Snapshot).filter(Snapshot.is_active.is_(True)).all()
    if not snapshots:
        return []

    totals = _build_monthly_totals(snapshots)

    points: List[Dict[str, Optional[float]]] = []
    prev_total: Optional[float] = None
    for ym in sorted(totals.keys()):
        total = totals[ym]
        if prev_total is None:
            change = None
            pct = None
        else:
            change = total - prev_total
            pct = (change / prev_total * 100.0) if prev_total > 0 else None

        points.append(
            {
                "month": ym,
                "total": total,
                "change": change,
                "percent_change": pct,
            }
        )
        prev_total = total

    return points


def get_history(db: Session, client_id: Optional[int]) -> List[Dict[str, float]]:
    query = db.query(Snapshot).filter(Snapshot.is_active.is_(True))
    if client_id and client_id != 0:
        query = query.filter(Snapshot.client_id == client_id)

    snapshots = query.all()
    if not snapshots:
        return []

    totals = _build_monthly_totals(snapshots)

    return [{"month": ym, "amount": round(totals[ym], 2)} for ym in sorted(totals.keys())]


def get_fund_history(
    db: Session,
    client_id: int,
    fund_number: str,
) -> List[Dict[str, Optional[float]]]:
    snapshots = (
        db.query(Snapshot)
        .filter(
            Snapshot.client_id == client_id,
            Snapshot.fund_number == fund_number,
            Snapshot.is_active.is_(True),
        )
        .order_by(Snapshot.snapshot_date)
        .all()
    )

    history: List[Dict[str, Optional[float]]] = []
    prev_amount: Optional[float] = None
    for s in snapshots:
        amount = _coerce_amount(s.amount)
        change: Optional[float]
        if prev_amount is None:
            change = None
        else:
            change = amount - prev_amount

        history.append(
            {
                "date": s.snapshot_date,
                "amount": amount,
                "source": s.source or "",
                "change": change,
            }
        )
        prev_amount = amount

    return history


def list_client_summaries(db: Session, month: Optional[str] = None) -> List[Dict[str, Any]]:
    clients = db.query(Client).order_by(Client.full_name).all()
    if not clients:
        return []

    snapshots = db.query(Snapshot).filter(Snapshot.is_active.is_(True)).all()
    if not snapshots:
        return [_empty_client_summary_row(c) for c in clients]

    months = sorted({m for m in (_extract_month(s.snapshot_date) for s in snapshots) if m})
    if not months:
        return [_empty_client_summary_row(c) for c in clients]

    target_month = month or months[-1]

    per_client: Dict[int, Dict[str, Any]] = {c.id: _init_client_summary_bucket(c) for c in clients}

    for s in snapshots:
        ym = _extract_month(s.snapshot_date)
        if ym != target_month:
            continue
        if s.client_id not in per_client:
            continue

        bucket = per_client[s.client_id]
        amount = _coerce_amount(s.amount)
        bucket["total_amount"] += amount
        if s.source:
            bucket["sources"].add(s.source)
        if s.fund_number:
            bucket["fund_numbers"].add(s.fund_number)

        if s.snapshot_date:
            current = bucket["last_update"]
            if current is None or s.snapshot_date > current:
                bucket["last_update"] = s.snapshot_date

    results: List[Dict[str, Any]] = []
    for client in clients:
        data = per_client.get(client.id)
        if not data:
            continue
        sources_list = sorted(data["sources"]) if isinstance(data["sources"], set) else list(data["sources"])
        fund_numbers = data["fund_numbers"] if isinstance(data["fund_numbers"], set) else set(data["fund_numbers"])
        results.append(
            {
                "id": data["id"],
                "full_name": data["full_name"],
                "id_number": data["id_number"],
                "total_amount": round(data["total_amount"], 2),
                "sources_display": ", ".join(sources_list) if sources_list else "אין נתונים",
                "raw_sources": ",".join(sources_list) if sources_list else "אין נתונים",
                "fund_count": len(fund_numbers),
                "last_update": data["last_update"],
            }
        )

    return results
