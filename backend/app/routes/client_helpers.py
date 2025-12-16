from __future__ import annotations

from sqlalchemy.orm import Session

from app.services import crm as crm_service
from app.utils.http_exceptions import raise_client_not_found


def get_client_or_404(db: Session, client_id: int):
    client = crm_service.get_client(db, client_id)
    if not client:
        raise_client_not_found()
    return client
