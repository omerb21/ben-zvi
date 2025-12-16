from typing import List, Dict, Any

from sqlalchemy.orm import Session

from app.models import SavingProduct, ExistingProduct, NewProduct, FormInstance
from app.schemas.justification import (
    NewProductCreate,
    FormInstanceCreate,
    ExistingProductCreate,
    ExistingProductUpdate,
)
from app.utils.db import commit_and_refresh as _commit_and_refresh
from app.utils.strings import strip_or_empty as _strip_or_empty
from app.services import justification_products_existing as _products_existing
from app.services import justification_products_maintenance as _products_maintenance
from app.services import justification_products_new as _products_new
from app.services import justification_products_utils as _products_utils
from app.services.justification_crm_sync import (
    sync_client_products_from_crm as _sync_client_products_from_crm,
)


def _product_schema_to_model_kwargs(product_in) -> Dict[str, Any]:
    return _products_utils._product_schema_to_model_kwargs(product_in)


def _existing_product_to_view_item(p: ExistingProduct) -> Dict[str, Any]:
    return _products_existing._existing_product_to_view_item(p)


_EXISTING_PRODUCT_UPDATE_FIELD_MAP: Dict[str, str] = _products_existing._EXISTING_PRODUCT_UPDATE_FIELD_MAP


def _apply_existing_product_update(product: ExistingProduct, data: Dict[str, Any]) -> None:
    return _products_existing._apply_existing_product_update(product, data)


def _find_existing_view_item_by_id(
    existing_view_items: List[Dict[str, Any]],
    target_id: int,
) -> Dict[str, Any] | None:
    return _products_utils._find_existing_view_item_by_id(existing_view_items, target_id)


def _materialize_virtual_existing_product(
    db: Session,
    client_id: int,
    virtual_item: Dict[str, Any],
) -> ExistingProduct:
    return _products_existing._materialize_virtual_existing_product(db, client_id, virtual_item)


def list_saving_products(db: Session) -> List[SavingProduct]:
    """Return all saving products ordered by company and fund name."""
    return _products_existing.list_saving_products(db)


def list_existing_products_for_client(db: Session, client_id: int) -> List[ExistingProduct]:
    """Return all existing products for a specific client."""
    return _products_existing.list_existing_products_for_client(db, client_id)


def create_existing_product_for_client(
    db: Session,
    client_id: int,
    existing_in: ExistingProductCreate,
) -> ExistingProduct:
    """Create a manually-entered existing product for the given client."""

    return _products_existing.create_existing_product_for_client(db, client_id, existing_in)


def update_existing_product(
    db: Session,
    existing_product_id: int,
    existing_in: ExistingProductUpdate,
) -> ExistingProduct | None:
    """Update fields of an existing product by ID.

    Returns the updated product, or None if not found.
    """

    return _products_existing.update_existing_product(db, existing_product_id, existing_in)


def list_existing_products_view_for_client(
    db: Session,
    client_id: int,
) -> List[Dict[str, Any]]:
    """Return existing products for justification UI.

    Combines real ExistingProduct rows (manually entered / migrated).
    Previously derived virtual products from CRM snapshots, but this logic is now
    moved to on-demand sync (sync_client_products_from_crm).
    """

    return _products_existing.list_existing_products_view_for_client(db, client_id)


def list_new_products_for_client(db: Session, client_id: int) -> List[NewProduct]:
    """Return all new products for a specific client."""
    return _products_new.list_new_products_for_client(db, client_id)


def create_new_product_for_client(
    db: Session,
    client_id: int,
    new_product_in: NewProductCreate,
) -> NewProduct:
    """Create a new product for the given client."""
    return _products_new.create_new_product_for_client(db, client_id, new_product_in)


def list_form_instances_for_new_product(db: Session, new_product_id: int) -> List[FormInstance]:
    """Return all form instances for a specific new product."""
    return _products_new.list_form_instances_for_new_product(db, new_product_id)


def create_form_instance_for_new_product(
    db: Session,
    new_product_id: int,
    form_in: FormInstanceCreate,
) -> FormInstance:
    """Create a new form instance for the given new product."""
    return _products_new.create_form_instance_for_new_product(db, new_product_id, form_in)


def _get_by_id(db: Session, model, row_id: int):
    return _products_maintenance._get_by_id(db, model, row_id)


def _delete_by_id(db: Session, model, row_id: int) -> bool:
    return _products_maintenance._delete_by_id(db, model, row_id)


def delete_new_product(db: Session, new_product_id: int) -> bool:
    """Delete a new product by ID. Returns True if deleted, False if not found."""
    return _products_maintenance.delete_new_product(db, new_product_id)


def delete_existing_product(db: Session, existing_product_id: int) -> bool:
    """Delete an existing product by ID. Returns True if deleted, False if not found."""
    return _products_maintenance.delete_existing_product(db, existing_product_id)


def delete_form_instance(db: Session, form_instance_id: int) -> bool:
    """Delete a form instance by ID. Returns True if deleted, False if not found."""
    return _products_maintenance.delete_form_instance(db, form_instance_id)


def clear_justification_data(db: Session) -> dict[str, int]:
    """Clear justification-specific data without deleting clients.

    This removes all form instances, new products, existing products and saving
    products, in that order, to respect foreign key relationships.
    """

    return _products_maintenance.clear_justification_data(db)


def sync_client_products_from_crm(db: Session, client_id: int) -> int:
    """Sync CRM snapshots to existing products for a client.

    This takes the latest snapshots, groups them by personal number (canonicalization),
    matches them with market products, and then upserts them into the ExistingProduct table.
    """
    return _products_maintenance.sync_client_products_from_crm(db, client_id)
