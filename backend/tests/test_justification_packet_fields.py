import io

from pypdf import PdfReader
from pypdf import PdfWriter
from reportlab.pdfgen import canvas

from app.services.justification_forms_signatures import count_signature_fields
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


def _write_reader(reader: PdfReader) -> bytes:
    output = io.BytesIO()
    writer = PdfWriter()
    writer.clone_document_from_reader(reader)
    writer.write(output)
    return output.getvalue()
