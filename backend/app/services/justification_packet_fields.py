from __future__ import annotations

from pathlib import Path

from pypdf import PdfReader, PdfWriter
from pypdf.generic import NameObject, TextStringObject


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


def get_acroform_fields(reader: PdfReader):
    root = reader.trailer.get("/Root")
    if root is None:
        return None

    acro = root.get("/AcroForm")
    if acro is None:
        return None

    fields = acro.get("/Fields")
    if not fields:
        return None

    return fields


def walk_acroform_field_array(field_array, visit_fn) -> None:
    for field_ref in field_array:
        field = field_ref.get_object()
        visit_fn(field)
        kids = field.get("/Kids")
        if kids:
            walk_acroform_field_array(kids, visit_fn)


def rename_kit_specific_fields(reader: PdfReader, prefix: str) -> None:
    fields = get_acroform_fields(reader)
    if not fields:
        return

    def _handle_field(field) -> None:
        name_obj = field.get("/T")
        if name_obj is not None:
            name_str = str(name_obj)
            if name_str.lower() in KIT_SPLIT_FIELD_NAMES_LOWER:
                new_name = TextStringObject(f"{prefix}{name_str}")
                field.update({NameObject("/T"): new_name})

    def _walk(field_array):  # type: ignore[no-redef]
        walk_acroform_field_array(field_array, _handle_field)

    _walk(fields)


def make_packet_field_names_unique_in_file(packet_path: Path) -> None:
    reader = PdfReader(str(packet_path))
    fields = get_acroform_fields(reader)
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

    def _handle_field(field) -> None:
        nonlocal counter
        name_obj = field.get("/T")
        if name_obj is not None:
            new_name = TextStringObject(f"field_{counter}")
            counter += 1
            field.update({NameObject("/T"): new_name})

    try:
        walk_acroform_field_array(fields_out, _handle_field)
    except Exception:
        return

    with packet_path.open("wb") as f:
        writer.write(f)
