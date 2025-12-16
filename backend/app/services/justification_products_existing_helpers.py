from typing import List, Dict, Any

from sqlalchemy.orm import Session

from app.models import SavingProduct, ExistingProduct
from app.schemas.justification import ExistingProductCreate, ExistingProductUpdate
from app.services import justification_products_utils as _products_utils
from app.utils.db import commit_and_refresh as _commit_and_refresh


def _existing_product_to_view_item(p: ExistingProduct) -> Dict[str, Any]:
    return {
        "id": p.id,
        "client_id": p.client_id,
        "fund_type": p.fund_type or "",
        "company_name": p.company_name or "",
        "fund_name": p.fund_name or "",
        "fund_code": p.fund_code or "",
        "yield_1yr": p.yield_1yr,
        "yield_3yr": p.yield_3yr,
        "personal_number": p.personal_number,
        "management_fee_balance": p.management_fee_balance,
        "management_fee_contributions": p.management_fee_contributions,
        "accumulated_amount": p.accumulated_amount,
        "employment_status": p.employment_status,
        "has_regular_contributions": p.has_regular_contributions,
        "is_virtual": False,
    }


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
    for incoming_key, attr_name in _EXISTING_PRODUCT_UPDATE_FIELD_MAP.items():
        if incoming_key in data:
            setattr(product, attr_name, data[incoming_key])


def _materialize_virtual_existing_product(
    db: Session,
    client_id: int,
    virtual_item: Dict[str, Any],
) -> ExistingProduct:
    existing_row = ExistingProduct(
        client_id=client_id,
        fund_type=virtual_item.get("fund_type") or "",
        company_name=virtual_item.get("company_name") or "",
        fund_name=virtual_item.get("fund_name") or "",
        fund_code=virtual_item.get("fund_code") or "",
        yield_1yr=virtual_item.get("yield_1yr"),
        yield_3yr=virtual_item.get("yield_3yr"),
        personal_number=virtual_item.get("personal_number"),
        management_fee_balance=virtual_item.get("management_fee_balance"),
        management_fee_contributions=virtual_item.get("management_fee_contributions"),
        accumulated_amount=virtual_item.get("accumulated_amount"),
        employment_status=virtual_item.get("employment_status"),
        has_regular_contributions=virtual_item.get("has_regular_contributions"),
    )
    db.add(existing_row)
    _commit_and_refresh(db, existing_row)
    return existing_row


def list_saving_products(db: Session) -> List[SavingProduct]:
    """Return all saving products ordered by company and fund name."""
    return db.query(SavingProduct).order_by(SavingProduct.company_name, SavingProduct.fund_name).all()


def list_existing_products_for_client(db: Session, client_id: int) -> List[ExistingProduct]:
    """Return all existing products for a specific client."""
    return (
        db.query(ExistingProduct)
        .filter(ExistingProduct.client_id == client_id)
        .order_by(ExistingProduct.company_name, ExistingProduct.fund_name)
        .all()
    )


def create_existing_product_for_client(
    db: Session,
    client_id: int,
    existing_in: ExistingProductCreate,
) -> ExistingProduct:
    """Create a manually-entered existing product for the given client."""

    product = ExistingProduct(
        client_id=client_id,
        **_products_utils._product_schema_to_model_kwargs(existing_in),
    )
    db.add(product)
    _commit_and_refresh(db, product)
    return product


def update_existing_product(
    db: Session,
    existing_product_id: int,
    existing_in: ExistingProductUpdate,
) -> ExistingProduct | None:
    """Update fields of an existing product by ID.

    Returns the updated product, or None if not found.
    """

    product = db.query(ExistingProduct).filter(ExistingProduct.id == existing_product_id).first()
    if not product:
        return None

    data = existing_in.model_dump(exclude_unset=True)

    _apply_existing_product_update(product, data)

    _commit_and_refresh(db, product)
    return product


def list_existing_products_view_for_client(
    db: Session,
    client_id: int,
) -> List[Dict[str, Any]]:
    """Return existing products for justification UI.

    Combines real ExistingProduct rows (manually entered / migrated).
    Previously derived virtual products from CRM snapshots, but this logic is now
    moved to on-demand sync (sync_client_products_from_crm).
    """

    real_products = list_existing_products_for_client(db, client_id)
    return [_existing_product_to_view_item(p) for p in real_products]
