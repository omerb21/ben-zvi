from datetime import date, datetime
from typing import Optional, List, Dict, Any
import hashlib
import hmac
import secrets
import string

from sqlalchemy.orm import Session

from app.models import Client, Snapshot, ClientNote, ClientBeneficiary
from app.schemas.crm import ClientCreate, SnapshotCreate, ClientUpdate
from app.utils.id_normalization import normalize_id_number
from app.utils.db import commit_and_refresh as _commit_and_refresh
from app.utils.strings import strip_or_empty as _strip_or_empty
from app.services.crm_snapshots import get_snapshot_summary as _get_snapshot_summary_impl
from app.services.crm_snapshots import get_monthly_change as _get_monthly_change_impl
from app.services.crm_snapshots import get_history as _get_history_impl
from app.services.crm_snapshots import get_fund_history as _get_fund_history_impl
from app.services.crm_snapshots import list_client_summaries as _list_client_summaries_impl

from app.services import crm_beneficiaries as _crm_beneficiaries
from app.services import crm_clients as _crm_clients
from app.services import crm_credentials as _crm_credentials
from app.services import crm_notes as _crm_notes
from app.services import crm_utils as _crm_utils

def _parse_iso_date(value: Optional[str]) -> Optional[date]:
    return _crm_utils._parse_iso_date(value)


def _utc_timestamp_str() -> str:
    return _crm_utils._utc_timestamp_str()


def _build_beneficiary_fields(item) -> tuple[str, str, str, str, str, str, float]:
    return _crm_beneficiaries._build_beneficiary_fields(item)


def _is_beneficiary_all_empty(
    first_name: str,
    last_name: str,
    id_number: str,
    birth_date_text: str,
    address: str,
    relation: str,
    percentage_value: float,
) -> bool:
    return _crm_beneficiaries._is_beneficiary_all_empty(
        first_name,
        last_name,
        id_number,
        birth_date_text,
        address,
        relation,
        percentage_value,
    )


def _apply_beneficiary_values(
    row: ClientBeneficiary,
    *,
    first_name: str,
    last_name: str,
    id_number: str,
    birth_date_value: date,
    address: str,
    relation: str,
    percentage_value: float,
) -> None:
    _crm_beneficiaries._apply_beneficiary_values(
        row,
        first_name=first_name,
        last_name=last_name,
        id_number=id_number,
        birth_date_value=birth_date_value,
        address=address,
        relation=relation,
        percentage_value=percentage_value,
    )


def _empty_client_summary_row(client: Client) -> Dict[str, Any]:
    return _crm_clients._empty_client_summary_row(client)


def _init_client_summary_bucket(client: Client) -> Dict[str, Any]:
    return _crm_clients._init_client_summary_bucket(client)


def _sync_client_beneficiaries(db: Session, client: Client, beneficiaries) -> None:
    _crm_beneficiaries._sync_client_beneficiaries(db, client, beneficiaries)


def list_clients(db: Session) -> List[Client]:
    """Return all clients ordered by ID."""
    return _crm_clients.list_clients(db)


def get_client(db: Session, client_id: int) -> Optional[Client]:
    """Return a single client by ID or None if not found."""
    return _crm_clients.get_client(db, client_id)


def get_client_by_token(db: Session, token: str) -> Optional[Client]:
    """Return a single client by client_token for external client apps.

    If the token is empty or no active client is associated with it, return None.
    """
    return _crm_clients.get_client_by_token(db, token)


def create_client(db: Session, client_in: ClientCreate) -> Client:
    """Create a new client from CRM input schema."""
    return _crm_clients.create_client(db, client_in)


def delete_client(db: Session, client_id: int) -> bool:
    """Delete a client and all its CRM-related data.

    Returns True if a client was deleted, False if it did not exist.
    """
    return _crm_clients.delete_client(db, client_id)


def clear_crm_data(db: Session) -> dict[str, int]:
    """Clear CRM-specific data (snapshots and client notes) without deleting clients.

    Returns a dict with counts of deleted rows for visibility in admin UI.
    """
    return _crm_clients.clear_crm_data(db)


def list_client_snapshots(db: Session, client_id: int) -> List[Snapshot]:
    """Return all snapshots for a given client ordered by snapshot date (descending)."""
    return _crm_clients.list_client_snapshots(db, client_id)


def create_snapshot_for_client(db: Session, client: Client, snapshot_in: SnapshotCreate) -> Snapshot:
    """Create a new product snapshot for the given client."""
    return _crm_clients.create_snapshot_for_client(db, client, snapshot_in)


