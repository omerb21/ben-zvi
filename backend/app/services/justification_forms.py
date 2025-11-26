from __future__ import annotations

import base64
import io
import os
from pathlib import Path
from typing import Optional

from pdfrw import PageMerge, PdfReader, PdfWriter
from pypdf import PdfReader as PyPdfReader, PdfWriter as PyPdfWriter
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas


def _decode_data_url(data_url: str) -> bytes:
    """Decode a data: URL or plain base64 string into raw bytes."""

    if not data_url:
        return b""

    parts = data_url.split(",", 1)
    if len(parts) == 2:
        _, b64_data = parts
    else:
        b64_data = parts[0]
    return base64.b64decode(b64_data)


def _register_overlay_font() -> str:
    """Register a font that can render Hebrew if possible.

    We try common system fonts; if none are available we fall back to
    the default Helvetica (which may not support Hebrew but avoids
    crashing).
    """

    font_name = "HebOverlay"

    # If already registered, just reuse it.
    try:
        pdfmetrics.getFont(font_name)
        return font_name
    except KeyError:
        pass

    candidates = [
        r"C:\\Windows\\Fonts\\arial.ttf",
        r"/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]
    for path in candidates:
        if os.path.exists(path):
            try:
                pdfmetrics.registerFont(TTFont(font_name, path))
                return font_name
            except Exception:
                continue

    # Fallback: use built-in Helvetica if nothing better is available.
    return "Helvetica"


def apply_overlay_to_pdf(
    source_pdf_bytes: bytes,
    free_text: Optional[str] = None,
    signature_image_data: Optional[str] = None,
    signature_position: Optional[str] = None,
) -> bytes:
    """Overlay free text and an optional signature image on top of the first page.

    The original PDF bytes are taken as the base. We draw a text block near the
    bottom-left, and optionally draw a signature image either from a data URL
    or from a static sign.jpg file placed according to signature_position.
    """

    reader = PdfReader(fdata=source_pdf_bytes)
    if not reader.pages:
        return source_pdf_bytes

    # Decide which page to overlay on:
    # - If a signature position is provided (advice document), we place the
    #   overlay on the last page, where חתימה sections usually appear.
    # - Otherwise (text-only overlays for B1 / kits), we place it on the
    #   first page so that it is immediately visible.
    if signature_position:
        target_page = reader.pages[-1]
    else:
        target_page = reader.pages[0]

    page_width = float(target_page.MediaBox[2])
    page_height = float(target_page.MediaBox[3])

    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=(page_width, page_height))

    text_margin_left = 40.0
    text_margin_bottom = 60.0
    line_height = 14.0

    if free_text:
        overlay_font = _register_overlay_font()
        c.setFont(overlay_font, 11)
        lines = free_text.splitlines()
        max_lines = 8
        for idx, raw_line in enumerate(lines[:max_lines]):
            line = raw_line.strip()
            if not line:
                continue
            y = text_margin_bottom + idx * line_height
            if y > page_height - 40.0:
                break
            c.drawString(text_margin_left, y, line)

    max_sig_width = 180.0
    max_sig_height = 80.0
    margin_h = 40.0
    margin_v = 60.0

    def _draw_image(img_obj: ImageReader) -> None:
        img_width, img_height = img_obj.getSize()

        if img_width <= 0 or img_height <= 0:
            return

        scale = min(max_sig_width / img_width, max_sig_height / img_height, 1.0)
        draw_w = img_width * scale
        draw_h = img_height * scale

        rel_x = None
        rel_y = None
        if signature_position and signature_position.lower().startswith("rel:"):
            try:
                _, coords = signature_position.split(":", 1)
                x_str, y_str = coords.split(",", 1)
                rel_x = float(x_str)
                rel_y = float(y_str)
            except Exception:
                rel_x = None
                rel_y = None

        if rel_x is not None and rel_y is not None:
            # Interpret rel_x/rel_y as 0..1 in page coordinates (0=left/bottom, 1=right/top)
            x_center = rel_x * page_width
            y_center = rel_y * page_height
            x = x_center - draw_w / 2.0
            y = y_center - draw_h / 2.0
            # Clamp so the image stays within page margins
            x = max(margin_h, min(page_width - draw_w - margin_h, x))
            y = max(margin_v, min(page_height - draw_h - margin_v, y))
        else:
            pos = (signature_position or "bottom_right").lower()

            if pos == "bottom_left":
                x = margin_h
                y = margin_v
            elif pos == "top_left":
                x = margin_h
                y = page_height - draw_h - margin_v
            elif pos == "top_right":
                x = page_width - draw_w - margin_h
                y = page_height - draw_h - margin_v
            else:  # default "bottom_right" or any unknown value
                x = page_width - draw_w - margin_h
                y = margin_v

        c.drawImage(
            img_obj,
            x,
            y,
            width=draw_w,
            height=draw_h,
            mask="auto",
        )

    # First priority: an explicit image sent from the frontend (used for older flows).
    if signature_image_data:
        try:
            img_bytes = _decode_data_url(signature_image_data)
            if img_bytes:
                img_stream = io.BytesIO(img_bytes)
                img = ImageReader(img_stream)
                _draw_image(img)
        except Exception:
            # If anything goes wrong with the signature image, ignore it and keep the text.
            pass

    # Second priority: a static sign.jpg, when a position was requested.
    elif signature_position:
        try:
            base_dir = Path(__file__).resolve().parent.parent
            primary_sign_path = base_dir / "static" / "signature.jpg"
            fallback_sign_path = base_dir / "static" / "sign.jpg"
            sign_path = primary_sign_path if primary_sign_path.is_file() else fallback_sign_path
            if sign_path.is_file():
                img = ImageReader(str(sign_path))
                _draw_image(img)
        except Exception:
            # Ignore static signature failures; keep the PDF text overlay only.
            pass

    c.save()
    buf.seek(0)

    overlay_reader = PdfReader(fdata=buf.getvalue())
    overlay_page = overlay_reader.pages[0]

    PageMerge(target_page).add(overlay_page).render()

    out_buf = io.BytesIO()
    writer = PdfWriter()
    for page in reader.pages:
        writer.addpage(page)
    writer.write(out_buf)

    return out_buf.getvalue()


