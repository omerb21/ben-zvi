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
from app.services import justification_forms_overlay_impl_helpers as _helpers


_OVERLAY_FONT_NAME: str = ""


def _get_default_signature_image_path() -> Optional[Path]:
    return _helpers._get_default_signature_image_path()


def _register_overlay_font() -> str:
    global _OVERLAY_FONT_NAME
    font_name = _helpers._register_overlay_font()
    _OVERLAY_FONT_NAME = _helpers._OVERLAY_FONT_NAME
    return font_name


def _parse_rel_signature_position(signature_position: Optional[str]) -> tuple[Optional[float], Optional[float]]:
    return _helpers._parse_rel_signature_position(signature_position)


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
    return _helpers._draw_signature_image(
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
    return _helpers._try_draw_signature_image_from_data_url(
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
    return _helpers._try_draw_signature_image_from_static_file(
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
    return _helpers._get_overlay_target_page(reader, signature_position)


def _draw_free_text_block(
    c,
    free_text: str,
    *,
    page_height: float,
    text_margin_left: float,
    text_margin_bottom: float,
    line_height: float,
) -> None:
    return _helpers._draw_free_text_block(
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
    global _OVERLAY_FONT_NAME
    result = _helpers.apply_overlay_to_pdf(
        source_pdf_bytes,
        free_text=free_text,
        signature_image_data=signature_image_data,
        signature_position=signature_position,
    )
    _OVERLAY_FONT_NAME = _helpers._OVERLAY_FONT_NAME
    return result