def get_snapshot_summary(
    db: Session,
    month: Optional[str] = None,
) -> tuple[Optional[str], float, Dict[str, float], Dict[str, float]]:
    """Compute total assets and breakdowns for a given month.

    If month is None, use the latest month present in snapshot_date (YYYY-MM).
    """
    return _get_snapshot_summary_impl(db, month)


def get_monthly_change(db: Session) -> List[Dict[str, Optional[float]]]:
    """Compute month-over-month changes in total assets across all clients."""
    return _get_monthly_change_impl(db)


def get_history(db: Session, client_id: Optional[int]) -> List[Dict[str, float]]:
    """Return monthly history for a specific client or for all clients (if client_id == 0)."""
    return _get_history_impl(db, client_id)


def get_fund_history(
    db: Session,
    client_id: int,
    fund_number: str,
) -> List[Dict[str, Optional[float]]]:
    """Return time series for a specific fund of a client."""
    return _get_fund_history_impl(db, client_id, fund_number)


def list_client_summaries(db: Session, month: Optional[str] = None) -> List[Dict[str, Any]]:
    """Summaries per client for a given month (or latest month if not provided)."""
    return _list_client_summaries_impl(db, month)


_CLIENT_UPDATE_ATTR_MAP: Dict[str, str] = _crm_clients._CLIENT_UPDATE_ATTR_MAP


def _apply_client_update_fields(client: Client, update: ClientUpdate) -> None:
    _crm_clients._apply_client_update_fields(client, update)


def list_client_notes(db: Session, client_id: int) -> List[ClientNote]:
    return _crm_notes.list_client_notes(db, client_id)


def create_client_note(
    db: Session,
    client_id: int,
    note_text: str,
    reminder_at: Optional[str],
) -> ClientNote:
    return _crm_notes.create_client_note(db, client_id, note_text, reminder_at)


def _get_client_note(db: Session, client_id: int, note_id: int) -> Optional[ClientNote]:
    return _crm_notes._get_client_note(db, client_id, note_id)


def dismiss_client_note(db: Session, client_id: int, note_id: int) -> Optional[ClientNote]:
    return _crm_notes.dismiss_client_note(db, client_id, note_id)


def clear_note_reminder(db: Session, client_id: int, note_id: int) -> Optional[ClientNote]:
    return _crm_notes.clear_note_reminder(db, client_id, note_id)


def delete_client_note(db: Session, client_id: int, note_id: int) -> bool:
    return _crm_notes.delete_client_note(db, client_id, note_id)


def list_global_reminders(db: Session, today: Optional[date] = None) -> List[Dict[str, Any]]:
    """Return all reminders due up to today across all clients."""
    return _crm_notes.list_global_reminders(db, today=today)


def _update_client_or_none(db: Session, client_id: int, apply_fn) -> Optional[Client]:
    return _crm_credentials._update_client_or_none(db, client_id, apply_fn)


def set_client_token(db: Session, client_id: int, token: Optional[str]) -> Optional[Client]:
    return _crm_credentials.set_client_token(db, client_id, token)


def _hash_pin(pin: str) -> str:
    return _crm_credentials._hash_pin(pin)


def _pin_hash_or_none(pin: Optional[str]) -> Optional[str]:
    return _crm_credentials._pin_hash_or_none(pin)


def set_client_pin(db: Session, client_id: int, pin: Optional[str]) -> Optional[Client]:
    return _crm_credentials.set_client_pin(db, client_id, pin)


def check_client_pin(client: Client, pin: Optional[str]) -> bool:
    return _crm_credentials.check_client_pin(client, pin)


def reset_client_credentials(
    db: Session,
    client_id: int,
) -> tuple[Optional[Client], Optional[str], Optional[str]]:
    """Generate and assign a new external token and PIN for a client.

    Returns a tuple of (client, token, pin). If the client does not exist, all
    values will be None.
    """
    return _crm_credentials.reset_client_credentials(db, client_id)


def disable_client_access(db: Session, client_id: int) -> Optional[Client]:
    """Disable external client app access by clearing token and PIN for a client.

    After this operation there is no valid client_token for external lookup and no
    PIN hash stored for the client.
    """
    return _crm_credentials.disable_client_access(db, client_id)


def update_client(db: Session, client_id: int, update: ClientUpdate) -> Optional[Client]:
    return _crm_clients.update_client(db, client_id, update)
