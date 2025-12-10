from __future__ import annotations

import io
import logging
import secrets
import time
from typing import Tuple

from pypdf import PdfReader as PyPdfReader, PdfWriter as PyPdfWriter

logger = logging.getLogger(__name__)
from sqlalchemy.orm import Session

from app.models import Client, ClientSignatureRequest
from app.services import justification_b1 as justification_b1_service
from app.services import justification_forms as justification_forms_service
from app.services import justification_packet as justification_packet_service
from app.services import justification_advice as justification_advice_service


def _get_fallback_signature_positions(advice_page_count: int):
    """
    מחזיר מיקומי חתימה קבועים לדפי ההנמקה.
    גישה מהירה במקום pdfplumber - חוסכת זמן עיבוד משמעותי.
    """
    positions = []
    if advice_page_count > 0:
        last_advice_idx = advice_page_count - 1
        fourth_from_end_idx = advice_page_count - 4
        if last_advice_idx >= 0:
            positions.append((last_advice_idx, 370, 400))
        if fourth_from_end_idx >= 0:
            positions.append((fourth_from_end_idx, 370, 260))
    return positions


def _add_signature_overlay_to_advice_pages(
    packet_bytes: bytes,
    signature_data_url: str,
    advice_page_count: int,
) -> bytes:
    """
    מוסיף overlay של חתימת לקוח לדפי ההנמקה בחבילה הערוכה.
    מחפש את המיקום של "חתימת הלקוח" בטקסט של כל עמוד ומציב את החתימה מתחת.
    """
    from reportlab.pdfgen import canvas
    from reportlab.lib.utils import ImageReader
    
    if not signature_data_url or advice_page_count <= 0:
        return packet_bytes
    
    try:
        sig_bytes = justification_forms_service._decode_data_url(signature_data_url)
        if not sig_bytes:
            return packet_bytes
        
        img = ImageReader(io.BytesIO(sig_bytes))
        img_width, img_height = img.getSize()
        if img_width <= 0 or img_height <= 0:
            return packet_bytes
        
        # שימוש במיקומים קבועים - מהיר יותר משמעותית מחיפוש בטקסט
        signature_positions = _get_fallback_signature_positions(advice_page_count)
        reader = PyPdfReader(io.BytesIO(packet_bytes))
        writer = PyPdfWriter()
        writer.clone_document_from_reader(reader)
        
        TARGET_W, TARGET_H = 120, 50
        scale = min(TARGET_W / img_width, TARGET_H / img_height, 1.0)
        draw_w = img_width * scale
        draw_h = img_height * scale
        
        for page_idx, x, y in signature_positions:
            if page_idx < 0 or page_idx >= len(writer.pages):
                continue
            
            page = writer.pages[page_idx]
            page_width = float(page.mediabox.width)
            page_height = float(page.mediabox.height)
            
            buf = io.BytesIO()
            c = canvas.Canvas(buf, pagesize=(page_width, page_height))
            c.drawImage(img, x, y, width=draw_w, height=draw_h, mask="auto")
            c.save()
            buf.seek(0)
            
            overlay_reader = PyPdfReader(buf)
            page.merge_page(overlay_reader.pages[0])
        
        out_buf = io.BytesIO()
        writer.write(out_buf)
        return out_buf.getvalue()
        
    except Exception:
        return packet_bytes


def _get_packet_paths_for_client(client: Client):
    export_dir = justification_b1_service._get_client_export_dir(client)
    base_packet_path = export_dir / f"packet_{client.id}.pdf"
    edited_packet_path = export_dir / f"packet_{client.id}_edited.pdf"
    signed_packet_path = export_dir / f"packet_{client.id}_signed_client.pdf"
    return export_dir, base_packet_path, edited_packet_path, signed_packet_path


def create_packet_signature_request(db: Session, client_id: int) -> ClientSignatureRequest:
    client = db.get(Client, client_id)
    if not client:
        raise ValueError("CLIENT_NOT_FOUND")

    export_dir, base_packet_path, edited_packet_path, _ = _get_packet_paths_for_client(client)

    packet_pdf_data = None

    if edited_packet_path.is_file():
        packet_path = edited_packet_path
        try:
            packet_pdf_data = edited_packet_path.read_bytes()
        except Exception:
            packet_pdf_data = None
    elif base_packet_path.is_file():
        packet_path = base_packet_path
    else:
        raise ValueError("CLIENT_PACKET_PDF_NOT_FOUND")

    db.query(ClientSignatureRequest).filter(
        ClientSignatureRequest.client_id == client_id,
        ClientSignatureRequest.status == "pending"
    ).delete()

    token = secrets.token_urlsafe(32)

    request = ClientSignatureRequest(
        client_id=client.id,
        token=token,
        packet_filename=packet_path.name,
        signed_packet_filename=None,
        status="pending",
        packet_pdf_data=packet_pdf_data,
    )
    db.add(request)
    db.commit()
    db.refresh(request)
    return request


