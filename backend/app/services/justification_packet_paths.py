from __future__ import annotations

from pathlib import Path
from typing import List, Tuple

from app.models import Client
from app.services import justification_b1 as justification_b1_service
from app.utils.filepaths import get_client_justification_filename


def _get_export_dir(client: Client) -> Path:
    return justification_b1_service._get_client_export_dir(client)


def _get_packet_paths(export_dir: Path, client_id: int) -> Tuple[Path, Path]:
    base_packet_path = export_dir / f"packet_{client_id}.pdf"
    edited_packet_path = export_dir / f"packet_{client_id}_edited.pdf"
    return base_packet_path, edited_packet_path


def _get_kit_paths(export_dir: Path, client_id: int, new_product_id: int) -> Tuple[Path, Path]:
    edited_path = export_dir / f"kit_{new_product_id}_edited.pdf"
    auto_path = export_dir / f"kit_{client_id}_{new_product_id}.pdf"
    return edited_path, auto_path


def _get_advice_pdf_path(client: Client) -> Path:
    export_dir = _get_export_dir(client)
    filename = get_client_justification_filename(client)
    return export_dir / filename


def _build_b1_base_filename(client: Client) -> str:
    return f"יפוי כח עבור {client.first_name or ''} {client.last_name or ''}.pdf".strip()


def _get_b1_pdf_candidates(client: Client) -> List[Path]:
    export_dir = _get_export_dir(client)

    candidates: List[Path] = []
    edited_path = export_dir / "b1_edited.pdf"
    if edited_path.is_file():
        candidates.append(edited_path)

    base_filename = _build_b1_base_filename(client)
    if base_filename:
        base_path = export_dir / base_filename
        if base_path.is_file():
            candidates.append(base_path)

    return candidates
