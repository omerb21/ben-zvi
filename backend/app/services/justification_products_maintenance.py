from sqlalchemy.orm import Session

from app.models import SavingProduct, ExistingProduct, NewProduct, FormInstance
from app.services.justification_crm_sync import sync_client_products_from_crm as _sync_client_products_from_crm


def _get_by_id(db: Session, model, row_id: int):
    return db.query(model).filter(model.id == row_id).first()


def _delete_by_id(db: Session, model, row_id: int) -> bool:
    row = _get_by_id(db, model, row_id)
    if not row:
        return False

    db.delete(row)
    db.commit()
    return True


def delete_new_product(db: Session, new_product_id: int) -> bool:
    """Delete a new product by ID. Returns True if deleted, False if not found."""
    return _delete_by_id(db, NewProduct, new_product_id)


def delete_existing_product(db: Session, existing_product_id: int) -> bool:
    """Delete an existing product by ID. Returns True if deleted, False if not found."""
    return _delete_by_id(db, ExistingProduct, existing_product_id)


def delete_form_instance(db: Session, form_instance_id: int) -> bool:
    """Delete a form instance by ID. Returns True if deleted, False if not found."""
    return _delete_by_id(db, FormInstance, form_instance_id)


def clear_justification_data(db: Session) -> dict[str, int]:
    """Clear justification-specific data without deleting clients.

    This removes all form instances, new products, existing products and saving
    products, in that order, to respect foreign key relationships.
    """

    deleted_form_instances = db.query(FormInstance).delete()
    deleted_new_products = db.query(NewProduct).delete()
    deleted_existing_products = db.query(ExistingProduct).delete()
    deleted_saving_products = db.query(SavingProduct).delete()
    db.commit()

    return {
        "deletedSavingProducts": deleted_saving_products,
        "deletedExistingProducts": deleted_existing_products,
        "deletedNewProducts": deleted_new_products,
        "deletedFormInstances": deleted_form_instances,
    }


def sync_client_products_from_crm(db: Session, client_id: int) -> int:
    """Sync CRM snapshots to existing products for a client.

    This takes the latest snapshots, groups them by personal number (canonicalization),
    matches them with market products, and then upserts them into the ExistingProduct table.
    """
    return _sync_client_products_from_crm(db, client_id)
