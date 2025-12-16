from datetime import date
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from app.models import Client, ClientNote, Snapshot
from app.schemas.crm import ClientCreate, ClientUpdate, SnapshotCreate
from app.services import crm_beneficiaries as _beneficiaries
from app.services.crm_utils import _parse_iso_date
from app.utils.db import commit_and_refresh as _commit_and_refresh
from app.utils.id_normalization import normalize_id_number


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


def list_clients(db: Session) -> List[Client]:
    return db.query(Client).order_by(Client.id).all()


def get_client(db: Session, client_id: int) -> Optional[Client]:
    return db.query(Client).filter(Client.id == client_id).first()


def get_client_by_token(db: Session, token: str) -> Optional[Client]:
    if not token:
        return None

    return db.query(Client).filter(Client.client_token == token).first()


def create_client(db: Session, client_in: ClientCreate) -> Client:
    id_number_raw = client_in.idNumber
    id_number = normalize_id_number(id_number_raw) or (id_number_raw or "")

    birth_date_value = _parse_iso_date(client_in.birthDate)

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
    _commit_and_refresh(db, client)
    return client


def delete_client(db: Session, client_id: int) -> bool:
    client = get_client(db, client_id)
    if not client:
        return False

    db.delete(client)
    db.commit()
    return True


def clear_crm_data(db: Session) -> dict[str, int]:
    deleted_snapshots = db.query(Snapshot).delete()
    deleted_client_notes = db.query(ClientNote).delete()
    db.commit()

    return {
        "deletedSnapshots": deleted_snapshots,
        "deletedClientNotes": deleted_client_notes,
    }


def list_client_snapshots(db: Session, client_id: int) -> List[Snapshot]:
    return (
        db.query(Snapshot)
        .filter(Snapshot.client_id == client_id)
        .order_by(Snapshot.snapshot_date.desc())
        .all()
    )


def create_snapshot_for_client(db: Session, client: Client, snapshot_in: SnapshotCreate) -> Snapshot:
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
    _commit_and_refresh(db, snapshot)
    return snapshot


_CLIENT_UPDATE_ATTR_MAP: Dict[str, str] = {
    "firstName": "first_name",
    "lastName": "last_name",
    "email": "email",
    "phone": "phone",
    "addressStreet": "address_street",
    "addressCity": "address_city",
    "addressPostalCode": "address_postal_code",
    "addressHouseNumber": "address_house_number",
    "addressApartment": "address_apartment",
    "gender": "gender",
    "maritalStatus": "marital_status",
    "birthCountry": "birth_country",
    "employerName": "employer_name",
    "employerHp": "employer_hp",
    "employerAddress": "employer_address",
    "employerPhone": "employer_phone",
}


def _apply_client_update_fields(client: Client, update: ClientUpdate) -> None:
    for schema_attr, model_attr in _CLIENT_UPDATE_ATTR_MAP.items():
        value = getattr(update, schema_attr, None)
        if value is not None:
            setattr(client, model_attr, value)

    if update.birthDate is not None:
        if update.birthDate == "":
            client.birth_date = date(1970, 1, 1)
        else:
            birth_date_value = _parse_iso_date(update.birthDate)
            if birth_date_value is not None:
                client.birth_date = birth_date_value


def update_client(db: Session, client_id: int, update: ClientUpdate) -> Optional[Client]:
    client = get_client(db, client_id)
    if not client:
        return None

    _apply_client_update_fields(client, update)

    if update.firstName or update.lastName:
        parts = [p for p in [client.first_name, client.last_name] if p]
        if parts:
            client.full_name = " ".join(parts)

    if update.beneficiaries is not None:
        _beneficiaries._sync_client_beneficiaries(db, client, update.beneficiaries)

    _commit_and_refresh(db, client)
    return client
