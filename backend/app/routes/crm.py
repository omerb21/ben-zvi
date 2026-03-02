from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Response, status, Header
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
from app.utils.filepaths import build_fs_safe_name as _build_fs_safe_name
from app.utils.http_headers import build_attachment_pdf_headers as _build_pdf_attachment_headers
from app.utils.http_exceptions import raise_client_not_found as _raise_client_not_found
from app.utils.http_exceptions import raise_not_found as _raise_not_found
from app.utils.http_exceptions import raise_invalid_access_code as _raise_invalid_access_code
from app.routes.client_helpers import get_client_or_404 as _get_client_or_404
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


def _raise_note_not_found() -> None:
    _raise_not_found("Note not found")


def _ensure_note_or_404(note):
    if not note:
        _raise_note_not_found()
    return note


def _pdf_attachment_response(pdf_bytes: bytes, filename: str) -> Response:
    # Validate input
    if not isinstance(pdf_bytes, bytes):
        raise ValueError("PDF content must be bytes")
    if not pdf_bytes:
        raise ValueError("PDF content cannot be empty")
    
    headers = _build_pdf_attachment_headers(filename)
    return Response(content=pdf_bytes, media_type="application/pdf", headers=headers)


def _build_client_report_pdf_filename(display_name: str | None, client_id: int) -> str:
    value = (display_name or "").strip()
    if not value:
        value = f"client_{client_id}"

    safe_name = _build_fs_safe_name(value, f"client_{client_id}")
    return f"client_report_{safe_name}.pdf"


def _resolve_effective_client_id_from_headers(
    db: Session,
    client_id: int | None,
    x_client_token: str | None,
    x_client_pin: str | None,
) -> int | None:
    effective_client_id = client_id

    if x_client_token:
        client_from_token = crm_service.get_client_by_token(db, x_client_token)
        if not client_from_token:
            _raise_client_not_found()
        if not crm_service.check_client_pin(client_from_token, x_client_pin):
            _raise_invalid_access_code()
        effective_client_id = client_from_token.id

    return effective_client_id


@router.get("/clients", response_model=List[ClientRead])
def list_clients(db: Session = Depends(get_db)):
    clients = crm_service.list_clients(db)
    return [to_client_read(client) for client in clients]


@router.get("/clients/{client_id}", response_model=ClientRead)
def get_client(client_id: int, db: Session = Depends(get_db)):
    client = _get_client_or_404(db, client_id)
    return to_client_read(client)


@router.post("/clients", response_model=ClientRead, status_code=status.HTTP_201_CREATED)
def create_client(client_in: ClientCreate, db: Session = Depends(get_db)):
    client = crm_service.create_client(db, client_in)
    return to_client_read(client)


@router.get(
    "/clients/{client_id}/snapshots",
    response_model=List[SnapshotRead],
)
def list_client_snapshots(
    client_id: int,
    db: Session = Depends(get_db),
    x_client_token: str | None = Header(default=None),
    x_client_pin: str | None = Header(default=None),
):
    effective_client_id = _resolve_effective_client_id_from_headers(
        db,
        client_id,
        x_client_token,
        x_client_pin,
    )
    client = _get_client_or_404(db, int(effective_client_id))

    snapshots = crm_service.list_client_snapshots(db, effective_client_id)
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
    client = _get_client_or_404(db, client_id)

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
def get_history(
    client_id: Optional[int] = None,
    db: Session = Depends(get_db),
    x_client_token: str | None = Header(default=None),
    x_client_pin: str | None = Header(default=None),
):
    effective_client_id = _resolve_effective_client_id_from_headers(
        db,
        client_id,
        x_client_token,
        x_client_pin,
    )

    items = crm_service.get_history(db, effective_client_id)
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
    _get_client_or_404(db, client_id)
    notes = crm_service.list_client_notes(db, client_id)
    return [to_note_read(n) for n in notes]


@router.post("/clients/{client_id}/notes", response_model=NoteRead, status_code=status.HTTP_201_CREATED)
def create_client_note(
    client_id: int,
    note_in: NoteCreate,
    db: Session = Depends(get_db),
):
    _get_client_or_404(db, client_id)

    note = crm_service.create_client_note(db, client_id, note_in.note, note_in.reminderAt)
    return to_note_read(note)


@router.post("/clients/{client_id}/notes/{note_id}/dismiss", response_model=NoteRead)
def dismiss_client_note(client_id: int, note_id: int, db: Session = Depends(get_db)):
    note = _ensure_note_or_404(crm_service.dismiss_client_note(db, client_id, note_id))
    return to_note_read(note)


@router.post("/clients/{client_id}/notes/{note_id}/clear-reminder", response_model=NoteRead)
def clear_note_reminder(client_id: int, note_id: int, db: Session = Depends(get_db)):
    note = _ensure_note_or_404(crm_service.clear_note_reminder(db, client_id, note_id))
    return to_note_read(note)


@router.delete("/clients/{client_id}/notes/{note_id}")
def delete_client_note(client_id: int, note_id: int, db: Session = Depends(get_db)):
    ok = crm_service.delete_client_note(db, client_id, note_id)
    if not ok:
        _raise_note_not_found()
    return {"status": "ok"}


@router.get("/reminders", response_model=List[ReminderRead])
def list_global_reminders(db: Session = Depends(get_db)):
    items = crm_service.list_global_reminders(db)
    return [to_reminder_read(i) for i in items]


@router.put("/clients/{client_id}", response_model=ClientRead)
def update_client(client_id: int, client_update: ClientUpdate, db: Session = Depends(get_db)):
    client = crm_service.update_client(db, client_id, client_update)
    if not client:
        _raise_client_not_found()
    return to_client_read(client)


@router.delete("/clients/{client_id}")
def delete_client(client_id: int, db: Session = Depends(get_db)):
    ok = crm_service.delete_client(db, client_id)
    if not ok:
        _raise_client_not_found()
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
        _raise_client_not_found()

    if not rows:
        _raise_not_found("No data found for this client")

    html = render_client_report_html(
        client=client_data,
        rows=rows,
        total_amount=total_amount,
        month=report_month,
    )
    pdf_bytes = generate_client_report_pdf(html)

    filename = _build_client_report_pdf_filename(
        client_data.get("full_name") or client_data.get("id_number"),
        client_id,
    )

    if pdf_bytes is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Failed to generate client report PDF. Please ensure wkhtmltopdf is installed and accessible."
        )

    return _pdf_attachment_response(pdf_bytes, filename)
