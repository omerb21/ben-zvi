from __future__ import annotations

from pathlib import Path
from typing import List, Tuple

from sqlalchemy.orm import Session
from pypdf import PdfWriter, PdfReader
from pypdf.generic import NameObject, TextStringObject

from app.models import Client
from app.services import justification as justification_service
from app.services import justification_advice as justification_advice_service
from app.services import justification_b1 as justification_b1_service
from app.services import justification_kits as justification_kits_service


def _get_export_dir(client: Client) -> Path:
    return justification_b1_service._get_client_export_dir(client)


def _get_advice_pdf_path(client: Client) -> Path:
    export_dir = _get_export_dir(client)

    display_name = client.full_name or client.id_number or f"client_{client.id}"
    safe_name_chars: List[str] = []
    for ch in display_name:
        if ch.isalnum() or "\u0590" <= ch <= "\u05FF":
            safe_name_chars.append(ch)
        else:
            safe_name_chars.append("_")
    safe_name = "".join(safe_name_chars)

    ascii_safe_name_chars: List[str] = []
    for ch in safe_name:
        if ch.isascii() and (ch.isalnum() or ch in "-_"):
            ascii_safe_name_chars.append(ch)
        else:
            ascii_safe_name_chars.append("_")
    ascii_safe_name = "".join(ascii_safe_name_chars) or f"client_{client.id}"

    filename = f"justification_{ascii_safe_name}.pdf"
    return export_dir / filename


def _get_b1_pdf_candidates(client: Client) -> List[Path]:
    export_dir = _get_export_dir(client)

    candidates: List[Path] = []
    edited_path = export_dir / "b1_edited.pdf"
    if edited_path.is_file():
        candidates.append(edited_path)

    base_filename = f"יפוי כח עבור {client.first_name or ''} {client.last_name or ''}.pdf".strip()
    if base_filename:
        base_path = export_dir / base_filename
        if base_path.is_file():
            candidates.append(base_path)

    return candidates


def _get_kit_pdf_paths_for_client(
    db: Session,
    client: Client,
) -> List[Path]:
    """החזרת קובצי קיט קיימים ללקוח, אחד לכל קופה קיימת לכל היותר.

    הלוגיקה מקבילה ל-handleGenerateAllKits בפרונט: לכל existing_product_id
    ייבחר מוצר חדש אחד בלבד (לפי מזהה מוצר חדש קטן יותר), ומוצרים חדשים
    ללא existing_product_id ייכללו תמיד. עבור כל מוצר ננסה קודם קובץ ערוך,
    ואז קובץ אוטומטי, אם הם קיימים בתיקיית הלקוח.
    """

    export_dir = _get_export_dir(client)

    new_products = justification_service.list_new_products_for_client(db, client.id)
    sorted_products = sorted(new_products, key=lambda p: getattr(p, "id", 0))

    seen_existing_ids = set()
    target_products = []

    for product in sorted_products:
        existing_id = getattr(product, "existing_product_id", None)
        if existing_id is not None:
            if existing_id in seen_existing_ids:
                continue
            seen_existing_ids.add(existing_id)
            target_products.append(product)
        else:
            target_products.append(product)

    kit_paths: List[Path] = []

    for product in target_products:
        new_product_id = product.id
        edited_path = export_dir / f"kit_{new_product_id}_edited.pdf"
        auto_path = export_dir / f"kit_{client.id}_{new_product_id}.pdf"

        if edited_path.is_file():
            kit_paths.append(edited_path)
        elif auto_path.is_file():
            kit_paths.append(auto_path)

    return kit_paths


KIT_SPLIT_FIELD_NAMES_LOWER = {
    "employ",
    "indipendent",
    "baalshlita",
    "indiploy",
    "dmnsum",
    "fund_code",
    "fund_name",
    "company_name",
    "kupacode",
    "depno",
    "depyes",
    "personal_number",
    "group3",
    "group29",
    "group30",
    "group31",
    "text6",
    "text8",
    "per1",
    "per2",
    "per3",
    "per4",
    "per5",
    "per6",
    "per7",
    "per8",
    "per9",
    "per10",
    "per11",
    "per12",
    "per13",
    "per14",
    "per15",
    "group4",
    "check box2",
    "check box3",
    "check box4",
    "check box5",
    "check box6",
    "check box7",
    "check box8",
    "check box9",
    "check box10",
    "check box11",
    "check box12",
    "check box13",
    "check box14",
    "check box15",
    "check box18",
    "code",
    "chosen",
}


def _rename_kit_specific_fields(reader: PdfReader, prefix: str) -> None:
    root = reader.trailer.get("/Root")
    if root is None:
        return

    acro = root.get("/AcroForm")
    if acro is None:
        return

    fields = acro.get("/Fields")
    if not fields:
        return

    def _walk(field_array):  # type: ignore[no-redef]
        for field_ref in field_array:
            field = field_ref.get_object()
            name_obj = field.get("/T")
            if name_obj is not None:
                name_str = str(name_obj)
                if name_str.lower() in KIT_SPLIT_FIELD_NAMES_LOWER:
                    new_name = TextStringObject(f"{prefix}{name_str}")
                    field.update({NameObject("/T"): new_name})
            kids = field.get("/Kids")
            if kids:
                _walk(kids)

    _walk(fields)


