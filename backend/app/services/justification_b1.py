from __future__ import annotations

import datetime
import io
import os
from pathlib import Path
from typing import Tuple

from pdfrw import PdfName, PageMerge, PdfReader, PdfWriter
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

from app.models import Client
from app.services.pdf_fill_safe import fill_form_auto
from app.utils.paths import get_app_base_dir as _get_base_dir
from app.utils.fs import ensure_dir as _ensure_dir
from app.services import justification_b1_paths as _paths
from app.services import justification_b1_text as _text
from app.services import justification_b1_fill as _fill

def _get_b1_template_path() -> Path:
    return _paths._get_b1_template_path()

def _get_b1_template_path_or_raise() -> Path:
    return _paths._get_b1_template_path_or_raise()

def _get_client_export_dir(client: Client) -> Path:
    return _paths._get_client_export_dir(client)

def _register_hebrew_font() -> str:
    return _fill._register_hebrew_font()

def _contains_hebrew(text: str) -> bool:
    return _text._contains_hebrew(text)

def _normalize_hebrew_value(value: str) -> str:
    if not isinstance(value, str):
        return _text._normalize_hebrew_value(value)
    # For B1 we keep Hebrew text in logical order and let the PDF viewer
    # handle right-to-left layout. No reversal or embedding marks here.
    return _text._normalize_hebrew_value(value)

def _build_client_address(client: Client) -> str:
    return _text._build_client_address(client)

def _build_b1_field_values(client: Client, today: str, full_address: str) -> dict[str, str]:
    return _text._build_b1_field_values(client, today, full_address)

def _build_b1_context(client: Client) -> tuple[str, str, dict[str, str]]:
    return _text._build_b1_context(client)

def _build_b1_temp_output_filename(client: Client, timestamp: str) -> str:
    return _paths._build_b1_temp_output_filename(client, timestamp)

def _get_b1_final_filename(client: Client) -> str:
    return _paths._get_b1_final_filename(client)

def _get_b1_generation_inputs(client: Client) -> tuple[Path, Path, str]:
    return _paths._get_b1_generation_inputs(client)

def _timestamp_str() -> str:
    return _paths._timestamp_str()

def _build_b1_temp_output_path(client: Client, output_dir: Path) -> Path:
    return _paths._build_b1_temp_output_path(client, output_dir)

def fill_b1_pdf_acroform(client: Client, template_path: Path, output_dir: Path) -> Path:
    return _fill.fill_b1_pdf_acroform(client, template_path, output_dir)

def fill_b1_pdf(client: Client, template_path: Path, output_dir: Path) -> Path:
    # Flatten the form by removing annotations and AcroForm so that
    # only the drawn overlay text remains.
    return _fill.fill_b1_pdf(client, template_path, output_dir)

def generate_b1_pdf_for_client(client: Client) -> Tuple[bytes, str]:
    return _fill.generate_b1_pdf_for_client(client)

def generate_b1_pdf_for_client_overlay(client: Client) -> Tuple[bytes, str]:
    # Use the overlay-based filler which reverses Hebrew visually and flattens the form.
    return _fill.generate_b1_pdf_for_client_overlay(client)