def get_active_request_for_token(db: Session, token: str) -> Tuple[ClientSignatureRequest, Client]:
    request = db.query(ClientSignatureRequest).filter(ClientSignatureRequest.token == token).first()
    if not request:
        raise ValueError("SIGNATURE_REQUEST_NOT_FOUND")
    if request.status != "pending":
        raise ValueError("SIGNATURE_REQUEST_ALREADY_COMPLETED")

    client = db.get(Client, request.client_id)
    if not client:
        raise ValueError("CLIENT_NOT_FOUND")

    return request, client


def get_request_and_client_for_token(db: Session, token: str) -> Tuple[ClientSignatureRequest, Client]:
    """Fetch a signature request and its client by token without enforcing status.

    Used when we want to access resources (כמו המסמך החתום) גם אחרי שהקישור
    החד-פעמי כבר נוצל והסטטוס של הבקשה איננו "pending".
    """

    request = db.query(ClientSignatureRequest).filter(ClientSignatureRequest.token == token).first()
    if not request:
        raise ValueError("SIGNATURE_REQUEST_NOT_FOUND")

    client = db.get(Client, request.client_id)
    if not client:
        raise ValueError("CLIENT_NOT_FOUND")

    return request, client


def complete_packet_signature(db: Session, token: str, signature_data_url: str) -> ClientSignatureRequest:
    start_time = time.time()
    request = db.query(ClientSignatureRequest).filter(ClientSignatureRequest.token == token).first()
    if not request:
        raise ValueError("SIGNATURE_REQUEST_NOT_FOUND")
    if request.status != "pending" or request.signed_at is not None:
        raise ValueError("SIGNATURE_REQUEST_ALREADY_COMPLETED")

    client = db.get(Client, request.client_id)
    if not client:
        raise ValueError("CLIENT_NOT_FOUND")

    export_dir, base_packet_path, edited_packet_path, signed_packet_path = _get_packet_paths_for_client(client)

    # First, persist the client's drawn signature as a PNG in the
    # export directory so that other documents (e.g. the advice PDF)
    # can embed it visually.
    try:
        sig_bytes = justification_forms_service._decode_data_url(signature_data_url)
        if sig_bytes:
            client_sig_path = export_dir / "client_signature.png"
            client_sig_path.write_bytes(sig_bytes)
    except Exception:
        pass

    # Next, (re)generate the advice PDF so that it can include the
    # client's signature image at the designated locations. Failures
    # here do not affect the main signing flow.
    try:
        justification_advice_service.save_advice_pdf_for_client(db, client)
    except Exception:
        pass

    # Determine which packet file we are signing.
    if request.packet_filename:
        packet_path = export_dir / request.packet_filename
    elif edited_packet_path.is_file():
        packet_path = edited_packet_path
    else:
        packet_path = base_packet_path

    # If we are signing the auto-generated base packet, rebuild it now
    # so that it reflects the latest advice/B1/kits, including the
    # newly signed advice PDF.
    if packet_path == base_packet_path:
        try:
            justification_packet_service.generate_client_packet_pdf(db, client, generate_missing=True)
        except Exception:
            # If packet generation fails, we fall back to the existing
            # packet file (if any). A missing/invalid packet will still
            # be caught by the check below.
            pass

    source_bytes: bytes | None = None

    if packet_path.is_file():
        source_bytes = packet_path.read_bytes()
    elif getattr(request, "packet_pdf_data", None):
        source_bytes = request.packet_pdf_data
    else:
        raise ValueError("CLIENT_PACKET_PDF_NOT_FOUND")

    # לחבילה ערוכה: הוסף חתימת לקוח לדפי ההנמקה (overlay)
    if packet_path != base_packet_path:
        advice_path = justification_packet_service._get_advice_pdf_path(client)
        if advice_path.is_file():
            try:
                advice_reader = PyPdfReader(io.BytesIO(advice_path.read_bytes()))
                advice_page_count = len(advice_reader.pages)
                source_bytes = _add_signature_overlay_to_advice_pages(
                    source_bytes,
                    signature_data_url,
                    advice_page_count,
                )
            except Exception:
                pass

    # לחבילה ערוכה: השתמש בחבילה המקורית כ-reference כדי לקבל מיקומי חתימות
    # שאולי אבדו בעריכה ב-Adobe
    reference_pdf_bytes = None
    if packet_path != base_packet_path and base_packet_path.is_file():
        try:
            reference_pdf_bytes = base_packet_path.read_bytes()
        except Exception:
            pass

    signed_bytes = justification_forms_service.apply_signature_to_sig_fields(
        source_bytes,
        signature_image_data=signature_data_url,
        reference_pdf_bytes=reference_pdf_bytes,
    )

    flattened_bytes = justification_forms_service.flatten_form_fields(signed_bytes)

    if not signed_packet_path.parent.exists():
        signed_packet_path.parent.mkdir(parents=True, exist_ok=True)

    signed_packet_path.write_bytes(flattened_bytes)

    from datetime import datetime, timezone

    request.signed_packet_filename = signed_packet_path.name
    request.status = "signed"
    request.signed_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(request)
    elapsed = time.time() - start_time
    logger.info(f"[PDF-TIMING] Signing completed in {elapsed:.2f}s for client_id={client.id}")
    return request
