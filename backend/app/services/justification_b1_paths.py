from __future__ import annotations

from pathlib import Path

from app.models import Client
from app.utils.paths import get_app_base_dir as _get_base_dir
from app.utils.fs import ensure_dir as _ensure_dir


def _get_b1_template_path() -> Path:
    base_dir = _get_base_dir()
    return base_dir / "static" / "B1.pdf"


def _get_b1_template_path_or_raise() -> Path:
    template_path = _get_b1_template_path()
    if not template_path.is_file():
        raise FileNotFoundError("B1 template not found")
    return template_path


def _get_client_export_dir(client: Client) -> Path:
    base_dir = _get_base_dir()
    client_dir_name = f"{client.id}_{client.first_name or ''}_{client.last_name or ''}"
    export_dir = base_dir / "exports" / client_dir_name
    _ensure_dir(export_dir)
    return export_dir


def _build_b1_temp_output_filename(client: Client, timestamp: str) -> str:
    return f"B1_filled_{client.id}_{timestamp}.pdf"


def _get_b1_final_filename(client: Client) -> str:
    return f"יפוי כח עבור {client.first_name or ''} {client.last_name or ''}.pdf".strip()


def _timestamp_str() -> str:
    import datetime

    return datetime.datetime.now().strftime("%Y%m%d_%H%M%S")


def _build_b1_temp_output_path(client: Client, output_dir: Path) -> Path:
    timestamp = _timestamp_str()
    output_filename = _build_b1_temp_output_filename(client, timestamp)
    return output_dir / output_filename


def _get_b1_generation_inputs(client: Client) -> tuple[Path, Path, str]:
    template_path = _get_b1_template_path_or_raise()
    export_dir = _get_client_export_dir(client)
    filename = _get_b1_final_filename(client)
    return template_path, export_dir, filename
