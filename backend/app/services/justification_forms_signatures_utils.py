from __future__ import annotations

import base64
import io
from typing import Optional

from reportlab.lib.utils import ImageReader


def _decode_data_url(data_url: str) -> bytes:
    if not data_url:
        return b""

    parts = data_url.split(",", 1)
    if len(parts) == 2:
        _, b64_data = parts
    else:
        b64_data = parts[0]
    return base64.b64decode(b64_data)


def _pdf_deref(value):
    return value.get_object() if hasattr(value, "get_object") else value


def _rect_to_float_tuple(rect) -> Optional[tuple[float, float, float, float]]:
    try:
        if not rect or len(rect) != 4:
            return None
        return float(rect[0]), float(rect[1]), float(rect[2]), float(rect[3])
    except Exception:
        return None


def _append_sig_rect(
    sig_rects_by_page: dict,
    page_idx: int,
    rect_tuple: tuple[float, float, float, float],
    *,
    dedupe: bool,
) -> None:
    if page_idx not in sig_rects_by_page:
        sig_rects_by_page[page_idx] = []
    if dedupe and rect_tuple in sig_rects_by_page[page_idx]:
        return
    sig_rects_by_page[page_idx].append(rect_tuple)


def _append_sig_rect_from_rect(sig_rects_by_page: dict, page_idx: Optional[int], rect, *, dedupe: bool) -> None:
    if page_idx is None:
        return
    rect_tuple = _rect_to_float_tuple(rect)
    if rect_tuple is None:
        return
    _append_sig_rect(sig_rects_by_page, page_idx, rect_tuple, dedupe=dedupe)


def _load_signature_image(signature_image_data: str) -> tuple[Optional[ImageReader], float, float]:
    try:
        img_bytes = _decode_data_url(signature_image_data)
        if not img_bytes:
            return None, 0.0, 0.0
        img_stream = io.BytesIO(img_bytes)
        img = ImageReader(img_stream)
        img_width, img_height = img.getSize()
        if img_width <= 0 or img_height <= 0:
            return None, 0.0, 0.0
        return img, float(img_width), float(img_height)
    except Exception:
        return None, 0.0, 0.0
