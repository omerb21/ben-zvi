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


class ClientTokenUpdate(BaseModel):
    clientToken: str


class ClientTokenUpdateResult(BaseModel):
    clientId: int
    clientToken: str | None


class ClientPinUpdate(BaseModel):
    clientPin: str | None = None


class ClientPinUpdateResult(BaseModel):
    clientId: int
    hasPin: bool


class ClientCredentialsResetResult(BaseModel):
    clientId: int
    clientToken: str
    clientPin: str


class ClientAccessDisableResult(BaseModel):
    clientId: int
    disabled: bool


class DatabaseStatsResult(BaseModel):
    totalClients: int
    totalSnapshots: int
    totalExistingProducts: int
    totalNewProducts: int
    totalFormInstances: int
    totalBeneficiaries: int
    totalSignatureRequests: int
    pendingSignatureRequests: int


class DeleteAllDocumentsResult(BaseModel):
    totalClients: int
    deletedDirectories: int
    totalFilesDeleted: int
    totalBytesFreed: int
    deletedClientNames: list[str]


class VerifyDeletionResult(BaseModel):
    totalClients: int
    clientsWithFiles: int
    orphanedDirectories: int
    totalRemainingFiles: int
    totalRemainingBytes: int
    remainingClientDirs: list[str]
    remainingOrphanedDirs: list[str]
