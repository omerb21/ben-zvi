import re
from typing import List, Dict

from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status, Form
from sqlalchemy.orm import Session

from app.database import get_db
from app.migration import (
    migrate_mini_crm,
    migrate_legacy_crm_clients_from_excel,
    migrate_justification,
    migrate_justification_clients_only,
)
from app.schemas.admin import (
    MiniCrmMigrationResult,
    JustificationMigrationResult,
    JustificationClientsOnlyMigrationResult,
    CrmExcelImportResult,
    GemelNetImportResult,
    ClearCrmDataResult,
    ClearJustificationDataResult,
    LegacyCrmClientsImportResult,
    ClientTokenUpdate,
    ClientTokenUpdateResult,
    ClientPinUpdate,
    ClientPinUpdateResult,
    ClientCredentialsResetResult,
    ClientAccessDisableResult,
    DatabaseStatsResult,
)
from app.schemas.justification import SavingProductCreate
from app.models import (
    Client, Snapshot, ExistingProduct, NewProduct,
    FormInstance, ClientBeneficiary, ClientSignatureRequest,
    SavingProduct,
)
from app.services.imports import (
    import_crm_from_excel,
    import_saving_products_from_gemelnet_xml,
    sync_saving_products_batch,
)
from app.services.crm import (
    clear_crm_data,
    set_client_token,
    set_client_pin,
    reset_client_credentials,
    disable_client_access,
)
from app.services.justification import clear_justification_data
from app.utils.http_exceptions import raise_client_not_found as _raise_client_not_found
from app.utils.uploads import (
    read_upload_bytes as _read_upload_bytes,
    save_upload_to_temp_file as _save_upload_to_temp_file,
)


router = APIRouter(prefix="/api/v1/admin", tags=["admin"])


def _ensure_client_or_404(client: Client | None) -> Client:
    if not client:
        _raise_client_not_found()
    return client


async def _read_upload_or_400(file: UploadFile, *, empty_detail: str) -> bytes:
    contents = await _read_upload_bytes(file)
    if not contents:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=empty_detail,
        )
    return contents


def _normalize_client_pin_or_422(raw_pin: str | None) -> str | None:
    if raw_pin is None:
        return None

    value = raw_pin.strip()
    if not value:
        return None

    if not re.fullmatch(r"\d{6}", value):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="clientPin must be a 6-digit numeric code",
        )

    return value


def _count_rows(db: Session, model, where=None) -> int:
    query = db.query(model)
    if where is not None:
        query = query.filter(where)
    return query.count()


def _get_result_count(result: dict, key: str) -> int:
    return result.get(key, 0)


@router.post("/migrate-mini-crm", response_model=MiniCrmMigrationResult)
def run_mini_crm_migration(db: Session = Depends(get_db)) -> MiniCrmMigrationResult:
    """Trigger migration from legacy mini_crm database into unified CRM snapshots.

    This endpoint is idempotent at the data level as much as possible because
    the underlying migration service de-duplicates clients and snapshots
    based on identifiers.
    """
    result = migrate_mini_crm(db)
    return MiniCrmMigrationResult(
        createdClients=_get_result_count(result, "created_clients"),
        reusedClients=_get_result_count(result, "reused_clients"),
        createdSnapshots=_get_result_count(result, "created_snapshots"),
    )


@router.post("/migrate-justification", response_model=JustificationMigrationResult)
def run_justification_migration(
    db: Session = Depends(get_db),
) -> JustificationMigrationResult:
    """Trigger migration from legacy justification system into unified DB.

    This imports saving products, existing products, new products and form
    instances into the normalized tables.
    """
    result = migrate_justification(db)
    return JustificationMigrationResult(
        createdClients=_get_result_count(result, "created_clients"),
        reusedClients=_get_result_count(result, "reused_clients"),
        createdSavingProducts=_get_result_count(result, "created_saving_products"),
        createdExistingProducts=_get_result_count(result, "created_existing_products"),
        createdNewProducts=_get_result_count(result, "created_new_products"),
        createdFormInstances=_get_result_count(result, "created_form_instances"),
    )


@router.post(
    "/migrate-justification-clients",
    response_model=JustificationClientsOnlyMigrationResult,
)
def run_justification_clients_migration(
    db: Session = Depends(get_db),
) -> JustificationClientsOnlyMigrationResult:
    """Import or back-fill client personal details from legacy justification DB.

    This endpoint only affects Client rows (no products or forms).
    """
    result = migrate_justification_clients_only(db)
    return JustificationClientsOnlyMigrationResult(
        createdClients=_get_result_count(result, "created_clients"),
        updatedClients=_get_result_count(result, "updated_clients"),
        reusedClients=_get_result_count(result, "reused_clients"),
    )


