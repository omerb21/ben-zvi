import httpClient from "./httpClient";

export type MiniCrmMigrationResult = {
  createdClients: number;
  reusedClients: number;
  createdSnapshots: number;
};

export type JustificationMigrationResult = {
  createdClients: number;
  reusedClients: number;
  createdSavingProducts: number;
  createdExistingProducts: number;
  createdNewProducts: number;
  createdFormInstances: number;
};

export type CrmExcelImportResult = {
  companyCode: string;
  createdClients: number;
  reusedClients: number;
  createdSnapshots: number;
  rowsProcessed: number;
  duplicatesSkipped: number;
};

export type GemelNetImportResult = {
  createdSavingProducts: number;
  updatedSavingProducts: number;
  rowsProcessed: number;
  duplicatesSkipped: number;
};

export type ClearCrmDataResult = {
  deletedSnapshots: number;
  deletedClientNotes: number;
};

export type ClearJustificationDataResult = {
  deletedSavingProducts: number;
  deletedExistingProducts: number;
  deletedNewProducts: number;
  deletedFormInstances: number;
};

export async function runMiniCrmMigration(): Promise<MiniCrmMigrationResult> {
  const response = await httpClient.post<MiniCrmMigrationResult>(
    "/api/v1/admin/migrate-mini-crm"
  );
  return response.data;
}

export async function runJustificationMigration(): Promise<JustificationMigrationResult> {
  const response = await httpClient.post<JustificationMigrationResult>(
    "/api/v1/admin/migrate-justification"
  );
  return response.data;
}

export async function importCrmExcel(
  file: File,
  snapshotMonth?: string
): Promise<CrmExcelImportResult> {
  const formData = new FormData();
  formData.append("file", file);
  if (snapshotMonth) {
    formData.append("snapshot_month", snapshotMonth);
  }

  const response = await httpClient.post<CrmExcelImportResult>(
    "/api/v1/admin/import-crm-excel",
    formData
  );
  return response.data;
}

export async function importGemelNetXml(
  file: File
): Promise<GemelNetImportResult> {
  const formData = new FormData();
  formData.append("file", file);

  const response = await httpClient.post<GemelNetImportResult>(
    "/api/v1/admin/import-gemelnet-xml",
    formData
  );
  return response.data;
}

export async function clearCrmData(): Promise<ClearCrmDataResult> {
  const response = await httpClient.delete<ClearCrmDataResult>(
    "/api/v1/admin/clear-crm-data"
  );
  return response.data;
}

export async function clearJustificationData(): Promise<ClearJustificationDataResult> {
  const response = await httpClient.delete<ClearJustificationDataResult>(
    "/api/v1/admin/clear-justification-data"
  );
  return response.data;
}
