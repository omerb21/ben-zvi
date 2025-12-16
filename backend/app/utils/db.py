from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session


def commit_and_refresh(db: Session, obj: Any) -> None:
    db.commit()
    db.refresh(obj)
