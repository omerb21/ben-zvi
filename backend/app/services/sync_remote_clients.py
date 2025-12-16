from __future__ import annotations

from typing import Any, Dict, List

from sqlalchemy.orm import Session

from app.models import Client
from app.schemas.crm import ClientBeneficiaryUpdate, ClientCreate, ClientUpdate
from app.services import crm as crm_service


def _build_client_create(remote_client: Dict[str, Any]) -> ClientCreate:
    return ClientCreate(
        idNumber=remote_client.get("idNumber"),
        fullName=remote_client.get("fullName"),
        firstName=remote_client.get("firstName"),
        lastName=remote_client.get("lastName"),
        email=remote_client.get("email"),
        phone=remote_client.get("phone"),
        addressStreet=remote_client.get("addressStreet"),
        addressCity=remote_client.get("addressCity"),
        addressPostalCode=remote_client.get("addressPostalCode"),
        birthDate=remote_client.get("birthDate"),
        gender=remote_client.get("gender"),
        maritalStatus=remote_client.get("maritalStatus"),
        birthCountry=remote_client.get("birthCountry"),
        employerName=remote_client.get("employerName"),
        employerHp=remote_client.get("employerHp"),
        employerAddress=remote_client.get("employerAddress"),
        employerPhone=remote_client.get("employerPhone"),
        addressHouseNumber=remote_client.get("addressHouseNumber"),
        addressApartment=remote_client.get("addressApartment"),
    )


def _to_beneficiary_update_or_none(raw: Any) -> ClientBeneficiaryUpdate | None:
    try:
        return ClientBeneficiaryUpdate(
            index=raw.get("index"),
            firstName=raw.get("firstName") or "",
            lastName=raw.get("lastName") or "",
            idNumber=raw.get("idNumber") or "",
            birthDate=raw.get("birthDate") or "",
            address=raw.get("address") or "",
            relation=raw.get("relation") or "",
            percentage=raw.get("percentage") or 0.0,
        )
    except Exception:
        return None


def _build_client_update(remote_client: Dict[str, Any]) -> ClientUpdate:
    raw_beneficiaries = remote_client.get("beneficiaries") or []
    beneficiaries: List[ClientBeneficiaryUpdate] = []
    for b in raw_beneficiaries:
        item = _to_beneficiary_update_or_none(b)
        if item is not None:
            beneficiaries.append(item)

    return ClientUpdate(
        firstName=remote_client.get("firstName"),
        lastName=remote_client.get("lastName"),
        email=remote_client.get("email"),
        phone=remote_client.get("phone"),
        addressStreet=remote_client.get("addressStreet"),
        addressCity=remote_client.get("addressCity"),
        addressPostalCode=remote_client.get("addressPostalCode"),
        birthDate=remote_client.get("birthDate"),
        gender=remote_client.get("gender"),
        maritalStatus=remote_client.get("maritalStatus"),
        birthCountry=remote_client.get("birthCountry"),
        employerName=remote_client.get("employerName"),
        employerHp=remote_client.get("employerHp"),
        employerAddress=remote_client.get("employerAddress"),
        employerPhone=remote_client.get("employerPhone"),
        addressHouseNumber=remote_client.get("addressHouseNumber"),
        addressApartment=remote_client.get("addressApartment"),
        beneficiaries=beneficiaries or None,
    )


def _get_or_create_local_client(db: Session, remote_client: Dict[str, Any]) -> Client:
    id_number = remote_client.get("idNumber")
    local_client: Client | None = None
    if id_number:
        local_client = db.query(Client).filter(Client.id_number == id_number).first()

    if local_client is None:
        create_payload = _build_client_create(remote_client)
        local_client = crm_service.create_client(db, create_payload)

    update_payload = _build_client_update(remote_client)
    updated = crm_service.update_client(db, local_client.id, update_payload)
    return updated or local_client
