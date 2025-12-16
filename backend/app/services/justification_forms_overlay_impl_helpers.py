from __future__ import annotations

import io
from pathlib import Path
from typing import Optional

from pdfrw import PageMerge, PdfReader, PdfWriter
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

from app.utils.paths import get_app_base_dir as _get_app_base_dir
from app.services.justification_forms_signatures import _load_signature_image as _load_signature_image


_OVERLAY_FONT_NAME: str = ""


def _get_default_signature_image_path() -> Optional[Path]:
    base_dir = _get_app_base_dir()
    primary_sign_path = base_dir / "static" / "signature.jpg"
    fallback_sign_path = base_dir / "static" / "sign.jpg"
    if primary_sign_path.is_file():
        return primary_sign_path
    if fallback_sign_path.is_file():
        return fallback_sign_path
    return None


def _register_overlay_font() -> str:
    global _OVERLAY_FONT_NAME

    if _OVERLAY_FONT_NAME:
        return _OVERLAY_FONT_NAME

    font_name = "HebOverlay"

    try:
        pdfmetrics.getFont(font_name)
        _OVERLAY_FONT_NAME = font_name
        return font_name
    except KeyError:
        pass

    base_dir = _get_app_base_dir()
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
                _OVERLAY_FONT_NAME = font_name
                return font_name
        except Exception:
            continue

    _OVERLAY_FONT_NAME = "Helvetica"
    return "Helvetica"


def _parse_rel_signature_position(signature_position: Optional[str]) -> tuple[Optional[float], Optional[float]]:
    if not signature_position:
        return None, None

    if not signature_position.lower().startswith("rel:"):
        return None, None

    try:
        _, coords = signature_position.split(":", 1)
        x_str, y_str = coords.split(",", 1)
        return float(x_str), float(y_str)
    except Exception:
        return None, None


def _draw_signature_image(
    c,
    img_obj: ImageReader,
    signature_position: Optional[str],
    page_width: float,
    page_height: float,
    max_sig_width: float,
    max_sig_height: float,
    margin_h: float,
    margin_v: float,
) -> None:
    img_width, img_height = img_obj.getSize()

    if img_width <= 0 or img_height <= 0:
        return

    scale = min(max_sig_width / img_width, max_sig_height / img_height, 1.0)
    draw_w = img_width * scale
    draw_h = img_height * scale

    rel_x, rel_y = _parse_rel_signature_position(signature_position)

    if rel_x is not None and rel_y is not None:
        x_center = rel_x * page_width
        y_center = rel_y * page_height
        x = x_center - draw_w / 2.0
        y = y_center - draw_h / 2.0
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
        else:
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


def _try_draw_signature_image_from_data_url(
    c,
    *,
    signature_image_data: Optional[str],
    signature_position: Optional[str],
    page_width: float,
    page_height: float,
    max_sig_width: float,
    max_sig_height: float,
    margin_h: float,
    margin_v: float,
) -> bool:
    if not signature_image_data:
        return False

    try:
        img, _img_w, _img_h = _load_signature_image(signature_image_data)
        if img is None:
            return False
        _draw_signature_image(
            c,
            img,
            signature_position,
            page_width,
            page_height,
            max_sig_width,
            max_sig_height,
            margin_h,
            margin_v,
        )
        return True
    except Exception:
        return False


def _try_draw_signature_image_from_static_file(
    c,
    *,
    signature_position: Optional[str],
    page_width: float,
    page_height: float,
    max_sig_width: float,
    max_sig_height: float,
    margin_h: float,
    margin_v: float,
) -> bool:
    if not signature_position:
        return False

    try:
        sign_path = _get_default_signature_image_path()
        if sign_path is None:
            return False
        img = ImageReader(str(sign_path))
        _draw_signature_image(
            c,
            img,
            signature_position,
            page_width,
            page_height,
            max_sig_width,
            max_sig_height,
            margin_h,
            margin_v,
        )
        return True
    except Exception:
        return False


def _get_overlay_target_page(reader, signature_position: Optional[str]):
    if signature_position:
        return reader.pages[-1]
    return reader.pages[0]


def _draw_free_text_block(
    c,
    free_text: str,
    *,
    page_height: float,
    text_margin_left: float,
    text_margin_bottom: float,
    line_height: float,
) -> None:
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


def apply_overlay_to_pdf(
    source_pdf_bytes: bytes,
    free_text: Optional[str] = None,
    signature_image_data: Optional[str] = None,
    signature_position: Optional[str] = None,
) -> bytes:
    reader = PdfReader(fdata=source_pdf_bytes)
    if not reader.pages:
        return source_pdf_bytes

    target_page = _get_overlay_target_page(reader, signature_position)

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
        _draw_free_text_block(
            c,
            free_text,
            page_height=page_height,
            text_margin_left=text_margin_left,
            text_margin_bottom=text_margin_bottom,
            line_height=line_height,
        )

    max_sig_width = 180.0
    max_sig_height = 80.0
    margin_h = 40.0
    margin_v = 60.0

    if signature_image_data:
        _try_draw_signature_image_from_data_url(
            c,
            signature_image_data=signature_image_data,
            signature_position=signature_position,
            page_width=page_width,
            page_height=page_height,
            max_sig_width=max_sig_width,
            max_sig_height=max_sig_height,
            margin_h=margin_h,
            margin_v=margin_v,
        )

    elif signature_position:
        _try_draw_signature_image_from_static_file(
            c,
            signature_position=signature_position,
            page_width=page_width,
            page_height=page_height,
            max_sig_width=max_sig_width,
            max_sig_height=max_sig_height,
            margin_h=margin_h,
            margin_v=margin_v,
        )

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
