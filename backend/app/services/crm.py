from collections import defaultdict
from datetime import date, datetime
from typing import Optional, List, Dict, Any

from sqlalchemy.orm import Session

from app.models import Client, Snapshot, ClientNote
from app.schemas.crm import ClientCreate, SnapshotCreate, ClientUpdate
from app.utils.id_normalization import normalize_id_number


def list_clients(db: Session) -> List[Client]:
    """Return all clients ordered by ID."""
    return db.query(Client).order_by(Client.id).all()


def get_client(db: Session, client_id: int) -> Optional[Client]:
    """Return a single client by ID or None if not found."""
    return db.query(Client).filter(Client.id == client_id).first()


def create_client(db: Session, client_in: ClientCreate) -> Client:
    """Create a new client from CRM input schema."""
    id_number_raw = client_in.idNumber
    id_number = normalize_id_number(id_number_raw) or (id_number_raw or "")

    birth_date_value: Optional[date] = None
    if client_in.birthDate:
        try:
            birth_date_value = datetime.fromisoformat(client_in.birthDate).date()
        except ValueError:
            birth_date_value = None

    client = Client(
        id_number_raw=id_number_raw,
        id_number=id_number,
        full_name=client_in.fullName,
        first_name=client_in.firstName,
        last_name=client_in.lastName,
        email=client_in.email,
        phone=client_in.phone,
        address_street=client_in.addressStreet,
        address_city=client_in.addressCity,
        address_postal_code=client_in.addressPostalCode,
        address_house_number=client_in.addressHouseNumber,
        address_apartment=client_in.addressApartment,
        birth_date=birth_date_value,
        gender=client_in.gender,
        marital_status=client_in.maritalStatus,
        birth_country=client_in.birthCountry,
        employer_name=client_in.employerName,
        employer_hp=client_in.employerHp,
        employer_address=client_in.employerAddress,
        employer_phone=client_in.employerPhone,
    )
    db.add(client)
    db.commit()
    db.refresh(client)
    return client


def delete_client(db: Session, client_id: int) -> bool:
    """Delete a client and all its CRM-related data.

    Returns True if a client was deleted, False if it did not exist.
    """
    client = get_client(db, client_id)
    if not client:
        return False

    db.delete(client)
    db.commit()
    return True


def clear_crm_data(db: Session) -> dict[str, int]:
    """Clear CRM-specific data (snapshots and client notes) without deleting clients.

    Returns a dict with counts of deleted rows for visibility in admin UI.
    """

    deleted_snapshots = db.query(Snapshot).delete()
    deleted_client_notes = db.query(ClientNote).delete()
    db.commit()

    return {
        "deletedSnapshots": deleted_snapshots,
        "deletedClientNotes": deleted_client_notes,
    }


def list_client_snapshots(db: Session, client_id: int) -> List[Snapshot]:
    """Return all snapshots for a given client ordered by snapshot date (descending)."""
    return (
        db.query(Snapshot)
        .filter(Snapshot.client_id == client_id)
        .order_by(Snapshot.snapshot_date.desc())
        .all()
    )


def create_snapshot_for_client(db: Session, client: Client, snapshot_in: SnapshotCreate) -> Snapshot:
    """Create a new product snapshot for the given client."""
    snapshot = Snapshot(
        client_id=client.id,
        fund_code=snapshot_in.fundCode,
        fund_type=snapshot_in.fundType,
        fund_name=snapshot_in.fundName,
        fund_number=snapshot_in.fundNumber,
        source=snapshot_in.source,
        amount=snapshot_in.amount,
        snapshot_date=snapshot_in.snapshotDate,
        is_active=snapshot_in.isActive,
    )
    db.add(snapshot)
    db.commit()
    db.refresh(snapshot)
    return snapshot


def _extract_month(value: Optional[str]) -> Optional[str]:
    if not value or len(value) < 7:
        return None
    return value[:7]


def get_snapshot_summary(
    db: Session,
    month: Optional[str] = None,
) -> tuple[Optional[str], float, Dict[str, float], Dict[str, float]]:
    """Compute total assets and breakdowns for a given month.

    If month is None, use the latest month present in snapshot_date (YYYY-MM).
    """
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
        amount = float(s.amount or 0.0)
        total += amount

        src = s.source or "לא ידוע"
        by_source[src] += amount

        ftype = s.fund_type or "לא זמין"
        by_type[ftype] += amount

    return target_month, round(total, 2), dict(by_source), dict(by_type)


def get_monthly_change(db: Session) -> List[Dict[str, Optional[float]]]:
    """Compute month-over-month changes in total assets across all clients."""
    snapshots = db.query(Snapshot).filter(Snapshot.is_active.is_(True)).all()
    if not snapshots:
        return []

    totals: Dict[str, float] = defaultdict(float)
    for s in snapshots:
        ym = _extract_month(s.snapshot_date)
        if not ym:
            continue
        totals[ym] += float(s.amount or 0.0)

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
    """Return monthly history for a specific client or for all clients (if client_id == 0)."""
    query = db.query(Snapshot).filter(Snapshot.is_active.is_(True))
    if client_id and client_id != 0:
        query = query.filter(Snapshot.client_id == client_id)

    snapshots = query.all()
    if not snapshots:
        return []

    totals: Dict[str, float] = defaultdict(float)
    for s in snapshots:
        ym = _extract_month(s.snapshot_date)
        if not ym:
            continue
        totals[ym] += float(s.amount or 0.0)

    return [
        {"month": ym, "amount": round(totals[ym], 2)}
        for ym in sorted(totals.keys())
    ]


