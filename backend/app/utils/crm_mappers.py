from datetime import date
from typing import Any, Dict, List, Optional

from app.models import Client, ClientNote, Snapshot
from app.schemas.crm import (
    ClientRead,
    ClientBeneficiaryRead,
    ClientSummaryItem,
    FundHistoryPoint,
    HistoryPoint,
    MonthlyChangePoint,
    NoteRead,
    ReminderRead,
    SnapshotRead,
    SummaryResponse,
)


def _iso_or_none(value: Optional[date]) -> Optional[str]:
    if not value:
        return None
    try:
        return value.isoformat()
    except Exception:
        return None


def to_client_read(client: Client) -> ClientRead:
    beneficiaries: List[ClientBeneficiaryRead] = []
    for b in sorted(getattr(client, "beneficiaries", []) or [], key=lambda x: x.index or 0):
        beneficiaries.append(
            ClientBeneficiaryRead(
                id=b.id,
                index=b.index,
                firstName=b.first_name or "",
                lastName=b.last_name or "",
                idNumber=b.id_number or "",
                birthDate=_iso_or_none(b.birth_date) or "",
                address=b.address or "",
                relation=b.relation or "",
                percentage=float(b.percentage or 0.0),
            )
        )

    return ClientRead(
        id=client.id,
        idNumber=client.id_number,
        fullName=client.full_name,
        firstName=client.first_name,
        lastName=client.last_name,
        email=client.email,
        phone=client.phone,
        addressStreet=client.address_street,
        addressCity=client.address_city,
        addressPostalCode=client.address_postal_code,
        addressHouseNumber=client.address_house_number,
        addressApartment=client.address_apartment,
        birthDate=_iso_or_none(client.birth_date),
        gender=client.gender,
        maritalStatus=client.marital_status,
        birthCountry=client.birth_country,
        employerName=client.employer_name,
        employerHp=client.employer_hp,
        employerAddress=client.employer_address,
        employerPhone=client.employer_phone,
        beneficiaries=beneficiaries,
    )


def to_snapshot_read(snapshot: Snapshot) -> SnapshotRead:
    return SnapshotRead(
        id=snapshot.id,
        clientId=snapshot.client_id,
        fundCode=snapshot.fund_code,
        fundType=snapshot.fund_type,
        fundName=snapshot.fund_name,
        fundNumber=snapshot.fund_number,
        amount=snapshot.amount,
        snapshotDate=snapshot.snapshot_date,
    )


def to_summary_response(
    month: Optional[str],
    total_assets: float,
    by_source: Dict[str, float],
    by_fund_type: Dict[str, float],
) -> SummaryResponse:
    return SummaryResponse(
        month=month,
        totalAssets=total_assets,
        bySource=by_source,
        byFundType=by_fund_type,
    )


def to_monthly_change_point(row: Dict[str, Any]) -> MonthlyChangePoint:
    return MonthlyChangePoint(
        month=row["month"],
        total=row["total"],
        change=row.get("change"),
        percentChange=row.get("percent_change"),
    )


def to_history_points(rows: List[Dict[str, Any]]) -> List[HistoryPoint]:
    return [HistoryPoint(month=row["month"], amount=row["amount"]) for row in rows]


def to_fund_history_point(row: Dict[str, Any]) -> FundHistoryPoint:
    return FundHistoryPoint(
        date=row["date"],
        amount=row["amount"],
        source=row["source"],
        change=row.get("change"),
    )


def to_client_summary_item(row: Dict[str, Any]) -> ClientSummaryItem:
    return ClientSummaryItem(
        id=row["id"],
        fullName=row["full_name"],
        idNumber=row["id_number"],
        totalAmount=row["total_amount"],
        sources=row["sources_display"],
        rawSources=row["raw_sources"],
        fundCount=row["fund_count"],
        lastUpdate=row["last_update"],
    )


def to_note_read(note: ClientNote) -> NoteRead:
    return NoteRead(
        id=note.id,
        note=note.note or "",
        createdAt=note.created_at,
        reminderAt=note.reminder_at,
        dismissedAt=note.dismissed_at,
    )


def to_reminder_read(row: Dict[str, Any]) -> ReminderRead:
    return ReminderRead(
        id=row["id"],
        note=row["note"],
        createdAt=row["created_at"],
        reminderAt=row["reminder_at"],
        dismissedAt=row["dismissed_at"],
        clientId=row["client_id"],
        clientName=row["client_name"],
    )
