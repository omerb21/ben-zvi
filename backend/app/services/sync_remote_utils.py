from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session


def _coerce_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value) if value is not None else default
    except Exception:
        return default


def _list_rows_for_client(db: Session, model: Any, client_id: int):
    return db.query(model).filter(model.client_id == client_id).all()
