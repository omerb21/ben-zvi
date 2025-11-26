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


def _get_base_dir() -> Path:
    return Path(__file__).resolve().parent.parent


def _get_b1_template_path() -> Path:
    base_dir = _get_base_dir()
    return base_dir / "static" / "B1.pdf"


def _get_client_export_dir(client: Client) -> Path:
    base_dir = _get_base_dir()
    client_dir_name = f"{client.id}_{client.first_name or ''}_{client.last_name or ''}"
    export_dir = base_dir / "exports" / client_dir_name
    export_dir.mkdir(parents=True, exist_ok=True)
    return export_dir


def _register_hebrew_font() -> str:
    candidates = [
        r"C:\\Windows\\Fonts\\arial.ttf",
        r"/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]
    for path in candidates:
        if os.path.exists(path):
            pdfmetrics.registerFont(TTFont("Heb", path))
            return "Heb"
    raise AssertionError("Hebrew TTF font not found")


def _contains_hebrew(text: str) -> bool:
    for ch in text:
        if "\u0590" <= ch <= "\u05FF":
            return True
    return False


def _normalize_hebrew_value(value: str) -> str:
    if not isinstance(value, str):
        return value
    # For B1 we keep Hebrew text in logical order and let the PDF viewer
    # handle right-to-left layout. No reversal or embedding marks here.
    return value


def fill_b1_pdf_acroform(client: Client, template_path: Path, output_dir: Path) -> Path:
    today = datetime.date.today().strftime("%d/%m/%Y")

    address_parts = []
    if client.address_street:
        address_parts.append(client.address_street)
    if client.address_house_number:
        house = str(client.address_house_number)
        if client.address_apartment:
            apartment = str(client.address_apartment)
            address_parts.append(f"{house}/{apartment}")
        else:
            address_parts.append(house)
    if client.address_city:
        address_parts.append(client.address_city)

    full_address = ", ".join(filter(None, address_parts))

    field_values = {
        "Today": today,
        "ClientFirstName": client.first_name or "",
        "ClientLastName": client.last_name or "",
        "ClientID": client.id_number or "",
        "ClientAddress": full_address,
    }

    normalized_values = {}
    for key, value in field_values.items():
        if isinstance(value, str):
            normalized_values[key] = _normalize_hebrew_value(value)
        else:
            normalized_values[key] = value

    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    output_filename = f"B1_filled_{client.id}_{timestamp}.pdf"
    output_path = output_dir / output_filename

    pdf_path = fill_form_auto(template_path, normalized_values, output_path)
    return pdf_path


def fill_b1_pdf(client: Client, template_path: Path, output_dir: Path) -> Path:
    font_name = _register_hebrew_font()

    today = datetime.date.today().strftime("%d/%m/%Y")

    address_parts = []
    if client.address_street:
        address_parts.append(client.address_street)
    if client.address_house_number:
        house = str(client.address_house_number)
        if client.address_apartment:
            apartment = str(client.address_apartment)
            address_parts.append(f"{house}/{apartment}")
        else:
            address_parts.append(house)
    if client.address_city:
        address_parts.append(client.address_city)

    full_address = ", ".join(filter(None, address_parts))

    field_values = {
        "Today": today,
        "ClientFirstName": client.first_name or "",
        "ClientLastName": client.last_name or "",
        "ClientID": client.id_number or "",
        "ClientAddress": full_address,
    }

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
                value = value[::-1]
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
        reversed_name = full_name[::-1]
        c.drawString(page_width / 2, page_height - 100, reversed_name)

        c.drawString(page_width / 2, page_height - 130, client.id_number or "")

        reversed_address = full_address[::-1]
        c.drawString(page_width / 2, page_height - 160, reversed_address)

        c.save()
        buf.seek(0)

        overlay = PdfReader(fdata=buf.getvalue()).pages[0]
        PageMerge(page).add(overlay).render()

    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    output_filename = f"B1_filled_{client.id}_{timestamp}.pdf"
    output_path = output_dir / output_filename

    # Flatten the form by removing annotations and AcroForm so that
    # only the drawn overlay text remains.
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
    template_path = _get_b1_template_path()
    if not template_path.is_file():
        raise FileNotFoundError("B1 template not found")

    export_dir = _get_client_export_dir(client)

    pdf_path = fill_b1_pdf_acroform(client, template_path, export_dir)

    filename = f"יפוי כח עבור {client.first_name or ''} {client.last_name or ''}.pdf".strip()
    final_path = export_dir / filename
    if pdf_path != final_path:
        if final_path.exists():
            final_path.unlink()
        pdf_path.rename(final_path)

    data = final_path.read_bytes()
    return data, filename


def generate_b1_pdf_for_client_overlay(client: Client) -> Tuple[bytes, str]:
    template_path = _get_b1_template_path()
    if not template_path.is_file():
        raise FileNotFoundError("B1 template not found")

    export_dir = _get_client_export_dir(client)

    # Use the overlay-based filler which reverses Hebrew visually and flattens the form.
    pdf_path = fill_b1_pdf(client, template_path, export_dir)

    filename = f"יפוי כח עבור {client.first_name or ''} {client.last_name or ''}.pdf".strip()
    data = Path(pdf_path).read_bytes()
    return data, filename
