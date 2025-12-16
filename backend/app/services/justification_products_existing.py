from typing import List, Dict, Any

from sqlalchemy.orm import Session

from app.models import SavingProduct, ExistingProduct
from app.schemas.justification import ExistingProductCreate, ExistingProductUpdate
from app.services import justification_products_utils as _products_utils
from app.services import justification_products_existing_helpers as _helpers
from app.utils.db import commit_and_refresh as _commit_and_refresh


def _existing_product_to_view_item(p: ExistingProduct) -> Dict[str, Any]:
    return _helpers._existing_product_to_view_item(p)


_EXISTING_PRODUCT_UPDATE_FIELD_MAP: Dict[str, str] = {
    "fundType": "fund_type",
    "companyName": "company_name",
    "fundName": "fund_name",
    "fundCode": "fund_code",
    "yield1yr": "yield_1yr",
    "yield3yr": "yield_3yr",
    "personalNumber": "personal_number",
    "managementFeeBalance": "management_fee_balance",
    "managementFeeContributions": "management_fee_contributions",
    "accumulatedAmount": "accumulated_amount",
    "employmentStatus": "employment_status",
    "hasRegularContributions": "has_regular_contributions",
}


def _apply_existing_product_update(product: ExistingProduct, data: Dict[str, Any]) -> None:
    return _helpers._apply_existing_product_update(product, data)


def _materialize_virtual_existing_product(
    db: Session,
    client_id: int,
    virtual_item: Dict[str, Any],
) -> ExistingProduct:
    return _helpers._materialize_virtual_existing_product(db, client_id, virtual_item)


def list_saving_products(db: Session) -> List[SavingProduct]:
    """Return all saving products ordered by company and fund name."""
    return _helpers.list_saving_products(db)


def list_existing_products_for_client(db: Session, client_id: int) -> List[ExistingProduct]:
    """Return all existing products for a specific client."""
    return _helpers.list_existing_products_for_client(db, client_id)


def create_existing_product_for_client(
    db: Session,
    client_id: int,
    existing_in: ExistingProductCreate,
) -> ExistingProduct:
    """Create a manually-entered existing product for the given client."""
    return _helpers.create_existing_product_for_client(db, client_id, existing_in)


def update_existing_product(
    db: Session,
    existing_product_id: int,
    existing_in: ExistingProductUpdate,
) -> ExistingProduct | None:
    """Update fields of an existing product by ID.

    Returns the updated product, or None if not found.
    """

    return _helpers.update_existing_product(db, existing_product_id, existing_in)


def list_existing_products_view_for_client(
    db: Session,
    client_id: int,
) -> List[Dict[str, Any]]:
    """Return existing products for justification UI.

    Combines real ExistingProduct rows (manually entered / migrated).
    Previously derived virtual products from CRM snapshots, but this logic is now
    moved to on-demand sync (sync_client_products_from_crm).
    """

    return _helpers.list_existing_products_view_for_client(db, client_id)
