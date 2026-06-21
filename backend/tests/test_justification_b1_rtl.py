import base64
from pathlib import Path

from pypdf import PdfReader

from app.models import Client
from app.services import justification_b1_fill, justification_b1_text, justification_forms


def test_hebrew_pdf_drawing_order_preserves_numbers_and_punctuation():
    visual = justification_b1_text._prepare_hebrew_for_pdf_drawing(
        "הגליל, 35, תל אביב"
    )

    assert visual == "ביבא לת ,35 ,לילגה"


def test_b1_generation_flattens_hebrew_fields(tmp_path):
    template = Path(__file__).resolve().parents[1] / "app" / "static" / "B1.pdf"
    client = Client(
        id=999,
        id_number="312937667",
        first_name="הילה",
        last_name="מרקוביץ",
        address_street="הגליל",
        address_house_number="35",
        address_city="תל אביב",
    )

    output = justification_b1_fill.fill_b1_pdf(client, template, tmp_path)
    reader = PdfReader(str(output))

    signature_fields = []
    for page in reader.pages:
        for annotation_ref in page.get("/Annots") or []:
            annotation = annotation_ref.get_object()
            if str(annotation.get("/FT")) == "/Sig":
                signature_fields.append(str(annotation.get("/T")))

    assert signature_fields == ["Signature1", "Signature2"]
    assert output.read_bytes().startswith(b"%PDF")


def test_b1_signature_uses_preserved_signature_rectangles(tmp_path, monkeypatch):
    template = Path(__file__).resolve().parents[1] / "app" / "static" / "B1.pdf"
    signature_path = Path(__file__).resolve().parents[1] / "app" / "static" / "signature.jpg"
    client = Client(id=999, first_name="הילה", last_name="מרקוביץ")
    output = justification_b1_fill.fill_b1_pdf(client, template, tmp_path)
    signature_data = "data:image/jpeg;base64," + base64.b64encode(
        signature_path.read_bytes()
    ).decode("ascii")

    def fail_if_fallback_is_used(*args, **kwargs):
        raise AssertionError("B1 signature unexpectedly used the bottom-right fallback")

    monkeypatch.setattr(
        justification_forms,
        "apply_overlay_to_pdf",
        fail_if_fallback_is_used,
    )

    signed = justification_forms.apply_signature_to_sig_fields(
        output.read_bytes(),
        signature_image_data=signature_data,
        reference_pdf_bytes=None,
    )

    assert signed != output.read_bytes()
