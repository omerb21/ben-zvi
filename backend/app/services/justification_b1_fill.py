from __future__ import annotations

import io
from pathlib import Path
from typing import Tuple

from pdfrw import PdfName, PageMerge, PdfReader, PdfWriter
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

from app.models import Client
from app.services.pdf_fill_safe import fill_form_auto
from app.services import justification_b1_paths as _paths
from app.services import justification_b1_text as _text


def _register_hebrew_font() -> str:
    from app.utils.paths import get_app_base_dir as _get_base_dir

    base_dir = _get_base_dir()
    project_font_dir = base_dir / "static" / "fonts"

    candidate_paths = [
        project_font_dir / "hebrew.ttf",
        project_font_dir / "arial.ttf",
        project_font_dir / "DejaVuSans.ttf",
        Path(r"C:\\Windows\\Fonts\\arial.ttf"),
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
    ]

    for path in candidate_paths:
        if path.is_file():
            pdfmetrics.registerFont(TTFont("Heb", str(path)))
            return "Heb"

    raise AssertionError("Hebrew TTF font not found")


def fill_b1_pdf_acroform(client: Client, template_path: Path, output_dir: Path) -> Path:
    today, _full_address, field_values = _text._build_b1_context(client)
    normalized_values = {
        key: _text._normalize_hebrew_value(value) if isinstance(value, str) else value
        for key, value in field_values.items()
    }

    output_path = _paths._build_b1_temp_output_path(client, output_dir)

    pdf_path = fill_form_auto(template_path, normalized_values, output_path)
    return pdf_path


def fill_b1_pdf(client: Client, template_path: Path, output_dir: Path) -> Path:
    font_name = _register_hebrew_font()

    today, full_address, field_values = _text._build_b1_context(client)

    hebrew_fields = {"ClientFirstName", "ClientLastName", "ClientAddress"}

    template_pdf = PdfReader(str(template_path))

    fallback_used = True

    for page_i, page in enumerate(template_pdf.pages):
        if not getattr(page, "Annots", None):
            continue

        fields_to_process = []
        for annotation in page.Annots:
            field_name = None
            if hasattr(annotation, "T") and annotation.T:
                field_name = str(annotation.T).strip("()")
            elif (
                hasattr(annotation, "Parent")
                and annotation.Parent
                and hasattr(annotation.Parent, "T")
                and annotation.Parent.T
            ):
                field_name = str(annotation.Parent.T).strip("()")

            if not field_name or field_name not in field_values:
                continue

            if hasattr(annotation, "Rect"):
                rect = annotation.Rect
                x1, y1, x2, y2 = map(float, rect)
                fields_to_process.append((field_name, x2, y1, y2))

        if not fields_to_process:
            continue

        fallback_used = False

        page_width = float(page.MediaBox[2])
        page_height = float(page.MediaBox[3])

        buf = io.BytesIO()
        c = canvas.Canvas(buf, pagesize=(page_width, page_height))
        c.setFont(font_name, 11)

        for field_name, x_right, y_bottom, y_top in fields_to_process:
            if field_name not in field_values:
                continue
            value = field_values[field_name]
            if field_name in hebrew_fields:
                value = _text._prepare_hebrew_for_pdf_drawing(value)
            tw = pdfmetrics.stringWidth(value, font_name, 11)
            c.drawString(x_right - tw - 2, y_bottom + 2, value)

        c.save()
        buf.seek(0)

        overlay = PdfReader(fdata=buf.getvalue()).pages[0]
        PageMerge(page).add(overlay).render()

    if fallback_used and template_pdf.pages:
        page = template_pdf.pages[0]
        page_width = float(page.MediaBox[2])
        page_height = float(page.MediaBox[3])

        buf = io.BytesIO()
        c = canvas.Canvas(buf, pagesize=(page_width, page_height))
        c.setFont(font_name, 11)

        c.drawString(page_width - 100, page_height - 50, today)

        full_name = f"{client.first_name or ''} {client.last_name or ''}".strip()
        visual_name = _text._prepare_hebrew_for_pdf_drawing(full_name)
        c.drawString(page_width / 2, page_height - 100, visual_name)

        c.drawString(page_width / 2, page_height - 130, client.id_number or "")

        visual_address = _text._prepare_hebrew_for_pdf_drawing(full_address)
        c.drawString(page_width / 2, page_height - 160, visual_address)

        c.save()
        buf.seek(0)

        overlay = PdfReader(fdata=buf.getvalue()).pages[0]
        PageMerge(page).add(overlay).render()

    output_path = _paths._build_b1_temp_output_path(client, output_dir)

    for page in template_pdf.pages:
        if getattr(page, "Annots", None):
            page.Annots = []

    acro = PdfName("AcroForm")
    if acro in template_pdf.Root:
        del template_pdf.Root[acro]

    writer = PdfWriter()
    for page in template_pdf.pages:
        writer.addpage(page)
    writer.write(str(output_path))

    return output_path


def generate_b1_pdf_for_client(client: Client) -> Tuple[bytes, str]:
    template_path, export_dir, filename = _paths._get_b1_generation_inputs(client)

    # Flatten B1 values into the page with an embedded Hebrew font. Live
    # AcroForm appearances are rendered left-to-right by some browser PDF
    # viewers, which reverses Hebrew in the signing/printing module.
    pdf_path = fill_b1_pdf(client, template_path, export_dir)
    final_path = export_dir / filename
    if pdf_path != final_path:
        if final_path.exists():
            final_path.unlink()
        pdf_path.rename(final_path)

    data = final_path.read_bytes()
    return data, filename


def generate_b1_pdf_for_client_overlay(client: Client) -> Tuple[bytes, str]:
    return generate_b1_pdf_for_client(client)
