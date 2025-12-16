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
from app.services.justification_forms_signatures import _decode_data_url as _decode_data_url_impl
from app.services.justification_forms_signatures import _load_signature_image as _load_signature_image
from app.services import justification_forms_overlay as _forms_overlay
from app.services.justification_forms_signatures import (
    apply_signature_to_sig_fields as _apply_signature_to_sig_fields_impl,
)
from app.services.justification_forms_signatures import flatten_form_fields as _flatten_form_fields_impl


def _decode_data_url(data_url: str) -> bytes:
    """Decode a data: URL or plain base64 string into raw bytes."""

    return _decode_data_url_impl(data_url)


# Cache for overlay font
_OVERLAY_FONT_NAME: str = ""


def _get_default_signature_image_path() -> Optional[Path]:
    return _forms_overlay._get_default_signature_image_path()


def _register_overlay_font() -> str:
    """Register a font that can render Hebrew if possible.
    Results are cached to avoid repeated file system checks.
    """
    global _OVERLAY_FONT_NAME
    font_name = _forms_overlay._register_overlay_font()
    _OVERLAY_FONT_NAME = _forms_overlay._OVERLAY_FONT_NAME
    return font_name


def _parse_rel_signature_position(signature_position: Optional[str]) -> tuple[Optional[float], Optional[float]]:
    return _forms_overlay._parse_rel_signature_position(signature_position)


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
    return _forms_overlay._draw_signature_image(
        c,
        img_obj,
        signature_position,
        page_width,
        page_height,
        max_sig_width,
        max_sig_height,
        margin_h,
        margin_v,
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
    return _forms_overlay._try_draw_signature_image_from_data_url(
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
    return _forms_overlay._try_draw_signature_image_from_static_file(
        c,
        signature_position=signature_position,
        page_width=page_width,
        page_height=page_height,
        max_sig_width=max_sig_width,
        max_sig_height=max_sig_height,
        margin_h=margin_h,
        margin_v=margin_v,
    )


def _get_overlay_target_page(reader, signature_position: Optional[str]):
    return _forms_overlay._get_overlay_target_page(reader, signature_position)


def _draw_free_text_block(
    c,
    free_text: str,
    *,
    page_height: float,
    text_margin_left: float,
    text_margin_bottom: float,
    line_height: float,
) -> None:
    return _forms_overlay._draw_free_text_block(
        c,
        free_text,
        page_height=page_height,
        text_margin_left=text_margin_left,
        text_margin_bottom=text_margin_bottom,
        line_height=line_height,
    )


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

    return _forms_overlay.apply_overlay_to_pdf(
        source_pdf_bytes,
        free_text=free_text,
        signature_image_data=signature_image_data,
        signature_position=signature_position,
    )
def apply_signature_to_sig_fields(
    source_pdf_bytes: bytes,
    signature_image_data: str,
    reference_pdf_bytes: bytes = None,
) -> bytes:
    """
    מחיל חתימה על כל שדות החתימה ב-PDF.
    אופטימיזציה: טוען את התמונה פעם אחת ומשתמש בה לכל השדות.
    """
    return _apply_signature_to_sig_fields_impl(
        source_pdf_bytes,
        signature_image_data,
        reference_pdf_bytes,
        overlay_fallback=apply_overlay_to_pdf,
    )


def flatten_form_fields(source_pdf_bytes: bytes) -> bytes:
    """"משטיח" את שדות החתימה בלבד בקובץ החתום.

    הרעיון כאן הוא:
    - להשאיר את שדות הטופס האחרים (טקסט, צ'קבוקסים וכו') כפי שהם.
    - להסיר מהעמודים את ה-annotations של שדות החתימה (FT=/Sig או שם שמזוהה
      כחתימה), אחרי שכבר ציירנו מעליהם את תמונת החתימה.

    בצורה זו, הלקוח יראה את החתימה כתמונה סטטית על גבי הטופס, בלי ששדה
    חתימה אינטראקטיבי "ריק" יסתיר אותה בחלק מהצופים (Chrome/Adobe).
    """

    return _flatten_form_fields_impl(source_pdf_bytes)
