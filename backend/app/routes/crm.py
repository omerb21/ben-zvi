from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.crm import (
    ClientCreate,
    ClientRead,
    SnapshotCreate,
    SnapshotRead,
    SummaryResponse,
    MonthlyChangePoint,
    HistoryPoint,
    FundHistoryPoint,
    ClientSummaryItem,
    NoteCreate,
    NoteRead,
    ReminderRead,
    ClientUpdate,
)
from app.services import crm as crm_service
from app.services.client_report import (
    build_client_report_data,
    generate_client_report_pdf,
    render_client_report_html,
)


router = APIRouter(prefix="/api/v1/crm", tags=["crm"])


@router.get("/clients", response_model=List[ClientRead])
def list_clients(db: Session = Depends(get_db)):
    clients = crm_service.list_clients(db)
    return [
        ClientRead(
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
            birthDate=client.birth_date.isoformat() if client.birth_date else None,
            gender=client.gender,
            maritalStatus=client.marital_status,
            birthCountry=client.birth_country,
            employerName=client.employer_name,
            employerHp=client.employer_hp,
            employerAddress=client.employer_address,
            employerPhone=client.employer_phone,
        )
        for client in clients
    ]


@router.get("/clients/{client_id}", response_model=ClientRead)
def get_client(client_id: int, db: Session = Depends(get_db)):
    client = crm_service.get_client(db, client_id)
    if not client:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Client not found")
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
        birthDate=client.birth_date.isoformat() if client.birth_date else None,
        gender=client.gender,
        maritalStatus=client.marital_status,
        birthCountry=client.birth_country,
        employerName=client.employer_name,
        employerHp=client.employer_hp,
        employerAddress=client.employer_address,
        employerPhone=client.employer_phone,
    )


@router.post("/clients", response_model=ClientRead, status_code=status.HTTP_201_CREATED)
def create_client(client_in: ClientCreate, db: Session = Depends(get_db)):
    client = crm_service.create_client(db, client_in)
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
        birthDate=client.birth_date.isoformat() if client.birth_date else None,
        gender=client.gender,
        maritalStatus=client.marital_status,
        birthCountry=client.birth_country,
        employerName=client.employer_name,
        employerHp=client.employer_hp,
        employerAddress=client.employer_address,
        employerPhone=client.employer_phone,
    )


@router.get(
    "/clients/{client_id}/snapshots",
    response_model=List[SnapshotRead],
)
def list_client_snapshots(client_id: int, db: Session = Depends(get_db)):
    client = crm_service.get_client(db, client_id)
    if not client:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Client not found")

    snapshots = crm_service.list_client_snapshots(db, client_id)
    return [
        SnapshotRead(
            id=snapshot.id,
            clientId=snapshot.client_id,
            fundCode=snapshot.fund_code,
            fundType=snapshot.fund_type,
            fundName=snapshot.fund_name,
            fundNumber=snapshot.fund_number,
            amount=snapshot.amount,
            snapshotDate=snapshot.snapshot_date,
        )
        for snapshot in snapshots
    ]


@router.post(
    "/clients/{client_id}/snapshots",
    response_model=SnapshotRead,
    status_code=status.HTTP_201_CREATED,
)
def create_client_snapshot(
    client_id: int,
    snapshot_in: SnapshotCreate,
    db: Session = Depends(get_db),
):
    client = crm_service.get_client(db, client_id)
    if not client:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Client not found")

    snapshot = crm_service.create_snapshot_for_client(db, client, snapshot_in)
    return SnapshotRead(
        id=snapshot.id,
        clientId=snapshot.client_id,
        fundCode=snapshot.fund_code,
        fundType=snapshot.fund_type,
        fundName=snapshot.fund_name,
        amount=snapshot.amount,
        snapshotDate=snapshot.snapshot_date,
    )


@router.get("/summary", response_model=SummaryResponse)
def get_summary(month: Optional[str] = None, db: Session = Depends(get_db)):
    target_month, total, by_source, by_type = crm_service.get_snapshot_summary(db, month)
    return SummaryResponse(
        month=target_month,
        totalAssets=total,
        bySource=by_source,
        byFundType=by_type,
    )


@router.get("/monthly-change", response_model=List[MonthlyChangePoint])
def get_monthly_change(db: Session = Depends(get_db)):
    points = crm_service.get_monthly_change(db)
    return [
        MonthlyChangePoint(
            month=p["month"],
            total=p["total"],
            change=p.get("change"),
            percentChange=p.get("percent_change"),
        )
        for p in points
    ]


@router.get("/history", response_model=List[HistoryPoint])
def get_history(client_id: Optional[int] = None, db: Session = Depends(get_db)):
    items = crm_service.get_history(db, client_id)
    return [HistoryPoint(month=i["month"], amount=i["amount"]) for i in items]


@router.get("/fund-history", response_model=List[FundHistoryPoint])
def get_fund_history(
    client_id: int,
    fund_number: str,
    db: Session = Depends(get_db),
):
    items = crm_service.get_fund_history(db, client_id, fund_number)
    return [
        FundHistoryPoint(
            date=i["date"],
            amount=i["amount"],
            source=i["source"],
            change=i.get("change"),
        )
        for i in items
    ]


