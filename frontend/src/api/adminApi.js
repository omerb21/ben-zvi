import httpClient from "./httpClient";

export async function runMiniCrmMigration() {
  const response = await httpClient.post("/api/v1/admin/migrate-mini-crm");
  return response.data;
}

export async function runJustificationMigration() {
  const response = await httpClient.post("/api/v1/admin/migrate-justification");
  return response.data;
}

export async function importCrmExcel(file, snapshotMonth) {
  const formData = new FormData();
  formData.append("file", file);
  if (snapshotMonth) {
    formData.append("snapshot_month", snapshotMonth);
  }

  const response = await httpClient.post("/api/v1/admin/import-crm-excel", formData);
  return response.data;
}

export async function importGemelNetXml(file) {
  const formData = new FormData();
  formData.append("file", file);

  const response = await httpClient.post("/api/v1/admin/import-gemelnet-xml", formData);
  return response.data;
}

export async function clearCrmData() {
  const response = await httpClient.delete("/api/v1/admin/clear-crm-data");
  return response.data;
}

export async function clearJustificationData() {
  const response = await httpClient.delete("/api/v1/admin/clear-justification-data");
  return response.data;
}

