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
)
from app.services.imports import import_crm_from_excel, import_saving_products_from_gemelnet_xml
from app.services.crm import clear_crm_data
from app.services.justification import clear_justification_data


router = APIRouter(prefix="/api/v1/admin", tags=["admin"])


@router.post("/migrate-mini-crm", response_model=MiniCrmMigrationResult)
def run_mini_crm_migration(db: Session = Depends(get_db)) -> MiniCrmMigrationResult:
    """Trigger migration from legacy mini_crm database into unified CRM snapshots.

    This endpoint is idempotent at the data level as much as possible because
    the underlying migration service de-duplicates clients and snapshots
    based on identifiers.
    """
    result = migrate_mini_crm(db)
    return MiniCrmMigrationResult(
        createdClients=result.get("created_clients", 0),
        reusedClients=result.get("reused_clients", 0),
        createdSnapshots=result.get("created_snapshots", 0),
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
        createdClients=result.get("created_clients", 0),
        reusedClients=result.get("reused_clients", 0),
        createdSavingProducts=result.get("created_saving_products", 0),
        createdExistingProducts=result.get("created_existing_products", 0),
        createdNewProducts=result.get("created_new_products", 0),
        createdFormInstances=result.get("created_form_instances", 0),
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
        createdClients=result.get("created_clients", 0),
        updatedClients=result.get("updated_clients", 0),
        reusedClients=result.get("reused_clients", 0),
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
        createdClients=result.get("created_clients", 0),
        updatedClients=result.get("updated_clients", 0),
        reusedClients=result.get("reused_clients", 0),
        rowsProcessed=result.get("rows_processed", 0),
    )


@router.post("/import-crm-excel", response_model=CrmExcelImportResult)
async def import_crm_excel(
    snapshot_month: str | None = Form(None),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
) -> CrmExcelImportResult:
    contents = await file.read()
    if not contents:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Empty Excel file uploaded",
        )
    try:
        result = import_crm_from_excel(db, "", contents, snapshot_month, file.filename)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    return CrmExcelImportResult(**result)


@router.post("/import-gemelnet-xml", response_model=GemelNetImportResult)
async def import_gemelnet_xml(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
) -> GemelNetImportResult:
    contents = await file.read()
    if not contents:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Empty XML file uploaded",
        )

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
