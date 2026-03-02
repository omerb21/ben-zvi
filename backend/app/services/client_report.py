from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from jinja2 import Environment, FileSystemLoader, select_autoescape
from sqlalchemy.orm import Session

from app.models.client import Client
from app.models.snapshot import Snapshot
from app.utils.source_names import get_source_display_name
from app.utils.numbers import coerce_amount as _coerce_amount
from app.utils.paths import get_app_base_dir as _get_base_dir

def _month_prefix_or_none(month: Optional[str]) -> Optional[str]:
    if not month:
        return None
    normalized = month.strip()
    if len(normalized) == 7 and normalized[4] == "-":
        return normalized
    return None


def _select_report_date(db: Session, client_id: int, month: Optional[str]) -> Optional[str]:
    query = db.query(Snapshot.snapshot_date).filter(
        Snapshot.client_id == client_id,
        Snapshot.is_active.is_(True),
    )
    dates = [row[0] for row in query.all() if row[0]]
    if not dates:
        return None

    month_prefix = _month_prefix_or_none(month)
    if month_prefix:
        candidates = [d for d in dates if isinstance(d, str) and d.startswith(month_prefix)]
        if candidates:
            return sorted(candidates)[-1]
        # Fallback to latest date if format invalid or no matches

    # Default: latest snapshot date for this client
    return max(dates)


def _load_client(db: Session, client_id: int) -> Optional[Client]:
    return db.query(Client).filter(Client.id == client_id).first()


def build_client_report_data(
    db: Session,
    client_id: int,
    month: Optional[str] = None,
) -> Tuple[Dict[str, Any], List[Dict[str, Any]], float, Optional[str]]:
    client = _load_client(db, client_id)
    if not client:
        raise ValueError("Client not found")

    snapshot_date = _select_report_date(db, client_id, month)
    if not snapshot_date:
        # No balances for this client
        return {}, [], 0.0, month

    snapshots = (
        db.query(Snapshot)
        .filter(
            Snapshot.client_id == client_id,
            Snapshot.is_active.is_(True),
            Snapshot.snapshot_date == snapshot_date,
        )
        .order_by(Snapshot.amount.desc())
        .all()
    )

    rows: List[Dict[str, Any]] = []
    total_amount = 0.0

    for s in snapshots:
        amount = _coerce_amount(s.amount)
        total_amount += amount
        rows.append(
            {
                "fund_number": s.fund_number or "",
                "fund_name": s.fund_name or "",
                "fund_type": s.fund_type or "",
                "company": get_source_display_name(s.source or ""),
                "amount": amount,
                "snapshot_date": s.snapshot_date or "",
            }
        )

    client_data: Dict[str, Any] = {
        "full_name": client.full_name or "",
        "id_number": client.id_number or "",
        "phone": client.phone or "",
        "email": client.email or "",
    }

    # Use the effective month (YYYY-MM) for display
    report_month: Optional[str]
    if month and len(month) >= 7:
        report_month = month[:7]
    else:
        report_month = snapshot_date[:7] if snapshot_date and len(snapshot_date) >= 7 else None

    return client_data, rows, total_amount, report_month


def _get_templates_env() -> Environment:
    templates_dir = _get_base_dir() / "templates"
    env = Environment(
        loader=FileSystemLoader(str(templates_dir)),
        autoescape=select_autoescape(["html", "xml"]),
    )
    return env


def render_client_report_html(
    client: Dict[str, Any],
    rows: List[Dict[str, Any]],
    total_amount: float,
    month: Optional[str],
) -> str:
    env = _get_templates_env()
    template = env.get_template("report_client_pdf.html")

    now = datetime.now()
    html = template.render(
        client=client,
        rows=rows,
        total_amount=total_amount,
        month=month,
        current_date=now.strftime("%d/%m/%Y"),
        current_datetime=now.strftime("%d/%m/%Y %H:%M"),
    )
    # Embed CSS inline to avoid external file/network issues
    css_path = _get_base_dir() / "static" / "report_client_pdf.css"
    try:
        css_content = css_path.read_text(encoding="utf-8")
    except Exception:
        css_content = ""
    if css_content:
        html = f'<style>{css_content}</style>' + html
    return html


def generate_client_report_pdf(
    html: str,
) -> Optional[bytes]:
    """Generate PDF from HTML using wkhtmltopdf with proper options.

    Returns PDF bytes if wkhtmltopdf is available and succeeds, otherwise None.
    """

    try:
        import pdfkit  # type: ignore
    except Exception:
        return None

    options = {
        "page-size": "A4",
        "encoding": "UTF-8",
        "disable-smart-shrinking": "",
        "enable-local-file-access": "",
    }

    try:
        # Use wkhtmltopdf for styled PDF generation
        pdf_bytes = pdfkit.from_string(html, False, options=options)
        return pdf_bytes
    except Exception as exc:
        import logging
        logger = logging.getLogger(__name__)
        logger.warning("Failed to generate client report PDF with wkhtmltopdf: %s", exc)
        return None
