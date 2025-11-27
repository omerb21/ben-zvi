from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import base64
import os

from jinja2 import Environment, FileSystemLoader, select_autoescape
from sqlalchemy.orm import Session

from app.models import Client, ExistingProduct, NewProduct
from app.services import justification_b1 as justification_b1_service
from app.services import justification_forms as justification_forms_service
from app.services import justification_advice_tables as advice_tables_service


def _get_templates_env() -> Environment:
    base_dir = Path(__file__).resolve().parent.parent
    templates_dir = base_dir / "templates"
    env = Environment(
        loader=FileSystemLoader(str(templates_dir)),
        autoescape=select_autoescape(["html", "xml"]),
    )

    def _url_for(endpoint: str, filename: str) -> str:
        if endpoint == "static":
            return f"/static/{filename}"
        return filename

    env.globals["url_for"] = _url_for
    return env


def build_advice_html(db: Session, client: Client, include_print_button: bool = True) -> str:
    tables = advice_tables_service.build_tables(client)
    coverage_tables = advice_tables_service.build_coverage_tables(db, client, tables)

    client_view: Dict[str, Any] = {
        "first_name": client.first_name or "",
        "last_name": client.last_name or "",
        "national_id": client.id_number or "",
        "date_of_birth": client.birth_date,
        "marital_status": client.marital_status or "",
        "employment_status": None,
        "retirement_income": None,
        "insurance_needs": None,
        "existing_products": list(client.existing_products or []),
        "new_products": list(client.new_products or []),
    }

    env = _get_templates_env()
    template = env.get_template("advice_print.html")
    now = date.today()

    base_dir = Path(__file__).resolve().parent.parent
    logo_path = base_dir / "static" / "logo.png"
    logo_data_url = ""
    try:
        if logo_path.is_file():
            logo_bytes = logo_path.read_bytes()
            logo_b64 = base64.b64encode(logo_bytes).decode("ascii")
            logo_data_url = f"data:image/png;base64,{logo_b64}"
    except Exception:
        logo_data_url = ""

    primary_sign_path = base_dir / "static" / "signature.jpg"
    fallback_sign_path = base_dir / "static" / "sign.jpg"
    signature_data_url = ""
    try:
        sign_path = primary_sign_path if primary_sign_path.is_file() else fallback_sign_path
        if sign_path.is_file():
            sign_bytes = sign_path.read_bytes()
            sign_b64 = base64.b64encode(sign_bytes).decode("ascii")
            signature_data_url = f"data:image/jpeg;base64,{sign_b64}"
    except Exception:
        signature_data_url = ""

    # Client signature (from signing flow), if available as PNG in the
    # client's export directory. This is used to render the client's
    # signature image in the advice document at the designated locations.
    client_signature_data_url = ""
    try:
        export_dir = justification_b1_service._get_client_export_dir(client)
        client_sig_path = export_dir / "client_signature.png"
        if client_sig_path.is_file():
            client_sig_bytes = client_sig_path.read_bytes()
            client_sig_b64 = base64.b64encode(client_sig_bytes).decode("ascii")
            client_signature_data_url = f"data:image/png;base64,{client_sig_b64}"
    except Exception:
        client_signature_data_url = ""

    html = template.render(
        client=client_view,
        tables=tables,
        coverage_tables=coverage_tables,
        now=now,
        logo_data_url=logo_data_url,
        signature_data_url=signature_data_url,
        client_signature_data_url=client_signature_data_url,
        show_print_button=include_print_button,
    )
    return html


def generate_advice_pdf(html: str) -> Optional[bytes]:
    try:
        import shutil
        import subprocess
        from pathlib import Path
        from uuid import uuid4
    except Exception:
        return None

    options = {
        "page-size": "A4",
        "encoding": "UTF-8",
        "load-error-handling": "ignore",
    }

    # backend_root: .../backend
    backend_root = Path(__file__).resolve().parent.parent.parent
    runtime_dir = backend_root / "advice_runtime"
    try:
        runtime_dir.mkdir(parents=True, exist_ok=True)
    except Exception:
        return None

    is_windows = os.name == "nt"
    candidate_paths: list[Path] = []
    if is_windows:
        candidate_paths.extend(
            [
                backend_root / "bin" / "wkhtmltopdf.exe",
                Path(r"C:\\Program Files\\wkhtmltopdf\\bin\\wkhtmltopdf.exe"),
                Path(r"C:\\Program Files (x86)\\wkhtmltopdf\\bin\\wkhtmltopdf.exe"),
            ]
        )
    else:
        candidate_paths.append(backend_root / "bin" / "wkhtmltopdf")

    wkhtmltopdf_cmd = shutil.which("wkhtmltopdf")
    if not wkhtmltopdf_cmd:
        for candidate in candidate_paths:
            if candidate.is_file():
                wkhtmltopdf_cmd = str(candidate)
                break

    if not wkhtmltopdf_cmd:
        # Debug log for environments (e.g. Render) where wkhtmltopdf is
        # not available or not found in the expected locations.
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
        return pdf_bytes
    except Exception:
        return None
    finally:
        try:
            if input_path.is_file():
                input_path.unlink()
        except Exception:
            pass
        try:
            if output_path.is_file():
                output_path.unlink()
        except Exception:
            pass


def save_advice_pdf_for_client(db: Session, client: Client) -> None:
    """(Re)generate the advice PDF for a client and save it to the
    standard export path. If generation fails, this function does
    nothing and does not raise.

    Used after the client has signed, so that the advice PDF can
    include the client's signature image when available.
    """

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

    export_dir = justification_b1_service._get_client_export_dir(client)
    save_path = export_dir / filename

    html = build_advice_html(db, client)
    pdf_bytes = generate_advice_pdf(html)
    if pdf_bytes is None:
        try:
            print("[advice] save_advice_pdf_for_client: PDF generation failed for client", client.id)
        except Exception:
            pass
        return

    try:
        save_path.write_bytes(pdf_bytes)
    except Exception:
        pass