@router.get("/clients-summary", response_model=List[ClientSummaryItem])
def list_client_summaries(month: Optional[str] = None, db: Session = Depends(get_db)):
    items = crm_service.list_client_summaries(db, month)
    return [
        ClientSummaryItem(
            id=i["id"],
            fullName=i["full_name"],
            idNumber=i["id_number"],
            totalAmount=i["total_amount"],
            sources=i["sources_display"],
            rawSources=i["raw_sources"],
            fundCount=i["fund_count"],
            lastUpdate=i["last_update"],
        )
        for i in items
    ]


@router.get("/clients/{client_id}/notes", response_model=List[NoteRead])
def list_client_notes(client_id: int, db: Session = Depends(get_db)):
    client = crm_service.get_client(db, client_id)
    if not client:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Client not found")
    notes = crm_service.list_client_notes(db, client_id)
    return [
        NoteRead(
            id=n.id,
            note=n.note or "",
            createdAt=n.created_at,
            reminderAt=n.reminder_at,
            dismissedAt=n.dismissed_at,
        )
        for n in notes
    ]


@router.post("/clients/{client_id}/notes", response_model=NoteRead, status_code=status.HTTP_201_CREATED)
def create_client_note(
    client_id: int,
    note_in: NoteCreate,
    db: Session = Depends(get_db),
):
    client = crm_service.get_client(db, client_id)
    if not client:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Client not found")

    note = crm_service.create_client_note(db, client_id, note_in.note, note_in.reminderAt)
    return NoteRead(
        id=note.id,
        note=note.note or "",
        createdAt=note.created_at,
        reminderAt=note.reminder_at,
        dismissedAt=note.dismissed_at,
    )


@router.post("/clients/{client_id}/notes/{note_id}/dismiss", response_model=NoteRead)
def dismiss_client_note(client_id: int, note_id: int, db: Session = Depends(get_db)):
    note = crm_service.dismiss_client_note(db, client_id, note_id)
    if not note:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Note not found")
    return NoteRead(
        id=note.id,
        note=note.note or "",
        createdAt=note.created_at,
        reminderAt=note.reminder_at,
        dismissedAt=note.dismissed_at,
    )


@router.post("/clients/{client_id}/notes/{note_id}/clear-reminder", response_model=NoteRead)
def clear_note_reminder(client_id: int, note_id: int, db: Session = Depends(get_db)):
    note = crm_service.clear_note_reminder(db, client_id, note_id)
    if not note:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Note not found")
    return NoteRead(
        id=note.id,
        note=note.note or "",
        createdAt=note.created_at,
        reminderAt=note.reminder_at,
        dismissedAt=note.dismissed_at,
    )


@router.delete("/clients/{client_id}/notes/{note_id}")
def delete_client_note(client_id: int, note_id: int, db: Session = Depends(get_db)):
    ok = crm_service.delete_client_note(db, client_id, note_id)
    if not ok:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Note not found")
    return {"status": "ok"}


@router.get("/reminders", response_model=List[ReminderRead])
def list_global_reminders(db: Session = Depends(get_db)):
    items = crm_service.list_global_reminders(db)
    return [
        ReminderRead(
            id=i["id"],
            note=i["note"],
            createdAt=i["created_at"],
            reminderAt=i["reminder_at"],
            dismissedAt=i["dismissed_at"],
            clientId=i["client_id"],
            clientName=i["client_name"],
        )
        for i in items
    ]


@router.put("/clients/{client_id}", response_model=ClientRead)
def update_client(client_id: int, client_update: ClientUpdate, db: Session = Depends(get_db)):
    client = crm_service.update_client(db, client_id, client_update)
    if not client:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Client not found")
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
        birthDate=client.birth_date.isoformat() if client.birth_date else None,
        gender=client.gender,
        maritalStatus=client.marital_status,
        birthCountry=client.birth_country,
        employerName=client.employer_name,
        employerHp=client.employer_hp,
        employerAddress=client.employer_address,
        employerPhone=client.employer_phone,
    )


@router.delete("/clients/{client_id}")
def delete_client(client_id: int, db: Session = Depends(get_db)):
    ok = crm_service.delete_client(db, client_id)
    if not ok:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Client not found",
        )
    return {"status": "ok"}


@router.get("/clients/{client_id}/report.pdf")
def download_client_report_pdf(
    client_id: int,
    month: Optional[str] = None,
    db: Session = Depends(get_db),
):
    try:
        client_data, rows, total_amount, report_month = build_client_report_data(
            db, client_id, month
        )
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Client not found",
        )

    if not rows:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No data found for this client",
        )

    html = render_client_report_html(
        client=client_data,
        rows=rows,
        total_amount=total_amount,
        month=report_month,
    )
    pdf_bytes = generate_client_report_pdf(html)

    display_name = (
        client_data.get("full_name")
        or client_data.get("id_number")
        or f"client_{client_id}"
    )
    safe_name_chars = []
    for ch in display_name:
        if ch.isalnum() or "\u0590" <= ch <= "\u05FF":
            safe_name_chars.append(ch)
        else:
            safe_name_chars.append("_")
    safe_name = "".join(safe_name_chars)
    filename = f"client_report_{safe_name}.pdf"

    if pdf_bytes is None:
        return Response(content=html, media_type="text/html; charset=utf-8")

    headers = {
        "Content-Disposition": f'attachment; filename="{filename}"',
    }
    return Response(content=pdf_bytes, media_type="application/pdf", headers=headers)
