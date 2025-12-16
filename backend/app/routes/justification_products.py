from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.justification import (
    FormInstanceCreate,
    FormInstanceRead,
    NewProductCreate,
    NewProductRead,
    SavingProductRead,
    ExistingProductRead,
    ExistingProductCreate,
    ExistingProductUpdate,
)
from app.utils.justification_mappers import (
    to_saving_product_read,
    to_existing_product_read,
    to_existing_product_read_from_dict,
    to_new_product_read,
    to_form_instance_read,
)
from app.services import justification as justification_service
from app.services import crm as crm_service
from app.utils.http_exceptions import raise_client_not_found as _raise_client_not_found
from app.utils.http_exceptions import raise_new_product_not_found as _raise_new_product_not_found
from app.utils.http_exceptions import raise_not_found as _raise_not_found
from app.routes.client_helpers import get_client_or_404 as _get_client_or_404


router = APIRouter(tags=["justification"])


def _raise_existing_product_not_found() -> None:
    _raise_not_found("Existing product not found")


def _raise_form_instance_not_found() -> None:
    _raise_not_found("Form instance not found")


def _ensure_deleted_or_404(deleted: bool, raise_not_found) -> None:
    if not deleted:
        raise_not_found()


@router.get("/saving-products", response_model=List[SavingProductRead])
def list_saving_products(db: Session = Depends(get_db)):
    products = justification_service.list_saving_products(db)
    return [to_saving_product_read(product) for product in products]


@router.post(
    "/clients/{client_id}/existing-products",
    response_model=ExistingProductRead,
    status_code=status.HTTP_201_CREATED,
)
def create_existing_product_for_client(
    client_id: int,
    existing_in: ExistingProductCreate,
    db: Session = Depends(get_db),
):
    _get_client_or_404(db, client_id)

    product = justification_service.create_existing_product_for_client(db, client_id, existing_in)
    return to_existing_product_read(product, is_virtual=False)


@router.post(
    "/clients/{client_id}/sync-crm",
    status_code=status.HTTP_200_OK,
)
def sync_client_products_from_crm(
    client_id: int,
    db: Session = Depends(get_db),
):
    _get_client_or_404(db, client_id)

    count = justification_service.sync_client_products_from_crm(db, client_id)
    return {"detail": f"Synced {count} products from CRM"}


@router.post(
    "/sync-all-crm",
    status_code=status.HTTP_200_OK,
)
def sync_all_clients_from_crm(
    db: Session = Depends(get_db),
):
    clients = crm_service.list_clients(db)
    total_products = 0
    client_count = 0
    for client in clients:
        count = justification_service.sync_client_products_from_crm(db, client.id)
        total_products += count
        client_count += 1

    return {
        "detail": f"Synced {total_products} products from CRM across {client_count} clients",
    }


@router.get(
    "/clients/{client_id}/existing-products",
    response_model=List[ExistingProductRead],
)
def list_existing_products_for_client(client_id: int, db: Session = Depends(get_db)):
    _get_client_or_404(db, client_id)

    products = justification_service.list_existing_products_view_for_client(db, client_id)
    return [to_existing_product_read_from_dict(product) for product in products]


@router.patch(
    "/existing-products/{existing_product_id}",
    response_model=ExistingProductRead,
)
def update_existing_product(
    existing_product_id: int,
    existing_in: ExistingProductUpdate,
    db: Session = Depends(get_db),
):
    product = justification_service.update_existing_product(db, existing_product_id, existing_in)
    if not product:
        _raise_existing_product_not_found()

    return to_existing_product_read(product, is_virtual=False)


@router.get(
    "/clients/{client_id}/new-products",
    response_model=List[NewProductRead],
)
def list_new_products_for_client(client_id: int, db: Session = Depends(get_db)):
    _get_client_or_404(db, client_id)

    products = justification_service.list_new_products_for_client(db, client_id)
    return [to_new_product_read(product) for product in products]


@router.post(
    "/clients/{client_id}/new-products",
    response_model=NewProductRead,
    status_code=status.HTTP_201_CREATED,
)
def create_new_product_for_client(
    client_id: int,
    new_product_in: NewProductCreate,
    db: Session = Depends(get_db),
):
    _get_client_or_404(db, client_id)

    product = justification_service.create_new_product_for_client(db, client_id, new_product_in)
    return to_new_product_read(product)


@router.get(
    "/new-products/{new_product_id}/form-instances",
    response_model=List[FormInstanceRead],
)
def list_form_instances_for_new_product(new_product_id: int, db: Session = Depends(get_db)):
    forms = justification_service.list_form_instances_for_new_product(db, new_product_id)
    return [to_form_instance_read(form) for form in forms]


@router.post(
    "/new-products/{new_product_id}/form-instances",
    response_model=FormInstanceRead,
    status_code=status.HTTP_201_CREATED,
)
def create_form_instance_for_new_product(
    new_product_id: int,
    form_in: FormInstanceCreate,
    db: Session = Depends(get_db),
):
    # Could validate that new_product_id exists here if needed
    form = justification_service.create_form_instance_for_new_product(db, new_product_id, form_in)
    return to_form_instance_read(form)


@router.delete(
    "/new-products/{new_product_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_new_product(new_product_id: int, db: Session = Depends(get_db)):
    deleted = justification_service.delete_new_product(db, new_product_id)
    _ensure_deleted_or_404(deleted, _raise_new_product_not_found)


@router.delete(
    "/existing-products/{existing_product_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_existing_product(existing_product_id: int, db: Session = Depends(get_db)):
    deleted = justification_service.delete_existing_product(db, existing_product_id)
    _ensure_deleted_or_404(deleted, _raise_existing_product_not_found)


@router.delete(
    "/form-instances/{form_instance_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_form_instance(form_instance_id: int, db: Session = Depends(get_db)):
    deleted = justification_service.delete_form_instance(db, form_instance_id)
    _ensure_deleted_or_404(deleted, _raise_form_instance_not_found)
