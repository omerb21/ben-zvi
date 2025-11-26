import httpClient from "./httpClient";

export type SavingProduct = {
  id: number;
  fundType: string;
  companyName: string;
  fundName: string;
  fundCode: string;
  yield1yr?: number | null;
  yield3yr?: number | null;
  riskLevel?: number | null;
  guaranteedReturn?: string | null;
};

export type NewProduct = {
  id: number;
  clientId: number;
  existingProductId?: number | null;
  fundType: string;
  companyName: string;
  fundName: string;
  fundCode: string;
  yield1yr?: number | null;
  yield3yr?: number | null;
  personalNumber?: string | null;
  managementFeeBalance?: number | null;
  managementFeeContributions?: number | null;
  accumulatedAmount?: number | null;
  employmentStatus?: string | null;
  hasRegularContributions?: boolean | null;
};

export type ExistingProductCreatePayload = {
  fundType: string;
  companyName: string;
  fundName: string;
  fundCode: string;
  yield1yr?: number | null;
  yield3yr?: number | null;
  personalNumber: string;
  managementFeeBalance?: number | null;
  managementFeeContributions?: number | null;
  accumulatedAmount?: number | null;
  employmentStatus?: string | null;
  hasRegularContributions?: boolean | null;
};

export type ExistingProduct = {
  id: number;
  clientId: number;
  fundType: string;
  companyName: string;
  fundName: string;
  fundCode: string;
  yield1yr?: number | null;
  yield3yr?: number | null;
  personalNumber: string;
  managementFeeBalance?: number | null;
  managementFeeContributions?: number | null;
  accumulatedAmount?: number | null;
  employmentStatus?: string | null;
  hasRegularContributions?: boolean | null;
  isVirtual?: boolean | null;
};

export type NewProductCreatePayload = {
  existingProductId?: number | null;
  fundType: string;
  companyName: string;
  fundName: string;
  fundCode: string;
  yield1yr?: number | null;
  yield3yr?: number | null;
  personalNumber?: string | null;
  managementFeeBalance?: number | null;
  managementFeeContributions?: number | null;
  accumulatedAmount?: number | null;
  employmentStatus?: string | null;
  hasRegularContributions?: boolean | null;
};

export type FormInstance = {
  id: number;
  newProductId: number;
  templateFilename: string;
  status?: string | null;
  filledData?: Record<string, unknown> | null;
  fileOutputPath?: string | null;
};

export type ExistingProductUpdatePayload = {
  fundType?: string | null;
  companyName?: string | null;
  fundName?: string | null;
  fundCode?: string | null;
  yield1yr?: number | null;
  yield3yr?: number | null;
  personalNumber?: string | null;
  managementFeeBalance?: number | null;
  managementFeeContributions?: number | null;
  accumulatedAmount?: number | null;
  employmentStatus?: string | null;
  hasRegularContributions?: boolean | null;
};

export type FormInstanceCreatePayload = {
  templateFilename: string;
  status?: string | null;
  filledData?: Record<string, unknown> | null;
  fileOutputPath?: string | null;
};

export type PdfOverlayPayload = {
  freeText?: string | null;
  signatureDataUrl?: string | null;
  signaturePosition?: string | null;
};

export async function fetchSavingProducts(): Promise<SavingProduct[]> {
  const response = await httpClient.get<SavingProduct[]>(
    "/api/v1/justification/saving-products"
  );
  return response.data;
}

export function buildPacketPdfUrl(clientId: number): string {
  const baseUrl = buildBaseUrl();
  return `${baseUrl}/api/v1/justification/clients/${clientId}/packet.pdf`;
}

export function buildSignedClientPacketPdfUrl(clientId: number): string {
  const baseUrl = buildBaseUrl();
  return `${baseUrl}/api/v1/justification/clients/${clientId}/packet-signed-client.pdf`;
}

export type PacketSignRequestResponse = {
  token: string;
  url: string;
};

export async function createPacketSignRequest(
  clientId: number
): Promise<PacketSignRequestResponse & { fullUrl: string }> {
  const response = await httpClient.post<PacketSignRequestResponse>(
    `/api/v1/justification/clients/${clientId}/packet-sign-request`,
    {}
  );

  const rawBase = httpClient.defaults.baseURL || "";
  const baseUrl = rawBase.replace(/\/+$/, "");
  const backendFullUrl = (response.data as any).fullUrl || "";
  const fallbackFullUrl = `${baseUrl}${response.data.url}`;
  const fullUrl = backendFullUrl || fallbackFullUrl;

  return { ...response.data, fullUrl };
}

export async function uploadPacketPdf(
  clientId: number,
  file: File
): Promise<void> {
  const formData = new FormData();
  formData.append("file", file);
  await httpClient.post(
    `/api/v1/justification/clients/${clientId}/packet-upload`,
    formData
  );
}

export async function trimPacketPdf(
  clientId: number,
  pagesToRemove: number[]
): Promise<void> {
  await httpClient.post(`/api/v1/justification/clients/${clientId}/packet-trim`, {
    pagesToRemove,
  });
}

