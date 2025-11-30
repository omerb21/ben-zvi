import httpClient from "./httpClient";

export type ClientBeneficiary = {
  id: number;
  index: number;
  firstName: string;
  lastName: string;
  idNumber: string;
  birthDate: string;
  address: string;
  relation: string;
  percentage: number;
};

export type Client = {
  id: number;
  idNumber: string;
  fullName: string;
  firstName?: string | null;
  lastName?: string | null;
  email?: string | null;
  phone?: string | null;
  addressStreet?: string | null;
  addressCity?: string | null;
  addressPostalCode?: string | null;
  addressHouseNumber?: string | null;
  addressApartment?: string | null;
  birthDate?: string | null;
  gender?: string | null;
  maritalStatus?: string | null;
  birthCountry?: string | null;
  employerName?: string | null;
  employerHp?: string | null;
  employerAddress?: string | null;
  employerPhone?: string | null;
  beneficiaries?: ClientBeneficiary[] | null;
};

export type Snapshot = {
  id: number;
  clientId: number;
  fundCode: string;
  fundType?: string | null;
  fundName?: string | null;
  amount: number;
  snapshotDate: string;
};

export type SummaryResponse = {
  month: string | null;
  totalAssets: number;
  bySource: Record<string, number>;
  byFundType: Record<string, number>;
};

export type MonthlyChangePoint = {
  month: string;
  total: number;
  change?: number | null;
  percentChange?: number | null;
};

export type HistoryPoint = {
  month: string;
  amount: number;
};

export type FundHistoryPoint = {
  date: string;
  amount: number;
  source: string;
  change?: number | null;
};

export type ClientSummary = {
  id: number;
  fullName: string;
  idNumber: string;
  totalAmount: number;
  sources: string;
  rawSources: string;
  fundCount: number;
  lastUpdate?: string | null;
};

export type ClientNote = {
  id: number;
  note: string;
  createdAt: string;
  reminderAt?: string | null;
  dismissedAt?: string | null;
};

export type Reminder = {
  id: number;
  note: string;
  createdAt: string;
  reminderAt?: string | null;
  dismissedAt?: string | null;
  clientId: number;
  clientName: string;
};

export type ClientBeneficiaryPayload = {
  index: number;
  firstName: string;
  lastName: string;
  idNumber: string;
  birthDate: string;
  address: string;
  relation: string;
  percentage: number;
};

export type ClientUpdatePayload = {
  firstName?: string;
  lastName?: string;
  email?: string;
  phone?: string;
  addressStreet?: string;
  addressCity?: string;
  addressPostalCode?: string;
  addressHouseNumber?: string;
  addressApartment?: string;
  birthDate?: string;
  gender?: string;
  maritalStatus?: string;
  birthCountry?: string;
  employerName?: string;
  employerHp?: string;
  employerAddress?: string;
  employerPhone?: string;
  beneficiaries?: ClientBeneficiaryPayload[];
};

export type ClientCreatePayload = {
  idNumber: string;
  fullName: string;
  firstName?: string;
  lastName?: string;
  email?: string;
  phone?: string;
  addressStreet?: string;
  addressCity?: string;
  addressPostalCode?: string;
  addressHouseNumber?: string;
  addressApartment?: string;
  birthDate?: string;
  gender?: string;
  maritalStatus?: string;
  birthCountry?: string;
  employerName?: string;
  employerHp?: string;
  employerAddress?: string;
  employerPhone?: string;
};

export type SnapshotCreatePayload = {
  fundCode: string;
  fundType?: string | null;
  fundName?: string | null;
  fundNumber?: string | null;
  source?: string | null;
  amount: number;
  snapshotDate: string;
};

export async function fetchClients(): Promise<Client[]> {
  const response = await httpClient.get<Client[]>("/api/v1/crm/clients");
  return response.data;
}

export async function fetchClient(clientId: number): Promise<Client> {
  const response = await httpClient.get<Client>(
    `/api/v1/crm/clients/${clientId}`
  );
  return response.data;
}

