from __future__ import annotations

from pathlib import Path
from typing import List

from pypdf import PdfWriter, PdfReader

from app.models import Client
from app.utils.fs import ensure_dir as _ensure_dir
from app.services import justification_packet_paths as _packet_paths


def _get_packet_source_path_or_raise(export_dir: Path, client_id: int) -> Path:
    base_packet_path, edited_packet_path = _packet_paths._get_packet_paths(export_dir, client_id)

    source_path = edited_packet_path if edited_packet_path.is_file() else base_packet_path
    if not source_path.is_file():
        raise ValueError("CLIENT_PACKET_PDF_NOT_FOUND")

    return source_path


def trim_client_packet_pdf(client: Client, pages_to_remove: List[int]) -> Path:
    export_dir = _packet_paths._get_export_dir(client)

    _base_packet_path, edited_packet_path = _packet_paths._get_packet_paths(export_dir, client.id)
    source_path = _get_packet_source_path_or_raise(export_dir, client.id)

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

    _ensure_dir(edited_packet_path.parent)
    with edited_packet_path.open("wb") as f:
        writer.write(f)

    return edited_packet_path
