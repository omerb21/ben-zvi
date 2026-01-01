import hashlib
import hmac
import secrets
import string
from typing import Optional

from sqlalchemy.orm import Session

from app.models import Client
from app.utils.db import commit_and_refresh as _commit_and_refresh
from app.utils.strings import strip_or_empty as _strip_or_empty


def _get_client(db: Session, client_id: int) -> Optional[Client]:
    return db.query(Client).filter(Client.id == client_id).first()


def _update_client_or_none(db: Session, client_id: int, apply_fn) -> Optional[Client]:
    client = _get_client(db, client_id)
    if not client:
        return None
    apply_fn(client)
    _commit_and_refresh(db, client)
    return client


def set_client_token(db: Session, client_id: int, token: Optional[str]) -> Optional[Client]:
    def _apply(client: Client) -> None:
        client.client_token = token or None

    return _update_client_or_none(db, client_id, _apply)


def _hash_pin(pin: str) -> str:
    normalized = _strip_or_empty(pin)
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def _pin_hash_or_none(pin: Optional[str]) -> Optional[str]:
    if pin is None:
        return None
    normalized = _strip_or_empty(pin)
    if not normalized:
        return None
    return _hash_pin(normalized)


def set_client_pin(db: Session, client_id: int, pin: Optional[str]) -> Optional[Client]:
    def _apply(client: Client) -> None:
        client.client_pin_hash = _pin_hash_or_none(pin)

    return _update_client_or_none(db, client_id, _apply)


def check_client_pin(client: Client, pin: Optional[str]) -> bool:
    if not client.client_pin_hash:
        return True
    if pin is None:
        return True
    candidate_hash = _hash_pin(pin)
    if hmac.compare_digest(client.client_pin_hash, candidate_hash):
        return True

    normalized = _strip_or_empty(pin)
    if normalized.isdigit() and len(normalized) < 6:
        padded_hash = _hash_pin(normalized.zfill(6))
        return hmac.compare_digest(client.client_pin_hash, padded_hash)

    return False


def reset_client_credentials(
    db: Session,
    client_id: int,
) -> tuple[Optional[Client], Optional[str], Optional[str]]:
    client = _get_client(db, client_id)
    if not client:
        return None, None, None

    alphabet = string.ascii_uppercase + string.digits
    random_part = "".join(secrets.choice(alphabet) for _ in range(16))
    token = f"C{client.id}-{random_part}"

    pin_value = f"{secrets.randbelow(1_000_000):06d}"

    updated_client = set_client_token(db, client_id, token)
    if not updated_client:
        return None, None, None

    updated_client = set_client_pin(db, client_id, pin_value)
    if not updated_client:
        return None, None, None

    return updated_client, token, pin_value


def disable_client_access(db: Session, client_id: int) -> Optional[Client]:
    client = set_client_token(db, client_id, None)
    if not client:
        return None

    client = set_client_pin(db, client_id, None)
    return client
