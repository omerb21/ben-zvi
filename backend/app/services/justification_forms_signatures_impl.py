from __future__ import annotations

import io

from pypdf import PdfReader as PyPdfReader, PdfWriter as PyPdfWriter
from pypdf.generic import NameObject
from reportlab.pdfgen import canvas

from app.services import justification_forms_signatures_sigfields as _sigfields
from app.services import justification_forms_signatures_utils as _sig_utils
from app.services import justification_forms_signatures_impl_helpers as _helpers


def _collect_sig_fields_from_acroform(reader) -> dict:
    return _helpers._collect_sig_fields_from_acroform(reader)


def _collect_all_sig_rects(reader) -> dict:
    return _helpers._collect_all_sig_rects(reader)


def count_signature_fields(source_pdf_bytes: bytes) -> int:
    return _helpers.count_signature_fields(source_pdf_bytes)


def apply_signature_to_sig_fields(
    source_pdf_bytes: bytes,
    signature_image_data: str,
    reference_pdf_bytes: bytes = None,
    *,
    overlay_fallback=None,
) -> bytes:
    return _helpers.apply_signature_to_sig_fields(
        source_pdf_bytes,
        signature_image_data,
        reference_pdf_bytes,
        overlay_fallback=overlay_fallback,
    )


def flatten_form_fields(source_pdf_bytes: bytes) -> bytes:
    return _helpers.flatten_form_fields(source_pdf_bytes)


def has_missing_signature_draws(source_pdf_bytes: bytes, reference_pdf_bytes: bytes) -> bool:
    return _helpers.has_missing_signature_draws(source_pdf_bytes, reference_pdf_bytes)
