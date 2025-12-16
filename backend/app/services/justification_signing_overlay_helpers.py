from __future__ import annotations

import io

from pypdf import PdfReader as PyPdfReader, PdfWriter as PyPdfWriter

from app.services import justification_forms as justification_forms_service


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