export async function createClient(
  payload: ClientCreatePayload
): Promise<Client> {
  const response = await httpClient.post<Client>(
    "/api/v1/crm/clients",
    payload
  );
  return response.data;
}

export async function fetchClientSnapshots(
  clientId: number
): Promise<Snapshot[]> {
  const response = await httpClient.get<Snapshot[]>(
    `/api/v1/crm/clients/${clientId}/snapshots`
  );
  return response.data;
}

export async function createSnapshotForClient(
  clientId: number,
  payload: SnapshotCreatePayload
): Promise<Snapshot> {
  const response = await httpClient.post<Snapshot>(
    `/api/v1/crm/clients/${clientId}/snapshots`,
    payload
  );
  return response.data;
}

export async function fetchSummary(month?: string): Promise<SummaryResponse> {
  const response = await httpClient.get<SummaryResponse>("/api/v1/crm/summary", {
    params: month ? { month } : undefined,
  });
  return response.data;
}

export async function fetchMonthlyChange(): Promise<MonthlyChangePoint[]> {
  const response = await httpClient.get<MonthlyChangePoint[]>(
    "/api/v1/crm/monthly-change"
  );
  return response.data;
}

export async function fetchHistory(
  clientId?: number
): Promise<HistoryPoint[]> {
  const response = await httpClient.get<HistoryPoint[]>(
    "/api/v1/crm/history",
    {
      params: clientId !== undefined ? { client_id: clientId } : undefined,
    }
  );
  return response.data;
}

export async function fetchFundHistory(
  clientId: number,
  fundNumber: string
): Promise<FundHistoryPoint[]> {
  const response = await httpClient.get<FundHistoryPoint[]>(
    "/api/v1/crm/fund-history",
    {
      params: { client_id: clientId, fund_number: fundNumber },
    }
  );
  return response.data;
}

export async function fetchClientSummaries(
  month?: string
): Promise<ClientSummary[]> {
  const response = await httpClient.get<ClientSummary[]>(
    "/api/v1/crm/clients-summary",
    {
      params: month ? { month } : undefined,
    }
  );
  return response.data;
}

export async function fetchClientNotes(
  clientId: number
): Promise<ClientNote[]> {
  const response = await httpClient.get<ClientNote[]>(
    `/api/v1/crm/clients/${clientId}/notes`
  );
  return response.data;
}

export async function createClientNote(
  clientId: number,
  payload: { note: string; reminderAt?: string | null }
): Promise<ClientNote> {
  const response = await httpClient.post<ClientNote>(
    `/api/v1/crm/clients/${clientId}/notes`,
    payload
  );
  return response.data;
}

export async function dismissClientNote(
  clientId: number,
  noteId: number
): Promise<ClientNote> {
  const response = await httpClient.post<ClientNote>(
    `/api/v1/crm/clients/${clientId}/notes/${noteId}/dismiss`
  );
  return response.data;
}

export async function clearNoteReminder(
  clientId: number,
  noteId: number
): Promise<ClientNote> {
  const response = await httpClient.post<ClientNote>(
    `/api/v1/crm/clients/${clientId}/notes/${noteId}/clear-reminder`
  );
  return response.data;
}

export async function deleteClientNote(
  clientId: number,
  noteId: number
): Promise<void> {
  await httpClient.delete(`/api/v1/crm/clients/${clientId}/notes/${noteId}`);
}

export async function fetchReminders(): Promise<Reminder[]> {
  const response = await httpClient.get<Reminder[]>("/api/v1/crm/reminders");
  return response.data;
}

export async function updateClient(
  clientId: number,
  payload: ClientUpdatePayload
): Promise<Client> {
  const response = await httpClient.put<Client>(
    `/api/v1/crm/clients/${clientId}`,
    payload
  );
  return response.data;
}

export async function deleteClient(clientId: number): Promise<void> {
  await httpClient.delete(`/api/v1/crm/clients/${clientId}`);
}

export async function downloadClientPdf(clientId: number) {
  return httpClient.get<Blob>(
    `/api/v1/crm/clients/${clientId}/report.pdf`,
    {
      responseType: "blob",
    }
  );
}