export async function uploadB1Pdf(
  clientId: number,
  file: File
): Promise<void> {
  const formData = new FormData();
  formData.append("file", file);
  await httpClient.post(
    `/api/v1/justification/clients/${clientId}/b1-upload`,
    formData
  );
}

export async function uploadKitPdf(
  clientId: number,
  newProductId: number,
  file: File
): Promise<void> {
  const formData = new FormData();
  formData.append("file", file);
  await httpClient.post(
    `/api/v1/justification/clients/${clientId}/new-products/${newProductId}/kit-upload`,
    formData
  );
}

export async function updateExistingProduct(
  existingProductId: number,
  payload: ExistingProductUpdatePayload
): Promise<ExistingProduct> {
  const response = await httpClient.patch<ExistingProduct>(
    `/api/v1/justification/existing-products/${existingProductId}`,
    payload
  );
  return response.data;
}

export async function deleteExistingProduct(
  existingProductId: number
): Promise<void> {
  await httpClient.delete(`/api/v1/justification/existing-products/${existingProductId}`);
}

export async function fetchNewProductsForClient(
  clientId: number
): Promise<NewProduct[]> {
  const response = await httpClient.get<NewProduct[]>(
    `/api/v1/justification/clients/${clientId}/new-products`
  );
  return response.data;
}

export async function fetchExistingProductsForClient(
  clientId: number
): Promise<ExistingProduct[]> {
  const response = await httpClient.get<ExistingProduct[]>(
    `/api/v1/justification/clients/${clientId}/existing-products`
  );
  return response.data;
}

export async function createExistingProductForClient(
  clientId: number,
  payload: ExistingProductCreatePayload
): Promise<ExistingProduct> {
  const response = await httpClient.post<ExistingProduct>(
    `/api/v1/justification/clients/${clientId}/existing-products`,
    payload
  );
  return response.data;
}

export async function createNewProductForClient(
  clientId: number,
  payload: NewProductCreatePayload
): Promise<NewProduct> {
  const response = await httpClient.post<NewProduct>(
    `/api/v1/justification/clients/${clientId}/new-products`,
    payload
  );
  return response.data;
}

export async function fetchFormInstancesForNewProduct(
  newProductId: number
): Promise<FormInstance[]> {
  const response = await httpClient.get<FormInstance[]>(
    `/api/v1/justification/new-products/${newProductId}/form-instances`
  );
  return response.data;
}

export async function createFormInstanceForNewProduct(
  newProductId: number,
  payload: FormInstanceCreatePayload
): Promise<FormInstance> {
  const response = await httpClient.post<FormInstance>(
    `/api/v1/justification/new-products/${newProductId}/form-instances`,
    payload
  );
  return response.data;
}

export async function deleteNewProduct(newProductId: number): Promise<void> {
  await httpClient.delete(`/api/v1/justification/new-products/${newProductId}`);
}

export async function deleteFormInstance(
  formInstanceId: number
): Promise<void> {
  await httpClient.delete(
    `/api/v1/justification/form-instances/${formInstanceId}`
  );
}

function buildBaseUrl(): string {
  const raw = httpClient.defaults.baseURL || "";
  return raw.replace(/\/+$/, "");
}

export function buildAdviceHtmlUrl(clientId: number): string {
  const baseUrl = buildBaseUrl();
  return `${baseUrl}/api/v1/justification/clients/${clientId}/advice.html`;
}

export function buildAdvicePdfUrl(clientId: number): string {
  const baseUrl = buildBaseUrl();
  return `${baseUrl}/api/v1/justification/clients/${clientId}/advice.pdf`;
}

export function buildB1PdfUrl(clientId: number): string {
  const baseUrl = buildBaseUrl();
  return `${baseUrl}/api/v1/justification/clients/${clientId}/b1.pdf`;
}

export function buildKitPdfUrl(clientId: number, newProductId: number): string {
  const baseUrl = buildBaseUrl();
  return `${baseUrl}/api/v1/justification/clients/${clientId}/new-products/${newProductId}/kit.pdf`;
}

export async function generateAdviceOverlayPdf(
  clientId: number,
  payload: PdfOverlayPayload
): Promise<Blob> {
  const response = await httpClient.post<Blob>(
    `/api/v1/justification/clients/${clientId}/advice-overlay.pdf`,
    payload,
    { responseType: "blob" }
  );
  return response.data;
}

export async function generateB1OverlayPdf(
  clientId: number,
  payload: PdfOverlayPayload
): Promise<Blob> {
  const response = await httpClient.post<Blob>(
    `/api/v1/justification/clients/${clientId}/b1-overlay.pdf`,
    payload,
    { responseType: "blob" }
  );
  return response.data;
}

export async function generateKitOverlayPdf(
  clientId: number,
  newProductId: number,
  payload: PdfOverlayPayload
): Promise<Blob> {
  const response = await httpClient.post<Blob>(
    `/api/v1/justification/clients/${clientId}/new-products/${newProductId}/kit-overlay.pdf`,
    payload,
    { responseType: "blob" }
  );
  return response.data;
}
