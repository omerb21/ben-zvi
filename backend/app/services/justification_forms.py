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

    base_dir = Path(__file__).resolve().parent.parent
    project_font_dir = base_dir / "static" / "fonts"

    candidate_paths = [
        project_font_dir / "hebrew.ttf",
        project_font_dir / "arial.ttf",
        project_font_dir / "DejaVuSans.ttf",
        Path(r"C:\\Windows\\Fonts\\arial.ttf"),
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
    ]

    for path in candidate_paths:
        try:
            if path.is_file():
                pdfmetrics.registerFont(TTFont(font_name, str(path)))
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


def _get_inherited_ft(field_obj) -> str:
    """
    מחזיר את ה-FT (field type) של שדה, כולל ירושה מהורים.
    ב-PDF, ה-FT יכול להיות על השדה עצמו או על אב קדמון.
    """
    current = field_obj
    visited = set()
    while current is not None:
        try:
            obj = current.get_object() if hasattr(current, "get_object") else current
            obj_id = id(obj)
            if obj_id in visited:
                break
            visited.add(obj_id)

            ft = obj.get("/FT")
            if ft:
                return str(ft)

            current = obj.get("/Parent")
        except Exception:
            break
    return ""


def _get_full_field_name(field_obj) -> str:
    """
    בונה את השם המלא של השדה (FQN) על ידי צירוף שמות ההורים.
    לדוגמה: "form1.page1.Signature1"
    """
    parts = []
    current = field_obj
    visited = set()
    while current is not None:
        try:
            obj = current.get_object() if hasattr(current, "get_object") else current
            obj_id = id(obj)
            if obj_id in visited:
                break
            visited.add(obj_id)

            name = obj.get("/T")
            if name:
                parts.append(str(name))

            current = obj.get("/Parent")
        except Exception:
            break
    parts.reverse()
    return ".".join(parts)


def _is_signature_field(annot) -> bool:
    """
    בודק אם annotation הוא שדה חתימה.
    בודק FT ישירות ובירושה, וגם שמות שדות.
    """
    # בדיקת FT בירושה מלאה
    ft = _get_inherited_ft(annot)
    if ft == "/Sig":
        return True

    # בדיקת שם מלא של השדה
    full_name = _get_full_field_name(annot).lower()
    if "sig" in full_name or "חתימ" in full_name:
        return True

    # בדיקת שם ישיר על ה-annotation
    field_name = annot.get("/T")
    if field_name:
        name_str = str(field_name).lower()
        if "sig" in name_str or "חתימ" in name_str:
            return True

    return False


def _collect_sig_fields_from_acroform(reader) -> dict:
    """
    אוסף את כל שדות החתימה מה-AcroForm ומחזיר מילון של page_index -> list of rects.
    זה מאפשר לזהות שדות חתימה גם כשהם לא מופיעים ישירות ב-Annots של הדף.
    """
    sig_rects_by_page = {}

    try:
        root = reader.trailer.get("/Root")
        if not root:
            return sig_rects_by_page

        root_obj = root.get_object() if hasattr(root, "get_object") else root
        acroform = root_obj.get("/AcroForm")
        if not acroform:
            return sig_rects_by_page

        acroform_obj = acroform.get_object() if hasattr(acroform, "get_object") else acroform
        fields = acroform_obj.get("/Fields")
        if not fields:
            return sig_rects_by_page

        # מיפוי דפים לאינדקסים
        page_to_index = {}
        for i, page in enumerate(reader.pages):
            page_to_index[id(page.get_object())] = i

        def process_field(field_ref, inherited_ft=""):
            try:
                field = field_ref.get_object() if hasattr(field_ref, "get_object") else field_ref

                # FT יכול להיות על השדה או לרשת מהורה
                ft = field.get("/FT")
                if ft:
                    current_ft = str(ft)
                else:
                    current_ft = inherited_ft

                # בדיקת שם
                field_name = field.get("/T")
                is_sig_by_name = False
                if field_name:
                    name_lower = str(field_name).lower()
                    if "sig" in name_lower or "חתימ" in name_lower:
                        is_sig_by_name = True

                is_sig_field = (current_ft == "/Sig") or is_sig_by_name

                # אם זה שדה חתימה, מצא את ה-Widget(s) שלו
                if is_sig_field:
                    # השדה עצמו יכול להיות Widget
                    rect = field.get("/Rect")
                    page_ref = field.get("/P")
                    if rect and len(rect) == 4 and page_ref:
                        try:
                            page_obj = page_ref.get_object() if hasattr(page_ref, "get_object") else page_ref
                            page_idx = page_to_index.get(id(page_obj))
                            if page_idx is not None:
                                llx, lly, urx, ury = float(rect[0]), float(rect[1]), float(rect[2]), float(rect[3])
                                if page_idx not in sig_rects_by_page:
                                    sig_rects_by_page[page_idx] = []
                                sig_rects_by_page[page_idx].append((llx, lly, urx, ury))
                        except Exception:
                            pass

                # עבור על Kids
                kids = field.get("/Kids")
                if kids:
                    for kid_ref in kids:
                        process_field(kid_ref, current_ft)

            except Exception:
                pass

        for field_ref in fields:
            process_field(field_ref)

    except Exception:
        pass

    return sig_rects_by_page


