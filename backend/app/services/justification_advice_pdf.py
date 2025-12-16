from __future__ import annotations

import logging
import os
import time
from pathlib import Path
from typing import Optional

from sqlalchemy.orm import Session

from app.models import Client
from app.services import justification_b1 as justification_b1_service
from app.services import justification_advice_render as _render
from app.utils.filepaths import get_client_justification_filename
from app.utils.fs import ensure_dir as _ensure_dir
from app.utils.paths import get_backend_root as _get_backend_root


logger = logging.getLogger("app.services.justification_advice")


_WKHTMLTOPDF_CMD: Optional[str] = None
_WKHTMLTOPDF_CHECKED = False


def _get_client_export_dir(client: Client) -> Path:
    return justification_b1_service._get_client_export_dir(client)


def _get_advice_pdf_output_path(client: Client) -> Path:
    filename = get_client_justification_filename(client)
    export_dir = _get_client_export_dir(client)
    return export_dir / filename


def _get_wkhtmltopdf_cmd() -> Optional[str]:
    """Find wkhtmltopdf command path once and cache it."""
    global _WKHTMLTOPDF_CMD, _WKHTMLTOPDF_CHECKED

    if _WKHTMLTOPDF_CHECKED:
        return _WKHTMLTOPDF_CMD

    import shutil

    backend_root = _get_backend_root()
    is_windows = os.name == "nt"

    # Try PATH first
    cmd = shutil.which("wkhtmltopdf")
    if cmd:
        _WKHTMLTOPDF_CMD = cmd
        _WKHTMLTOPDF_CHECKED = True
        return cmd

    # Try known paths
    candidate_paths: list[Path] = []
    if is_windows:
        candidate_paths.extend([
            backend_root / "bin" / "wkhtmltopdf.exe",
            Path(r"C:\\Program Files\\wkhtmltopdf\\bin\\wkhtmltopdf.exe"),
            Path(r"C:\\Program Files (x86)\\wkhtmltopdf\\bin\\wkhtmltopdf.exe"),
        ])
    else:
        candidate_paths.append(backend_root / "bin" / "wkhtmltopdf")

    for candidate in candidate_paths:
        if candidate.is_file():
            _WKHTMLTOPDF_CMD = str(candidate)
            break

    _WKHTMLTOPDF_CHECKED = True
    return _WKHTMLTOPDF_CMD


def _safe_unlink(path: Path) -> None:
    try:
        if path.is_file():
            path.unlink()
    except Exception:
        return


def generate_advice_pdf(html: str) -> Optional[bytes]:
    import subprocess
    from uuid import uuid4

    start_time = time.time()
    wkhtmltopdf_cmd = _get_wkhtmltopdf_cmd()
    if not wkhtmltopdf_cmd:
        logger.warning("[PDF-TIMING] wkhtmltopdf not found")
        return None

    options = {
        "page-size": "A4",
        "encoding": "UTF-8",
        "load-error-handling": "ignore",
    }

    backend_root = _get_backend_root()
    runtime_dir = backend_root / "advice_runtime"
    try:
        _ensure_dir(runtime_dir)
    except Exception:
        return None

    html_name = f"advice_{uuid4().hex}.html"
    pdf_name = html_name.replace(".html", ".pdf")
    input_path = runtime_dir / html_name
    output_path = runtime_dir / pdf_name

    try:
        input_path.write_text(html, encoding="utf-8")

        cmd = [wkhtmltopdf_cmd]
        for key, value in options.items():
            cmd.extend([f"--{key}", str(value)])
        cmd.extend([str(input_path), str(output_path)])

        result = subprocess.run(
            cmd,
            cwd=str(runtime_dir),
            capture_output=True,
            text=True,
        )

        if result.returncode != 0:
            return None

        if not output_path.is_file():
            return None

        pdf_bytes = output_path.read_bytes()
        elapsed = time.time() - start_time
        logger.info(f"[PDF-TIMING] Advice PDF generated in {elapsed:.2f}s, size={len(pdf_bytes)} bytes")
        return pdf_bytes
    except Exception as e:
        elapsed = time.time() - start_time
        logger.error(f"[PDF-TIMING] Advice PDF generation failed after {elapsed:.2f}s: {e}")
        return None
    finally:
        _safe_unlink(input_path)
        _safe_unlink(output_path)


def save_advice_pdf_for_client(db: Session, client: Client) -> None:
    save_path = _get_advice_pdf_output_path(client)

    html = _render.build_advice_html(db, client)
    pdf_bytes = generate_advice_pdf(html)
    if pdf_bytes is None:
        return

    try:
        save_path.write_bytes(pdf_bytes)
    except Exception:
        logger.exception(
            "[ADVICE] Failed to write advice PDF for client_id=%s to path %s",
            getattr(client, "id", None),
            save_path,
        )