def apply_signature_to_sig_fields(
    source_pdf_bytes: bytes,
    signature_image_data: str,
) -> bytes:
    if not signature_image_data:
        return source_pdf_bytes

    try:
        img_bytes = _decode_data_url(signature_image_data)
        if not img_bytes:
            return source_pdf_bytes
        img_stream = io.BytesIO(img_bytes)
        img = ImageReader(img_stream)
        img_width, img_height = img.getSize()
        if img_width <= 0 or img_height <= 0:
            return source_pdf_bytes
    except Exception:
        return source_pdf_bytes

    # Use pypdf for reading/writing the PDF so that we keep the existing
    # AcroForm and appearance settings as stable as possible.
    pdf_stream = io.BytesIO(source_pdf_bytes)
    base_reader = PyPdfReader(pdf_stream)
    if not base_reader.pages:
        return source_pdf_bytes

    writer = PyPdfWriter()
    writer.clone_document_from_reader(base_reader)

    any_signature_drawn = False

    print("[sign] apply_signature_to_sig_fields: pages=", len(writer.pages))

    for page_index, page in enumerate(writer.pages):
        annots = page.get("/Annots") or []
        if not annots:
            continue

        sig_rects = []
        for annot_ref in annots:
            annot = annot_ref.get_object()
            ft = annot.get("/FT")
            parent = annot.get("/Parent")
            parent_ft = parent.get("/FT") if parent is not None else None

            if ft != "/Sig" and parent_ft != "/Sig":
                continue

            rect = annot.get("/Rect")
            if not rect or len(rect) != 4:
                continue

            try:
                llx = float(rect[0])
                lly = float(rect[1])
                urx = float(rect[2])
                ury = float(rect[3])
            except Exception:
                continue

            sig_rects.append((llx, lly, urx, ury))

        if not sig_rects:
            continue

        any_signature_drawn = True

        print("[sign] page", page_index, ": sig_annots=", len(sig_rects))

        page_width = float(page.mediabox.width)
        page_height = float(page.mediabox.height)

        buf = io.BytesIO()
        c = canvas.Canvas(buf, pagesize=(page_width, page_height))

        for llx, lly, urx, ury in sig_rects:
            box_w = max(urx - llx, 1.0)
            box_h = max(ury - lly, 1.0)

            scale = min(box_w / img_width, box_h / img_height, 1.0)
            draw_w = img_width * scale
            draw_h = img_height * scale

            x = llx + (box_w - draw_w) / 2.0
            y = lly + (box_h - draw_h) / 2.0

            c.drawImage(
                img,
                x,
                y,
                width=draw_w,
                height=draw_h,
                mask="auto",
            )

        c.save()
        buf.seek(0)

        overlay_reader = PyPdfReader(buf)
        overlay_page = overlay_reader.pages[0]
        page.merge_page(overlay_page)

    if not any_signature_drawn:
        # אם משום מה לא מצאנו שדות /Sig, נשתמש בפולבק הקודם
        print("[sign] no /Sig fields found, using bottom_right fallback")
        return apply_overlay_to_pdf(
            source_pdf_bytes,
            free_text=None,
            signature_image_data=signature_image_data,
            signature_position="bottom_right",
        )

    out_buf = io.BytesIO()
    writer.write(out_buf)

    return out_buf.getvalue()
