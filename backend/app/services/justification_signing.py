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


def _find_client_signature_positions(packet_bytes: bytes, advice_page_count: int):
    """
    מחפש את המיקומים של "חתימת הלקוח" בדפי ההנמקה.
    מחזיר רשימה של (page_idx, x, y) עבור כל מיקום שנמצא.
    אם pdfplumber לא מותקן, מחזיר רשימה ריקה כדי שנשתמש בפולבק קבוע.
    """
    positions = []

    # נסה לייבא את pdfplumber; אם אינו זמין, נחזור מיד ללא שגיאה
    try:
        import pdfplumber  # type: ignore
    except Exception as e:  # pragma: no cover - הגנה בסביבות ללא pdfplumber
        print(f"[SIGNING] pdfplumber not available: {e}. Falling back to fixed positions.")
        return positions

    try:
        with pdfplumber.open(io.BytesIO(packet_bytes)) as pdf:
            for page_idx in range(min(advice_page_count, len(pdf.pages))):
                page = pdf.pages[page_idx]
                page_height = float(page.height)
                page_width = float(page.width)
                words = page.extract_words() or []

                for i, word in enumerate(words):
                    text = word.get("text", "")
                    # חפש "חתימת הלקוח" - יכול להיות מילה אחת או שתיים
                    if "הלקוח" in text and "חתימת" in text:
                        # מצאנו את הביטוי המלא במילה אחת
                        word_top = float(word.get("top", 0))
                        word_x0 = float(word.get("x0", 0))
                        pdf_y = page_height - word_top - 70
                        if 0 < pdf_y < page_height and 0 < word_x0 < page_width:
                            positions.append((page_idx, word_x0, pdf_y))
                    elif "הלקוח" in text:
                        # בדוק אם המילה הקודמת היא "חתימת"
                        if i > 0:
                            prev_word = words[i - 1].get("text", "")
                            if "חתימת" in prev_word:
                                word_top = float(word.get("top", 0))
                                word_x0 = float(words[i - 1].get("x0", 0))
                                pdf_y = page_height - word_top - 70
                                if 0 < pdf_y < page_height and 0 < word_x0 < page_width:
                                    positions.append((page_idx, word_x0, pdf_y))
    except Exception as e:
        print(f"[SIGNING] pdfplumber error: {e}")

    print(f"[SIGNING] Found {len(positions)} signature positions: {positions}")
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
        
        # חפש את מיקומי "חתימת הלקוח" ב-PDF
        signature_positions = _find_client_signature_positions(packet_bytes, advice_page_count)
        
        # אם לא מצאנו, נשתמש בקואורדינטות fallback
        if not signature_positions:
            print(f"[SIGNING] Using fallback positions. advice_page_count={advice_page_count}")
            last_advice_idx = advice_page_count - 1
            fourth_from_end_idx = advice_page_count - 4
            # הרם מעט את החתימות על ציר ה-Y כך שישבו קצת מעל הקו
            if last_advice_idx >= 0:
                signature_positions.append((last_advice_idx, 370, 400))
            if fourth_from_end_idx >= 0:
                signature_positions.append((fourth_from_end_idx, 370, 260))
            print(f"[SIGNING] Fallback positions: {signature_positions}")
        
        print(f"[SIGNING] Will apply signatures at: {signature_positions}")
        reader = PyPdfReader(io.BytesIO(packet_bytes))
        writer = PyPdfWriter()
        writer.clone_document_from_reader(reader)
        
        TARGET_W, TARGET_H = 120, 50
        scale = min(TARGET_W / img_width, TARGET_H / img_height, 1.0)
        draw_w = img_width * scale
        draw_h = img_height * scale
        
        for page_idx, x, y in signature_positions:
            if page_idx < 0 or page_idx >= len(writer.pages):
                print(f"[SIGNING] Skipping invalid page_idx={page_idx}, total_pages={len(writer.pages)}")
                continue
            
            print(f"[SIGNING] Applying signature to page {page_idx} at ({x}, {y})")
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
        print(f"[SIGNING] Successfully wrote signed packet, size={len(out_buf.getvalue())}")
        return out_buf.getvalue()
        
    except Exception as e:
        print(f"[SIGNING] Exception in _add_signature_overlay_to_advice_pages: {e}")
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

    # לחבילה ערוכה: הוסף חתימת לקוח לדפי ההנמקה (overlay)
    if packet_path != base_packet_path:
        print(f"[SIGNING] Edited packet detected, will add signature overlay")
        advice_path = justification_packet_service._get_advice_pdf_path(client)
        print(f"[SIGNING] Advice path: {advice_path}, exists: {advice_path.is_file()}")
        if advice_path.is_file():
            try:
                advice_reader = PyPdfReader(io.BytesIO(advice_path.read_bytes()))
                advice_page_count = len(advice_reader.pages)
                print(f"[SIGNING] Advice page count: {advice_page_count}")
                source_bytes = _add_signature_overlay_to_advice_pages(
                    source_bytes,
                    signature_data_url,
                    advice_page_count,
                )
            except Exception as e:
                print(f"[SIGNING] Error adding signature overlay: {e}")
    else:
        print(f"[SIGNING] Base packet, skipping advice overlay")

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
