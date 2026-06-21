from pathlib import Path

from pypdf import PdfReader

from app.models import Client
from app.services import justification_b1_fill, justification_b1_text


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

    assert not reader.get_fields()
    assert output.read_bytes().startswith(b"%PDF")
