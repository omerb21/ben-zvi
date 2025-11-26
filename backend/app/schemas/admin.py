from pydantic import BaseModel


class MiniCrmMigrationResult(BaseModel):
    createdClients: int
    reusedClients: int
    createdSnapshots: int


class JustificationMigrationResult(BaseModel):
    createdClients: int
    reusedClients: int
    createdSavingProducts: int
    createdExistingProducts: int
    createdNewProducts: int
    createdFormInstances: int


class JustificationClientsOnlyMigrationResult(BaseModel):
    createdClients: int
    updatedClients: int
    reusedClients: int


class CrmExcelImportResult(BaseModel):
    companyCode: str
    createdClients: int
    reusedClients: int
    createdSnapshots: int
    rowsProcessed: int
    duplicatesSkipped: int


class GemelNetImportResult(BaseModel):
    createdSavingProducts: int
    updatedSavingProducts: int
    rowsProcessed: int
    duplicatesSkipped: int


class ClearCrmDataResult(BaseModel):
    deletedSnapshots: int
    deletedClientNotes: int


class ClearJustificationDataResult(BaseModel):
    deletedSavingProducts: int
    deletedExistingProducts: int
    deletedNewProducts: int
    deletedFormInstances: int


class LegacyCrmClientsImportResult(BaseModel):
    createdClients: int
    updatedClients: int
    reusedClients: int
    rowsProcessed: int