@router.post(
    "/migrate-legacy-crm-clients",
    response_model=LegacyCrmClientsImportResult,
)
def run_legacy_crm_clients_migration(
    db: Session = Depends(get_db),
) -> LegacyCrmClientsImportResult:
    """Import or back-fill client personal details from legacy Clients.xlsx.

    The Excel file is expected at dev/mini_crm/uploads/Clients.xlsx relative
    to this backend project and uses the same ID normalization as the legacy
    Mini‑CRM ingestion.
    """

    try:
        result = migrate_legacy_crm_clients_from_excel(db)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except Exception as exc:  # pragma: no cover - defensive
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Legacy CRM clients migration failed: {exc}",
        ) from exc

    return LegacyCrmClientsImportResult(
        createdClients=_get_result_count(result, "created_clients"),
        updatedClients=_get_result_count(result, "updated_clients"),
        reusedClients=_get_result_count(result, "reused_clients"),
        rowsProcessed=_get_result_count(result, "rows_processed"),
    )


@router.post("/import-crm-excel", response_model=CrmExcelImportResult)
async def import_crm_excel(
    snapshot_month: str | None = Form(None),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
) -> CrmExcelImportResult:
    # Instead of reading the whole file into RAM, we stream it to a temporary file.
    # This prevents server crashes (OOM) on large files, which often manifest as CORS errors in the frontend.
    temp_path = _save_upload_to_temp_file(file)
    try:
        # Pass the path directly to the service layer
        result = import_crm_from_excel(db, "", temp_path, snapshot_month, file.filename)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    finally:
        # Cleanup temp file
        if temp_path.exists():
            temp_path.unlink()

    return CrmExcelImportResult(**result)


@router.post("/import-gemelnet-xml", response_model=GemelNetImportResult)
async def import_gemelnet_xml(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
) -> GemelNetImportResult:
    contents = await _read_upload_or_400(file, empty_detail="Empty XML file uploaded")
    result = import_saving_products_from_gemelnet_xml(db, contents)
    return GemelNetImportResult(**result)


@router.delete("/clear-crm-data", response_model=ClearCrmDataResult)
def clear_crm_data_endpoint(db: Session = Depends(get_db)) -> ClearCrmDataResult:
    """Clear CRM-specific data (snapshots and client notes)."""

    result = clear_crm_data(db)
    return ClearCrmDataResult(**result)


@router.delete("/clear-justification-data", response_model=ClearJustificationDataResult)
def clear_justification_data_endpoint(
    db: Session = Depends(get_db),
) -> ClearJustificationDataResult:
    """Clear justification-specific data (saving/existing/new products and forms)."""

    result = clear_justification_data(db)
    return ClearJustificationDataResult(**result)


@router.post("/clients/{client_id}/token", response_model=ClientTokenUpdateResult)
def update_client_token(
    client_id: int,
    payload: ClientTokenUpdate,
    db: Session = Depends(get_db),
) -> ClientTokenUpdateResult:
    client = _ensure_client_or_404(set_client_token(db, client_id, payload.clientToken))

    return ClientTokenUpdateResult(clientId=client.id, clientToken=client.client_token)


@router.post("/clients/{client_id}/pin", response_model=ClientPinUpdateResult)
def update_client_pin(
    client_id: int,
    payload: ClientPinUpdate,
    db: Session = Depends(get_db),
) -> ClientPinUpdateResult:
    normalized_pin = _normalize_client_pin_or_422(payload.clientPin)

    client = _ensure_client_or_404(set_client_pin(db, client_id, normalized_pin))

    return ClientPinUpdateResult(clientId=client.id, hasPin=bool(client.client_pin_hash))


@router.post(
    "/clients/{client_id}/credentials/reset",
    response_model=ClientCredentialsResetResult,
)
def reset_client_credentials_endpoint(
    client_id: int,
    db: Session = Depends(get_db),
) -> ClientCredentialsResetResult:
    client, token, pin = reset_client_credentials(db, client_id)
    if not client or token is None or pin is None:
        _raise_client_not_found()

    return ClientCredentialsResetResult(
        clientId=client.id,
        clientToken=token,
        clientPin=pin,
    )


@router.post(
    "/clients/{client_id}/access/disable",
    response_model=ClientAccessDisableResult,
)
def disable_client_access_endpoint(
    client_id: int,
    db: Session = Depends(get_db),
) -> ClientAccessDisableResult:
    client = _ensure_client_or_404(disable_client_access(db, client_id))

    return ClientAccessDisableResult(clientId=client.id, disabled=True)


@router.get("/stats", response_model=DatabaseStatsResult)
def get_database_stats(db: Session = Depends(get_db)) -> DatabaseStatsResult:
    """Get basic database statistics for admin dashboard."""
    return DatabaseStatsResult(
        totalClients=_count_rows(db, Client),
        totalSnapshots=_count_rows(db, Snapshot),
        totalExistingProducts=_count_rows(db, ExistingProduct),
        totalNewProducts=_count_rows(db, NewProduct),
        totalFormInstances=_count_rows(db, FormInstance),
        totalBeneficiaries=_count_rows(db, ClientBeneficiary),
        totalSignatureRequests=_count_rows(db, ClientSignatureRequest),
        pendingSignatureRequests=_count_rows(
            db,
            ClientSignatureRequest,
            where=(ClientSignatureRequest.status == "pending"),
        ),
    )


@router.post("/sync-market-products")
def sync_market_products_endpoint(
    products: List[SavingProductCreate],
    db: Session = Depends(get_db),
):
    """Sync a batch of market products (SavingProducts) to the DB."""
    result = sync_saving_products_batch(db, products)
    return result

