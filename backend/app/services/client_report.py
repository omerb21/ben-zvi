from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from jinja2 import Environment, FileSystemLoader, select_autoescape
from sqlalchemy.orm import Session

from app.models.client import Client
from app.models.snapshot import Snapshot
from app.utils.source_names import get_source_display_name


def _select_report_date(db: Session, client_id: int, month: Optional[str]) -> Optional[str]:
    query = db.query(Snapshot.snapshot_date).filter(
        Snapshot.client_id == client_id,
        Snapshot.is_active.is_(True),
    )
    dates = [row[0] for row in query.all() if row[0]]
    if not dates:
        return None

    if month:
        # Expecting YYYY-MM, choose first day of that month
        month = month.strip()
        if len(month) == 7 and month[4] == "-":
            target_prefix = month
            candidates = [d for d in dates if isinstance(d, str) and d.startswith(target_prefix)]
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
        amount = float(s.amount or 0.0)
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
    base_dir = Path(__file__).resolve().parent.parent
    templates_dir = base_dir / "templates"
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
    return template.render(
        client=client,
        rows=rows,
        total_amount=total_amount,
        month=month,
        current_date=now.strftime("%d/%m/%Y"),
        current_datetime=now.strftime("%d/%m/%Y %H:%M"),
    )


def generate_client_report_pdf(
    html: str,
) -> Optional[bytes]:
    """Best-effort PDF generation from HTML.

    Returns PDF bytes if pdfkit is available and succeeds, otherwise None.
    """

    try:
        import pdfkit  # type: ignore
    except Exception:
        return None

    base_dir = Path(__file__).resolve().parent.parent
    css_path = base_dir / "static" / "report_client_pdf.css"

    options = {
        "page-size": "A4",
        "encoding": "UTF-8",
    }

    try:
        if css_path.is_file():
            pdf_bytes: bytes = pdfkit.from_string(
                html,
                False,
                options=options,
                css=str(css_path),
            )
        else:
            pdf_bytes = pdfkit.from_string(html, False, options=options)
        return pdf_bytes
    except Exception:
        return None