def _collect_all_sig_rects(reader) -> dict:
    """
    אוסף את כל מיקומי שדות החתימה מ-PDF ומחזיר מילון של page_index -> list of rects.
    """
    sig_rects_by_page = {}

    # שיטה 1: חיפוש מה-AcroForm
    acroform_rects = _collect_sig_fields_from_acroform(reader)
    for page_idx, rects in acroform_rects.items():
        if page_idx not in sig_rects_by_page:
            sig_rects_by_page[page_idx] = []
        sig_rects_by_page[page_idx].extend(rects)

    # שיטה 2: חיפוש ישיר ב-Annots של כל דף
    for page_idx, page in enumerate(reader.pages):
        annots = page.get("/Annots") or []
        for annot_ref in annots:
            try:
                annot = annot_ref.get_object()
                if not _is_signature_field(annot):
                    continue
                rect = annot.get("/Rect")
                if not rect or len(rect) != 4:
                    continue
                llx = float(rect[0])
                lly = float(rect[1])
                urx = float(rect[2])
                ury = float(rect[3])
                rect_tuple = (llx, lly, urx, ury)
                if page_idx not in sig_rects_by_page:
                    sig_rects_by_page[page_idx] = []
                if rect_tuple not in sig_rects_by_page[page_idx]:
                    sig_rects_by_page[page_idx].append(rect_tuple)
            except Exception:
                continue

    return sig_rects_by_page


def apply_signature_to_sig_fields(
    source_pdf_bytes: bytes,
    signature_image_data: str,
    reference_pdf_bytes: bytes = None,
) -> bytes:
    """
    מחיל חתימה על כל שדות החתימה ב-PDF.
    
    Args:
        source_pdf_bytes: ה-PDF שעליו יוחלו החתימות
        signature_image_data: תמונת החתימה כ-data URL
        reference_pdf_bytes: אופציונלי - PDF מקורי לחילוץ מיקומי שדות חתימה
                            שאולי אבדו בעריכה
    """
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

    # אסוף שדות חתימה מה-PDF המקור
    sig_rects_by_page = _collect_all_sig_rects(base_reader)

    # אם יש PDF מקורי לייחוס, אסוף גם ממנו את מיקומי החתימות
    # זה מטפל במקרה שעריכה ב-Adobe איבדה את שדות החתימה
    if reference_pdf_bytes:
        try:
            ref_reader = PyPdfReader(io.BytesIO(reference_pdf_bytes))
            ref_sig_rects = _collect_all_sig_rects(ref_reader)
            
            # הוסף מיקומים מה-reference שלא נמצאו ב-source
            for page_idx, rects in ref_sig_rects.items():
                if page_idx >= len(base_reader.pages):
                    continue  # דלג על עמודים שלא קיימים ב-source
                if page_idx not in sig_rects_by_page:
                    sig_rects_by_page[page_idx] = []
                for rect in rects:
                    if rect not in sig_rects_by_page[page_idx]:
                        sig_rects_by_page[page_idx].append(rect)
        except Exception:
            pass

    any_signature_drawn = False

    for page_index, page in enumerate(writer.pages):
        # קח את מיקומי החתימות שכבר אספנו (מה-source ומה-reference)
        sig_rects = sig_rects_by_page.get(page_index, [])

        if not sig_rects:
            continue

        any_signature_drawn = True

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
        return apply_overlay_to_pdf(
            source_pdf_bytes,
            free_text=None,
            signature_image_data=signature_image_data,
            signature_position="bottom_right",
        )

    out_buf = io.BytesIO()
    writer.write(out_buf)

    return out_buf.getvalue()


def flatten_form_fields(source_pdf_bytes: bytes) -> bytes:
    # החזרה למצב הקודם: לא משטחים בפועל את ה-PDF, רק מחזירים את הקובץ המקורי.
    # זה מוודא שהחתימה פועלת כמו בעבר, ללא שינוי באופן הרינדור של כרום/Adobe.
    return source_pdf_bytes
