from __future__ import annotations

from pathlib import Path
from typing import List

from pypdf import PdfWriter, PdfReader

from app.models import Client
from app.utils.fs import ensure_dir as _ensure_dir
from app.services import justification_packet_paths as _packet_paths


def _page_content_fingerprint(page) -> tuple:
    content_bytes = []
    contents = page.get("/Contents")
    if contents:
        content_items = contents if isinstance(contents, list) else [contents]
        for item in content_items:
            try:
                obj = item.get_object() if hasattr(item, "get_object") else item
                if hasattr(obj, "get_data"):
                    content_bytes.append(obj.get_data())
                else:
                    content_bytes.append(repr(obj).encode("utf-8", errors="ignore"))
            except Exception:
                content_bytes.append(repr(item).encode("utf-8", errors="ignore"))

    return (
        str(page.mediabox),
        str(page.get("/Rotate") or 0),
        b"\n".join(content_bytes),
    )


def _match_pages_by_content(source_reader: PdfReader, reference_reader: PdfReader) -> list[int] | None:
    reference_pages_by_fingerprint: dict[tuple, list[int]] = {}
    for ref_idx, page in enumerate(reference_reader.pages):
        fingerprint = _page_content_fingerprint(page)
        reference_pages_by_fingerprint.setdefault(fingerprint, []).append(ref_idx)

    matched_pages: list[int] = []
    for page in source_reader.pages:
        fingerprint = _page_content_fingerprint(page)
        matches = reference_pages_by_fingerprint.get(fingerprint) or []
        if not matches:
            return None
        matched_pages.append(matches.pop(0))

    return matched_pages


def _write_selected_reference_pages(reference_reader: PdfReader, page_indices: list[int], out_path: Path) -> None:
    writer = PdfWriter()
    writer.append(reference_reader, pages=page_indices)
    _ensure_dir(out_path.parent)
    with out_path.open("wb") as f:
        writer.write(f)


def refresh_edited_packet_from_base_if_possible(base_packet_path: Path, edited_packet_path: Path) -> bool:
    if not base_packet_path.is_file() or not edited_packet_path.is_file():
        return False

    try:
        base_reader = PdfReader(str(base_packet_path))
        edited_reader = PdfReader(str(edited_packet_path))
        matched_pages = _match_pages_by_content(edited_reader, base_reader)
        if matched_pages is None:
            return False
        _write_selected_reference_pages(base_reader, matched_pages, edited_packet_path)
        return True
    except Exception:
        return False


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

    pages_to_keep = [
        index
        for index in range(total_pages)
        if index not in normalized_remove
    ]

    if not pages_to_keep:
        raise ValueError("NO_PAGES_LEFT_AFTER_TRIM")

    _write_selected_reference_pages(reader, pages_to_keep, edited_packet_path)

    return edited_packet_path
