from datetime import date
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from app.models import Client, ClientNote
from app.services.crm_utils import _utc_timestamp_str
from app.utils.db import commit_and_refresh as _commit_and_refresh


def list_client_notes(db: Session, client_id: int) -> List[ClientNote]:
    return (
        db.query(ClientNote)
        .filter(ClientNote.client_id == client_id)
        .order_by(ClientNote.created_at.desc(), ClientNote.id.desc())
        .all()
    )


def create_client_note(
    db: Session,
    client_id: int,
    note_text: str,
    reminder_at: Optional[str],
) -> ClientNote:
    created_at = _utc_timestamp_str()
    note = ClientNote(
        client_id=client_id,
        note=note_text,
        created_at=created_at,
        reminder_at=reminder_at,
        dismissed_at=None,
    )
    db.add(note)
    _commit_and_refresh(db, note)
    return note


def _get_client_note(db: Session, client_id: int, note_id: int) -> Optional[ClientNote]:
    return (
        db.query(ClientNote)
        .filter(ClientNote.id == note_id, ClientNote.client_id == client_id)
        .first()
    )


def dismiss_client_note(db: Session, client_id: int, note_id: int) -> Optional[ClientNote]:
    note = _get_client_note(db, client_id, note_id)
    if not note:
        return None
    note.dismissed_at = _utc_timestamp_str()
    _commit_and_refresh(db, note)
    return note


def clear_note_reminder(db: Session, client_id: int, note_id: int) -> Optional[ClientNote]:
    note = _get_client_note(db, client_id, note_id)
    if not note:
        return None
    note.reminder_at = None
    note.dismissed_at = None
    _commit_and_refresh(db, note)
    return note


def delete_client_note(db: Session, client_id: int, note_id: int) -> bool:
    note = _get_client_note(db, client_id, note_id)
    if not note:
        return False
    db.delete(note)
    db.commit()
    return True


def list_global_reminders(db: Session, today: Optional[date] = None) -> List[Dict[str, Any]]:
    if today is None:
        today = date.today()
    today_str = today.isoformat()

    rows = (
        db.query(ClientNote, Client)
        .join(Client, ClientNote.client_id == Client.id)
        .all()
    )

    results: List[Dict[str, Any]] = []
    for note, client in rows:
        if not note.reminder_at:
            continue
        if note.dismissed_at not in (None, ""):
            continue
        if note.reminder_at > today_str:
            continue

        results.append(
            {
                "id": note.id,
                "note": note.note or "",
                "created_at": note.created_at,
                "reminder_at": note.reminder_at,
                "dismissed_at": note.dismissed_at,
                "client_id": client.id,
                "client_name": client.full_name or "",
            }
        )

    return results