def generate_client_packet_pdf(
    db: Session,
    client: Client,
    generate_missing: bool = True,
) -> Tuple[bytes, str]:
    """Generate a combined packet PDF for the client.

    The packet contains, בסדר הבא:
    1. מסמך הנמקה (אם קיים / הופק).
    2. טופס B1 (ערוך אם קיים, אחרת בסיסי אם קיים / הופק).
    3. כל קיטי ההצטרפות לפי סדר מזהה המוצר החדש, כשהעדפה ראשונה היא לגרסה ערוכה.

    כל הקבצים נלקחים מתיקיית הייצוא של הלקוח, ובמידת הצורך מופקים מחדש.
    התוצאה נכתבת לקובץ packet_<client_id>.pdf בתיקיית הייצוא ומוחזרת כ‑bytes.
    """

    export_dir = _get_export_dir(client)
    export_dir.mkdir(parents=True, exist_ok=True)

    parts: List[Path] = []

    # 1. Advice PDF
    advice_path = _get_advice_pdf_path(client)
    if advice_path.is_file():
        parts.append(advice_path)
    elif generate_missing:
        # If the advice PDF is missing, try to (re)generate it now so that
        # the packet always includes the latest advice document when
        # requested via generate=1 or from the signing flow.
        try:
            justification_advice_service.save_advice_pdf_for_client(db, client)
        except Exception:
            pass

        if advice_path.is_file():
            parts.append(advice_path)

    # 2. B1 (edited/base) – לוקחים גרסה אחת בלבד לחבילה, אם קיימת
    b1_candidates = _get_b1_pdf_candidates(client)
    if b1_candidates:
        # העדפה ראשונה לערוך (edited), אחרת בסיסי
        parts.append(b1_candidates[0])

    # 3. Kits – קיטים קיימים בלבד, אחד לכל קופה קיימת לכל היותר
    kit_paths = _get_kit_pdf_paths_for_client(db, client)
    parts.extend(kit_paths)

    # אם אין אף מסמך – זו שגיאה לוגית
    if not parts:
        raise ValueError("NO_PDFS_FOR_CLIENT_PACKET")

    packet_filename = f"packet_{client.id}.pdf"
    packet_path = export_dir / packet_filename

    writer = PdfWriter()
    has_pages = False
    kit_index = 1
    for pdf_path in parts:
        try:
            reader = PdfReader(str(pdf_path))
        except Exception:
            # אם קובץ אחד בעייתי, לא מפילים את כל תהליך יצירת החבילה
            continue

        is_kit = pdf_path.name.startswith("kit_")

        if is_kit:
            try:
                _rename_kit_specific_fields(reader, f"kit{kit_index}_")
            except Exception:
                pass
            kit_index += 1

        try:
            writer.append(reader)
            has_pages = True
        except Exception:
            # אם קובץ אחד בעייתי, לא מפילים את כל תהליך יצירת החבילה
            continue

    # אם משום מה לא נוספה אף עמוד, נכשלים באופן מפורש
    if not has_pages:
        raise ValueError("NO_PAGES_IN_CLIENT_PACKET")

    try:
        writer.write(str(packet_path))
    except Exception as exc:
        raise ValueError(f"FAILED_TO_WRITE_PACKET:{exc}")

    _debug_dump_packet_fields(packet_path)

    data = packet_path.read_bytes()
    return data, packet_filename


def _make_packet_field_names_unique_in_file(packet_path: Path) -> None:
    reader = PdfReader(str(packet_path))
    root = reader.trailer.get("/Root")
    if root is None:
        return

    acro = root.get("/AcroForm")
    if acro is None:
        return

    fields = acro.get("/Fields")
    if not fields:
        return

    writer = PdfWriter()
    writer.clone_document_from_reader(reader)

    acro_out = writer._root_object.get("/AcroForm")
    if acro_out is None:
        return

    fields_out = acro_out.get("/Fields")
    if not fields_out:
        return

    counter = 1

    def _walk(field_array):  # type: ignore[no-redef]
        nonlocal counter
        for field_ref in field_array:
            field = field_ref.get_object()
            name_obj = field.get("/T")
            if name_obj is not None:
                new_name = TextStringObject(f"field_{counter}")
                counter += 1
                field.update({NameObject("/T"): new_name})
            kids = field.get("/Kids")
            if kids:
                _walk(kids)

    try:
        _walk(fields_out)
    except Exception:
        return

    with packet_path.open("wb") as f:
        writer.write(f)


def _debug_dump_packet_fields(packet_path: Path) -> None:
    try:
        reader = PdfReader(str(packet_path))
        fields = reader.get_fields()
    except Exception:
        return

    if not fields:
        return

    debug_path = packet_path.with_name(f"{packet_path.stem}_debug_fields.txt")

    try:
        lines = []
        for name in fields.keys():
            lines.append(str(name))
        content = "\n".join(lines)
        debug_path.write_text(content, encoding="utf-8")
    except Exception:
        return


def trim_client_packet_pdf(client: Client, pages_to_remove: List[int]) -> Path:
    export_dir = _get_export_dir(client)
    base_packet_path = export_dir / f"packet_{client.id}.pdf"
    edited_packet_path = export_dir / f"packet_{client.id}_edited.pdf"

    source_path = edited_packet_path if edited_packet_path.is_file() else base_packet_path
    if not source_path.is_file():
        raise ValueError("CLIENT_PACKET_PDF_NOT_FOUND")

    reader = PdfReader(str(source_path))
    total_pages = len(reader.pages)

    normalized_remove = {
        p - 1
        for p in pages_to_remove
        if isinstance(p, int) and 1 <= p <= total_pages
    }

    writer = PdfWriter()
    for index in range(total_pages):
        if index not in normalized_remove:
            writer.add_page(reader.pages[index])

    if not writer.pages:
        raise ValueError("NO_PAGES_LEFT_AFTER_TRIM")

    edited_packet_path.parent.mkdir(parents=True, exist_ok=True)
    with edited_packet_path.open("wb") as f:
        writer.write(f)

    return edited_packet_path
