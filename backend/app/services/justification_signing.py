from __future__ import annotations

import io
import secrets
from typing import Tuple

from pypdf import PdfReader as PyPdfReader, PdfWriter as PyPdfWriter
from sqlalchemy.orm import Session

from app.models import Client, ClientSignatureRequest
from app.services import justification_b1 as justification_b1_service
from app.services import justification_forms as justification_forms_service
from app.services import justification_packet as justification_packet_service
from app.services import justification_advice as justification_advice_service


def _add_signature_to_advice_pages(
    packet_bytes: bytes,
    signature_data_url: str,
    advice_page_count: int,
) -> bytes:
    """
    מוסיף את חתימת הלקוח לדפי ההנמקה (הדפים הראשונים בחבילה).
    משתמש ב-overlay כדי לא לפגוע בשדות הטופס.
    """
    from reportlab.pdfgen import canvas
    from reportlab.lib.utils import ImageReader
    
    if not signature_data_url or advice_page_count <= 0:
        return packet_bytes
    
    try:
        # פענח את תמונת החתימה
        sig_bytes = justification_forms_service._decode_data_url(signature_data_url)
        if not sig_bytes:
            return packet_bytes
        
        img = ImageReader(io.BytesIO(sig_bytes))
        img_width, img_height = img.getSize()
        if img_width <= 0 or img_height <= 0:
            return packet_bytes
        
        reader = PyPdfReader(io.BytesIO(packet_bytes))
        writer = PyPdfWriter()
        writer.clone_document_from_reader(reader)
        
        # מיקומי חתימת לקוח בדפי ההנמקה (מבוסס על התבנית)
        # קואורדינטות ב-PDF הן מהפינה השמאלית-תחתונה
        # עמוד A4: 595 רוחב, 842 גובה
        # X=400 זה בצד ימין, Y גבוה יותר = גבוה יותר בדף
        SIGNATURE_POSITIONS = [
            # (page_index, x, y, width, height) - 0-indexed
            # חתימה בעמוד האחרון
            (advice_page_count - 1, 370, 390, 120, 50),
            # חתימה בעמוד הרביעי מהסוף
            (advice_page_count - 4, 370, 250, 120, 50),
        ]
        
        for pos in SIGNATURE_POSITIONS:
            if pos is None:
                continue
            page_idx, x, y, target_w, target_h = pos
            if page_idx < 0 or page_idx >= len(writer.pages):
                continue
            
            page = writer.pages[page_idx]
            page_width = float(page.mediabox.width)
            page_height = float(page.mediabox.height)
            
            # חשב את הגודל תוך שמירה על יחס הגובה-רוחב
            scale = min(target_w / img_width, target_h / img_height, 1.0)
            draw_w = img_width * scale
            draw_h = img_height * scale
            
            # צור overlay עם החתימה
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

    if edited_packet_path.is_file():
        packet_path = edited_packet_path
    elif base_packet_path.is_file():
        packet_path = base_packet_path
    else:
        raise ValueError("CLIENT_PACKET_PDF_NOT_FOUND")

    token = secrets.token_urlsafe(32)

    request = ClientSignatureRequest(
        client_id=client.id,
        token=token,
        packet_filename=packet_path.name,
        status="pending",
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

    if not packet_path.is_file():
        raise ValueError("CLIENT_PACKET_PDF_NOT_FOUND")

    source_bytes = packet_path.read_bytes()

    # לחבילה ערוכה: הוסף חתימת לקוח לדפי ההנמקה (overlay, לא החלפה)
    if packet_path != base_packet_path:
        advice_path = justification_packet_service._get_advice_pdf_path(client)
        if advice_path.is_file():
            try:
                advice_reader = PyPdfReader(io.BytesIO(advice_path.read_bytes()))
                advice_page_count = len(advice_reader.pages)
                source_bytes = _add_signature_to_advice_pages(
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
    return request
