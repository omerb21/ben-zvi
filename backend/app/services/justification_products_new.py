from typing import List

from sqlalchemy.orm import Session

from app.models import NewProduct, FormInstance
from app.schemas.justification import NewProductCreate, FormInstanceCreate
from app.services import justification_products_existing as _existing_products
from app.services import justification_products_utils as _products_utils
from app.utils.db import commit_and_refresh as _commit_and_refresh


def list_new_products_for_client(db: Session, client_id: int) -> List[NewProduct]:
    """Return all new products for a specific client."""
    return (
        db.query(NewProduct)
        .filter(NewProduct.client_id == client_id)
        .order_by(NewProduct.created_at.desc())
        .all()
    )


def create_new_product_for_client(
    db: Session,
    client_id: int,
    new_product_in: NewProductCreate,
) -> NewProduct:
    """Create a new product for the given client."""
    existing_product_id: int | None = None

    raw_existing_id = new_product_in.existingProductId
    if raw_existing_id is not None:
        if raw_existing_id > 0:
            existing_product_id = raw_existing_id
        else:
            existing_view_items = _existing_products.list_existing_products_view_for_client(db, client_id)
            virtual_item = _products_utils._find_existing_view_item_by_id(existing_view_items, raw_existing_id)

            if virtual_item is not None:
                existing_row = _existing_products._materialize_virtual_existing_product(db, client_id, virtual_item)
                existing_product_id = existing_row.id

    new_product = NewProduct(
        client_id=client_id,
        existing_product_id=existing_product_id,
        **_products_utils._product_schema_to_model_kwargs(new_product_in),
    )
    db.add(new_product)
    _commit_and_refresh(db, new_product)
    return new_product


def list_form_instances_for_new_product(db: Session, new_product_id: int) -> List[FormInstance]:
    """Return all form instances for a specific new product."""
    return (
        db.query(FormInstance)
        .filter(FormInstance.new_product_id == new_product_id)
        .order_by(FormInstance.generated_at.desc())
        .all()
    )


def create_form_instance_for_new_product(
    db: Session,
    new_product_id: int,
    form_in: FormInstanceCreate,
) -> FormInstance:
    """Create a new form instance for the given new product."""
    form = FormInstance(
        new_product_id=new_product_id,
        template_filename=form_in.templateFilename,
        status=form_in.status or "נוצר",
        filled_data=form_in.filledData,
        file_output_path=form_in.fileOutputPath,
    )
    db.add(form)
    _commit_and_refresh(db, form)
    return form
