from __future__ import annotations

from typing import Optional

from reportlab.lib.utils import ImageReader
 
from app.services import justification_forms_signatures_impl as _sig_impl
from app.services import justification_forms_signatures_sigfields as _sigfields
from app.services import justification_forms_signatures_utils as _sig_utils


def _decode_data_url(data_url: str) -> bytes:
    """Decode a data: URL or plain base64 string into raw bytes."""

    return _sig_utils._decode_data_url(data_url)


def _pdf_deref(value):
    return _sig_utils._pdf_deref(value)


def _rect_to_float_tuple(rect) -> Optional[tuple[float, float, float, float]]:
    return _sig_utils._rect_to_float_tuple(rect)


def _append_sig_rect(sig_rects_by_page: dict, page_idx: int, rect_tuple: tuple[float, float, float, float], *, dedupe: bool) -> None:
    return _sig_utils._append_sig_rect(sig_rects_by_page, page_idx, rect_tuple, dedupe=dedupe)


def _append_sig_rect_from_rect(sig_rects_by_page: dict, page_idx: Optional[int], rect, *, dedupe: bool) -> None:
    return _sig_utils._append_sig_rect_from_rect(sig_rects_by_page, page_idx, rect, dedupe=dedupe)


def _load_signature_image(signature_image_data: str) -> tuple[Optional[ImageReader], float, float]:
    return _sig_utils._load_signature_image(signature_image_data)


def _get_inherited_ft(field_obj) -> str:
    """
    מחזיר את ה-FT (field type) של שדה, כולל ירושה מהורים.
    ב-PDF, ה-FT יכול להיות על השדה עצמו או על אב קדמון.
    """
    return _sigfields._get_inherited_ft(field_obj)


def _get_full_field_name(field_obj) -> str:
    """
    בונה את השם המלא של השדה (FQN) על ידי צירוף שמות ההורים.
    לדוגמה: "form1.page1.Signature1"
    """
    return _sigfields._get_full_field_name(field_obj)


def _is_signature_field(annot) -> bool:
    """
    בודק אם annotation הוא שדה חתימה.
    בודק FT ישירות ובירושה, וגם שמות שדות.
    """
    return _sigfields._is_signature_field(annot)


def _collect_sig_fields_from_acroform(reader) -> dict:
    """
    אוסף את כל שדות החתימה מה-AcroForm ומחזיר מילון של page_index -> list of rects.
    זה מאפשר לזהות שדות חתימה גם כשהם לא מופיעים ישירות ב-Annots של הדף.
    """
    return _sig_impl._collect_sig_fields_from_acroform(reader)


def _collect_all_sig_rects(reader) -> dict:
    """
    אוסף את כל מיקומי שדות החתימה מ-PDF ומחזיר מילון של page_index -> list of rects.
    """
    return _sig_impl._collect_all_sig_rects(reader)


def count_signature_fields(source_pdf_bytes: bytes) -> int:
    """Return the number of dedicated signature rectangles in a PDF."""
    return _sig_impl.count_signature_fields(source_pdf_bytes)


def apply_signature_to_sig_fields(
    source_pdf_bytes: bytes,
    signature_image_data: str,
    reference_pdf_bytes: bytes = None,
    *,
    overlay_fallback=None,
) -> bytes:
    """
    מחיל חתימה על כל שדות החתימה ב-PDF.
    אופטימיזציה: טוען את התמונה פעם אחת ומשתמש בה לכל השדות.
    """
    return _sig_impl.apply_signature_to_sig_fields(
        source_pdf_bytes,
        signature_image_data,
        reference_pdf_bytes,
        overlay_fallback=overlay_fallback,
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
    return _sig_impl.flatten_form_fields(source_pdf_bytes)