def get_fund_history(
    db: Session,
    client_id: int,
    fund_number: str,
) -> List[Dict[str, Optional[float]]]:
    """Return time series for a specific fund of a client."""
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
        amount = float(s.amount or 0.0)
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
    """Summaries per client for a given month (or latest month if not provided)."""
    clients = db.query(Client).order_by(Client.full_name).all()
    if not clients:
        return []

    snapshots = db.query(Snapshot).filter(Snapshot.is_active.is_(True)).all()
    if not snapshots:
        return [
            {
                "id": c.id,
                "full_name": c.full_name,
                "id_number": c.id_number,
                "total_amount": 0.0,
                "sources": [],
                "fund_numbers": set(),
                "last_update": None,
            }
            for c in clients
        ]

    months = sorted({m for m in (_extract_month(s.snapshot_date) for s in snapshots) if m})
    if not months:
        return [
            {
                "id": c.id,
                "full_name": c.full_name,
                "id_number": c.id_number,
                "total_amount": 0.0,
                "sources": [],
                "fund_numbers": set(),
                "last_update": None,
            }
            for c in clients
        ]

    target_month = month or months[-1]

    per_client: Dict[int, Dict[str, Any]] = {
        c.id: {
            "id": c.id,
            "full_name": c.full_name,
            "id_number": c.id_number,
            "total_amount": 0.0,
            "sources": set(),
            "fund_numbers": set(),
            "last_update": None,
        }
        for c in clients
    }

    for s in snapshots:
        ym = _extract_month(s.snapshot_date)
        if ym != target_month:
            continue
        if s.client_id not in per_client:
            continue

        bucket = per_client[s.client_id]
        amount = float(s.amount or 0.0)
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
    created_at = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    note = ClientNote(
        client_id=client_id,
        note=note_text,
        created_at=created_at,
        reminder_at=reminder_at,
        dismissed_at=None,
    )
    db.add(note)
    db.commit()
    db.refresh(note)
    return note


def dismiss_client_note(db: Session, client_id: int, note_id: int) -> Optional[ClientNote]:
    note = (
        db.query(ClientNote)
        .filter(ClientNote.id == note_id, ClientNote.client_id == client_id)
        .first()
    )
    if not note:
        return None
    note.dismissed_at = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    db.commit()
    db.refresh(note)
    return note


def clear_note_reminder(db: Session, client_id: int, note_id: int) -> Optional[ClientNote]:
    note = (
        db.query(ClientNote)
        .filter(ClientNote.id == note_id, ClientNote.client_id == client_id)
        .first()
    )
    if not note:
        return None
    note.reminder_at = None
    note.dismissed_at = None
    db.commit()
    db.refresh(note)
    return note


def delete_client_note(db: Session, client_id: int, note_id: int) -> bool:
    note = (
        db.query(ClientNote)
        .filter(ClientNote.id == note_id, ClientNote.client_id == client_id)
        .first()
    )
    if not note:
        return False
    db.delete(note)
    db.commit()
    return True


def list_global_reminders(db: Session, today: Optional[date] = None) -> List[Dict[str, Any]]:
    """Return all reminders due up to today across all clients."""
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


def update_client(db: Session, client_id: int, update: ClientUpdate) -> Optional[Client]:
    client = get_client(db, client_id)
    if not client:
        return None

    if update.firstName is not None:
        client.first_name = update.firstName
    if update.lastName is not None:
        client.last_name = update.lastName
    if update.email is not None:
        client.email = update.email
    if update.phone is not None:
        client.phone = update.phone
    if update.addressStreet is not None:
        client.address_street = update.addressStreet
    if update.addressCity is not None:
        client.address_city = update.addressCity
    if update.addressPostalCode is not None:
        client.address_postal_code = update.addressPostalCode
    if update.addressHouseNumber is not None:
        client.address_house_number = update.addressHouseNumber
    if update.addressApartment is not None:
        client.address_apartment = update.addressApartment

    if update.birthDate is not None:
        if update.birthDate == "":
            client.birth_date = date(1970, 1, 1)
        else:
            try:
                client.birth_date = datetime.fromisoformat(update.birthDate).date()
            except ValueError:
                pass
    if update.gender is not None:
        client.gender = update.gender
    if update.maritalStatus is not None:
        client.marital_status = update.maritalStatus
    if update.birthCountry is not None:
        client.birth_country = update.birthCountry
    if update.employerName is not None:
        client.employer_name = update.employerName
    if update.employerHp is not None:
        client.employer_hp = update.employerHp
    if update.employerAddress is not None:
        client.employer_address = update.employerAddress
    if update.employerPhone is not None:
        client.employer_phone = update.employerPhone

    if update.firstName or update.lastName:
        parts = [p for p in [client.first_name, client.last_name] if p]
        if parts:
            client.full_name = " ".join(parts)

    db.commit()
    db.refresh(client)
    return client
