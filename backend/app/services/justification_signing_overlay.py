from __future__ import annotations

from app.services import justification_signing_overlay_helpers as _helpers


def _get_fallback_signature_positions(advice_page_count: int):
    """
    מחזיר מיקומי חתימה קבועים לדפי ההנמקה.
    גישה מהירה במקום pdfplumber - חוסכת זמן עיבוד משמעותי.
    """
    return _helpers._get_fallback_signature_positions(advice_page_count)


def _add_signature_overlay_to_advice_pages(
    packet_bytes: bytes,
    signature_data_url: str,
    advice_page_count: int,
) -> bytes:
    """
    מוסיף overlay של חתימת לקוח לדפי ההנמקה בחבילה הערוכה.
    מחפש את המיקום של "חתימת הלקוח" בטקסט של כל עמוד ומציב את החתימה מתחת.
    """
    return _helpers._add_signature_overlay_to_advice_pages(
        packet_bytes,
        signature_data_url,
        advice_page_count,
    )
