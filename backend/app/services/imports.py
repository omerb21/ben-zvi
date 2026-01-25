from typing import Dict, List
from pathlib import Path

from sqlalchemy.orm import Session

from app.schemas.justification import SavingProductCreate
from app.services.imports_crm import import_crm_from_excel as _import_crm_from_excel
from app.services.imports_saving_products import (
    import_saving_products_from_gemelnet_xml as _import_saving_products_from_gemelnet_xml,
    sync_saving_products_batch as _sync_saving_products_batch,
)


def import_crm_from_excel(
    db: Session,
    company_code: str,
    file_source: bytes | str | Path,
    snapshot_month: str | None = None,
    filename: str | None = None,
) -> Dict[str, int | str]:
    """Import CRM balances from Excel using the exact legacy Mini‑CRM logic.

    The function delegates Excel parsing and normalization to the old
    `mini_crm` ingestion pipeline (per‑provider loaders) and then maps the
    resulting rows into the unified SQLAlchemy models.
    """
    return _import_crm_from_excel(
        db,
        company_code,
        file_source,
        snapshot_month,
        filename,
    )


def import_saving_products_from_gemelnet_xml(db: Session, file_bytes: bytes) -> Dict[str, int]:
    return _import_saving_products_from_gemelnet_xml(db, file_bytes)


def sync_saving_products_batch(db: Session, products: List[SavingProductCreate]) -> Dict[str, int]:
    """Sync a batch of saving products (upsert)."""
    return _sync_saving_products_batch(db, products)
