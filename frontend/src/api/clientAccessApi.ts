import httpClient from "./httpClient";

export type ClientCredentialsResetResult = {
  clientId: number;
  clientToken: string;
  clientPin: string;
};

export type ClientTokenUpdateResult = {
  clientId: number;
  clientToken: string | null;
};

export type ClientPinUpdateResult = {
  clientId: number;
  hasPin: boolean;
};

export type ClientAccessDisableResult = {
  clientId: number;
  disabled: boolean;
};

export async function resetClientCredentials(
  clientId: number
): Promise<ClientCredentialsResetResult> {
  const response = await httpClient.post<ClientCredentialsResetResult>(
    `/api/v1/admin/clients/${clientId}/credentials/reset`
  );
  return response.data;
}

export async function updateClientToken(
  clientId: number,
  clientToken: string
): Promise<ClientTokenUpdateResult> {
  const response = await httpClient.post<ClientTokenUpdateResult>(
    `/api/v1/admin/clients/${clientId}/token`,
    { clientToken }
  );
  return response.data;
}

export async function updateClientPin(
  clientId: number,
  clientPin: string | null
): Promise<ClientPinUpdateResult> {
  const response = await httpClient.post<ClientPinUpdateResult>(
    `/api/v1/admin/clients/${clientId}/pin`,
    { clientPin }
  );
  return response.data;
}

export async function disableClientAccess(
  clientId: number
): Promise<ClientAccessDisableResult> {
  // Clear token and PIN using existing admin endpoints
  await updateClientToken(clientId, "");
  await updateClientPin(clientId, null);

  return { clientId, disabled: true };
}
