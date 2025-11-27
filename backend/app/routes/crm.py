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
from app.utils.crm_mappers import (
    to_client_read,
    to_snapshot_read,
    to_summary_response,
    to_monthly_change_point,
    to_history_points,
    to_fund_history_point,
    to_client_summary_item,
    to_note_read,
    to_reminder_read,
)


router = APIRouter(prefix="/api/v1/crm", tags=["crm"])


@router.get("/clients", response_model=List[ClientRead])
def list_clients(db: Session = Depends(get_db)):
    clients = crm_service.list_clients(db)
    return [to_client_read(client) for client in clients]


@router.get("/clients/{client_id}", response_model=ClientRead)
def get_client(client_id: int, db: Session = Depends(get_db)):
    client = crm_service.get_client(db, client_id)
    if not client:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Client not found")
    return to_client_read(client)


@router.post("/clients", response_model=ClientRead, status_code=status.HTTP_201_CREATED)
def create_client(client_in: ClientCreate, db: Session = Depends(get_db)):
    client = crm_service.create_client(db, client_in)
    return to_client_read(client)


@router.get(
    "/clients/{client_id}/snapshots",
    response_model=List[SnapshotRead],
)
def list_client_snapshots(client_id: int, db: Session = Depends(get_db)):
    client = crm_service.get_client(db, client_id)
    if not client:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Client not found")

    snapshots = crm_service.list_client_snapshots(db, client_id)
    return [to_snapshot_read(snapshot) for snapshot in snapshots]


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
    return to_snapshot_read(snapshot)


@router.get("/summary", response_model=SummaryResponse)
def get_summary(month: Optional[str] = None, db: Session = Depends(get_db)):
    target_month, total, by_source, by_type = crm_service.get_snapshot_summary(db, month)
    return to_summary_response(target_month, total, by_source, by_type)


@router.get("/monthly-change", response_model=List[MonthlyChangePoint])
def get_monthly_change(db: Session = Depends(get_db)):
    points = crm_service.get_monthly_change(db)
    return [to_monthly_change_point(p) for p in points]


@router.get("/history", response_model=List[HistoryPoint])
def get_history(client_id: Optional[int] = None, db: Session = Depends(get_db)):
    items = crm_service.get_history(db, client_id)
    return to_history_points(items)


@router.get("/fund-history", response_model=List[FundHistoryPoint])
def get_fund_history(
    client_id: int,
    fund_number: str,
    db: Session = Depends(get_db),
):
    items = crm_service.get_fund_history(db, client_id, fund_number)
    return [to_fund_history_point(i) for i in items]


@router.get("/clients-summary", response_model=List[ClientSummaryItem])
def list_client_summaries(month: Optional[str] = None, db: Session = Depends(get_db)):
    items = crm_service.list_client_summaries(db, month)
    return [to_client_summary_item(i) for i in items]


@router.get("/clients/{client_id}/notes", response_model=List[NoteRead])
def list_client_notes(client_id: int, db: Session = Depends(get_db)):
    client = crm_service.get_client(db, client_id)
    if not client:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Client not found")
    notes = crm_service.list_client_notes(db, client_id)
    return [to_note_read(n) for n in notes]


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
    return to_note_read(note)


@router.post("/clients/{client_id}/notes/{note_id}/dismiss", response_model=NoteRead)
def dismiss_client_note(client_id: int, note_id: int, db: Session = Depends(get_db)):
    note = crm_service.dismiss_client_note(db, client_id, note_id)
    if not note:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Note not found")
    return to_note_read(note)


@router.post("/clients/{client_id}/notes/{note_id}/clear-reminder", response_model=NoteRead)
def clear_note_reminder(client_id: int, note_id: int, db: Session = Depends(get_db)):
    note = crm_service.clear_note_reminder(db, client_id, note_id)
    if not note:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Note not found")
    return to_note_read(note)


@router.delete("/clients/{client_id}/notes/{note_id}")
def delete_client_note(client_id: int, note_id: int, db: Session = Depends(get_db)):
    ok = crm_service.delete_client_note(db, client_id, note_id)
    if not ok:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Note not found")
    return {"status": "ok"}


@router.get("/reminders", response_model=List[ReminderRead])
def list_global_reminders(db: Session = Depends(get_db)):
    items = crm_service.list_global_reminders(db)
    return [to_reminder_read(i) for i in items]


@router.put("/clients/{client_id}", response_model=ClientRead)
def update_client(client_id: int, client_update: ClientUpdate, db: Session = Depends(get_db)):
    client = crm_service.update_client(db, client_id, client_update)
    if not client:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Client not found")
    return to_client_read(client)


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
