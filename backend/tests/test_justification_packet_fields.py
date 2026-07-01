import base64
import io
from pathlib import Path

from pypdf import PdfReader
from pypdf import PdfWriter
from reportlab.pdfgen import canvas

from app.services.justification_forms_signatures import apply_signature_to_sig_fields
from app.services.justification_forms_signatures import count_signature_fields
from app.services.justification_forms_signatures import flatten_form_fields
from app.services.justification_packet_trim import refresh_edited_packet_from_base_if_possible
from app.services.justification_packet_parts_helpers import _append_parts_to_writer
from app.services.justification_packet_fields import rename_kit_specific_fields


def _build_pdf_with_signature_named_text_field() -> bytes:
    output = io.BytesIO()
    pdf = canvas.Canvas(output, pagesize=(595, 842))
    pdf.drawString(72, 780, "Kit document")
    pdf.acroForm.textfield(
        name="Signature1",
        x=300,
        y=120,
        width=180,
        height=40,
    )
    pdf.save()
    return output.getvalue()


def _build_reference_pdf_with_offset_sensitive_signature_fields() -> bytes:
    output = io.BytesIO()
    pdf = canvas.Canvas(output, pagesize=(595, 842))
    for page_label, x, y in [
        ("keep-first", 50, 110),
        ("remove-middle", 300, 110),
        ("keep-last", 50, 610),
    ]:
        pdf.drawString(72, 780, page_label)
        pdf.acroForm.textfield(
            name=f"{page_label}_Signature",
            x=x,
            y=y,
            width=120,
            height=35,
        )
        pdf.showPage()
    pdf.save()
    return output.getvalue()


def _build_source_pdf_without_signature_fields() -> bytes:
    output = io.BytesIO()
    pdf = canvas.Canvas(output, pagesize=(595, 842))
    for page_label in ["keep-first", "keep-last"]:
        pdf.drawString(72, 780, page_label)
        pdf.showPage()
    pdf.save()
    return output.getvalue()


def _signature_data_url() -> str:
    signature_path = Path(__file__).resolve().parents[1] / "app" / "static" / "signature.jpg"
    return "data:image/jpeg;base64," + base64.b64encode(signature_path.read_bytes()).decode("ascii")


def test_kit_signature_fields_are_prefixed_before_packet_merge():
    reader = PdfReader(io.BytesIO(_build_pdf_with_signature_named_text_field()))

    rename_kit_specific_fields(reader, "kit1_")

    fields = reader.get_fields() or {}
    assert "kit1_Signature1" in fields
    assert "Signature1" not in fields
    assert count_signature_fields(_write_reader(reader)) == 1


def test_packet_merge_preserves_duplicate_kit_signature_fields(tmp_path):
    kit_one = tmp_path / "kit_1_1.pdf"
    kit_two = tmp_path / "kit_1_2.pdf"
    kit_one.write_bytes(_build_pdf_with_signature_named_text_field())
    kit_two.write_bytes(_build_pdf_with_signature_named_text_field())

    writer = PdfWriter()

    assert _append_parts_to_writer(writer, [kit_one, kit_two]) is True

    output = io.BytesIO()
    writer.write(output)
    merged = output.getvalue()
    fields = PdfReader(io.BytesIO(merged)).get_fields() or {}

    assert "kit1_Signature1" in fields
    assert "kit2_Signature1" in fields
    assert count_signature_fields(merged) == 2


def test_flatten_removes_signature_widgets_from_page_annotations():
    source = _build_pdf_with_signature_named_text_field()

    flattened = flatten_form_fields(source)

    assert count_signature_fields(source) == 1
    assert count_signature_fields(flattened) == 0


def test_reference_signature_rects_follow_matching_pages_after_middle_pages_removed():
    signed = apply_signature_to_sig_fields(
        _build_source_pdf_without_signature_fields(),
        _signature_data_url(),
        reference_pdf_bytes=_build_reference_pdf_with_offset_sensitive_signature_fields(),
    )

    reader = PdfReader(io.BytesIO(signed))
    first_page_content = reader.pages[0].get_contents().get_data().decode("latin-1")

    assert "76.08247 110 cm" in first_page_content
    assert "326.08247 110 cm" not in first_page_content


def test_stale_edited_packet_is_refreshed_from_base_with_form_fields(tmp_path):
    base_path = tmp_path / "packet.pdf"
    edited_path = tmp_path / "packet_edited.pdf"
    base_path.write_bytes(_build_reference_pdf_with_offset_sensitive_signature_fields())

    base_reader = PdfReader(str(base_path))
    stale_writer = PdfWriter()
    stale_writer.add_page(base_reader.pages[0])
    stale_writer.add_page(base_reader.pages[2])
    with edited_path.open("wb") as f:
        stale_writer.write(f)

    assert PdfReader(str(edited_path)).get_fields() in (None, {})

    assert refresh_edited_packet_from_base_if_possible(base_path, edited_path) is True

    fields = PdfReader(str(edited_path)).get_fields() or {}
    assert "keep-first_Signature" in fields
    assert "keep-last_Signature" in fields
    assert count_signature_fields(edited_path.read_bytes()) == 2


def _write_reader(reader: PdfReader) -> bytes:
    output = io.BytesIO()
    writer = PdfWriter()
    writer.clone_document_from_reader(reader)
    writer.write(output)
    return output.getvalue()
