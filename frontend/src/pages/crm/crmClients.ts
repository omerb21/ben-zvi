import type {
  Client,
  ClientSummary,
  Snapshot,
  ClientNote,
  HistoryPoint,
  FundHistoryPoint,
  Reminder,
  ClientCreatePayload,
  ClientUpdatePayload,
} from "../../api/crmApi";
import {
  fetchClient,
  fetchClientSnapshots,
  fetchClientNotes,
  fetchHistory,
  deleteClient,
  createClient,
  updateClient,
} from "../../api/crmApi";
import type { Dispatch, SetStateAction } from "react";

export type ViewMode = "main" | "dashboard" | "clientDetail";

export type LoadClientDetailsArgs = {
  client: ClientSummary;
  setSelectedClient: Dispatch<SetStateAction<ClientSummary | null>>;
  setViewMode: Dispatch<SetStateAction<ViewMode>>;
  setSnapshots: Dispatch<SetStateAction<Snapshot[]>>;
  setSelectedSnapshot: Dispatch<SetStateAction<Snapshot | null>>;
  setClientHistory: Dispatch<SetStateAction<HistoryPoint[]>>;
  setFundHistory: Dispatch<SetStateAction<FundHistoryPoint[]>>;
  setNotes: Dispatch<SetStateAction<ClientNote[]>>;
  setLoading: Dispatch<SetStateAction<boolean>>;
  setClientDetailsMap: Dispatch<SetStateAction<Record<number, Client>>>;
  setEditFirstName: Dispatch<SetStateAction<string>>;
  setEditLastName: Dispatch<SetStateAction<string>>;
  setEditEmail: Dispatch<SetStateAction<string>>;
  setEditPhone: Dispatch<SetStateAction<string>>;
  setEditBirthDate: Dispatch<SetStateAction<string>>;
  setEditAddressStreet: Dispatch<SetStateAction<string>>;
  setEditAddressCity: Dispatch<SetStateAction<string>>;
  setEditAddressPostalCode: Dispatch<SetStateAction<string>>;
  setEditGender: Dispatch<SetStateAction<string>>;
  setEditMaritalStatus: Dispatch<SetStateAction<string>>;
  setEditEmployerName: Dispatch<SetStateAction<string>>;
  setEditEmployerHp: Dispatch<SetStateAction<string>>;
  setEditEmployerAddress: Dispatch<SetStateAction<string>>;
  setEditEmployerPhone: Dispatch<SetStateAction<string>>;
  setError: Dispatch<SetStateAction<string | null>>;
};

export function loadClientDetailsAction({
  client,
  setSelectedClient,
  setViewMode,
  setSnapshots,
  setSelectedSnapshot,
  setClientHistory,
  setFundHistory,
  setNotes,
  setLoading,
  setClientDetailsMap,
  setEditFirstName,
  setEditLastName,
  setEditEmail,
  setEditPhone,
  setEditBirthDate,
  setEditAddressStreet,
  setEditAddressCity,
  setEditAddressPostalCode,
  setEditGender,
  setEditMaritalStatus,
  setEditEmployerName,
  setEditEmployerHp,
  setEditEmployerAddress,
  setEditEmployerPhone,
  setError,
}: LoadClientDetailsArgs) {
  setSelectedClient(client);
  setViewMode("clientDetail");
  setSnapshots([]);
  setSelectedSnapshot(null);
  setClientHistory([]);
  setFundHistory([]);
  setNotes([]);
  setLoading(true);

  Promise.all([
    fetchClient(client.id),
    fetchClientSnapshots(client.id),
    fetchClientNotes(client.id),
    fetchHistory(client.id),
  ])
    .then(([details, snapshotsData, notesData, historyData]) => {
      setClientDetailsMap((prev) => ({
        ...prev,
        [details.id]: details,
      }));
      setEditFirstName(details.firstName || "");
      setEditLastName(details.lastName || "");
      setEditEmail(details.email || "");
      setEditPhone(details.phone || "");
      setEditBirthDate(details.birthDate || "");
      setEditAddressStreet(details.addressStreet || "");
      setEditAddressCity(details.addressCity || "");
      setEditAddressPostalCode(details.addressPostalCode || "");
      setEditGender(details.gender || "");
      setEditMaritalStatus(details.maritalStatus || "");
      setEditEmployerName(details.employerName || "");
      setEditEmployerHp(details.employerHp || "");
      setEditEmployerAddress(details.employerAddress || "");
      setEditEmployerPhone(details.employerPhone || "");
      setSnapshots(snapshotsData);
      setNotes(notesData);
      setClientHistory(historyData);
      setError(null);
    })
    .catch(() => {
      setError("שגיאה בטעינת נתוני לקוח");
    })
    .finally(() => {
      setLoading(false);
    });
}

export type CreateClientArgs = {
  newClientIdNumber: string;
  newClientFullName: string;
  newClientEmail: string;
  newClientPhone: string;
  newClientBirthDate: string;
  newClientGender: string;
  newClientMaritalStatus: string;
  newClientEmployerName: string;
  newClientEmployerHp: string;
  newClientEmployerAddress: string;
  newClientEmployerPhone: string;
  setLoading: Dispatch<SetStateAction<boolean>>;
  setClients: Dispatch<SetStateAction<ClientSummary[]>>;
  setClientDetailsMap: Dispatch<SetStateAction<Record<number, Client>>>;
  setNewClientIdNumber: Dispatch<SetStateAction<string>>;
  setNewClientFullName: Dispatch<SetStateAction<string>>;
  setNewClientEmail: Dispatch<SetStateAction<string>>;
  setNewClientPhone: Dispatch<SetStateAction<string>>;
  setNewClientBirthDate: Dispatch<SetStateAction<string>>;
  setNewClientGender: Dispatch<SetStateAction<string>>;
  setNewClientMaritalStatus: Dispatch<SetStateAction<string>>;
  setNewClientEmployerName: Dispatch<SetStateAction<string>>;
  setNewClientEmployerHp: Dispatch<SetStateAction<string>>;
  setNewClientEmployerAddress: Dispatch<SetStateAction<string>>;
  setNewClientEmployerPhone: Dispatch<SetStateAction<string>>;
  setError: Dispatch<SetStateAction<string | null>>;
};

export function createClientAction({
  newClientIdNumber,
  newClientFullName,
  newClientEmail,
  newClientPhone,
  newClientBirthDate,
  newClientGender,
  newClientMaritalStatus,
  newClientEmployerName,
  newClientEmployerHp,
  newClientEmployerAddress,
  newClientEmployerPhone,
  setLoading,
  setClients,
  setClientDetailsMap,
  setNewClientIdNumber,
  setNewClientFullName,
  setNewClientEmail,
  setNewClientPhone,
  setNewClientBirthDate,
  setNewClientGender,
  setNewClientMaritalStatus,
  setNewClientEmployerName,
  setNewClientEmployerHp,
  setNewClientEmployerAddress,
  setNewClientEmployerPhone,
  setError,
}: CreateClientArgs) {
  const idNumber = newClientIdNumber.trim();
  const fullName = newClientFullName.trim();

  if (!idNumber || !fullName) {
    return;
  }

  const payload: ClientCreatePayload = {
    idNumber,
    fullName,
  };

  if (newClientEmail.trim()) {
    payload.email = newClientEmail.trim();
  }
  if (newClientPhone.trim()) {
    payload.phone = newClientPhone.trim();
  }
  if (newClientBirthDate.trim()) {
    payload.birthDate = newClientBirthDate.trim();
  }
  if (newClientGender.trim()) {
    payload.gender = newClientGender.trim();
  }
  if (newClientMaritalStatus.trim()) {
    payload.maritalStatus = newClientMaritalStatus.trim();
  }
  if (newClientEmployerName.trim()) {
    payload.employerName = newClientEmployerName.trim();
  }
  if (newClientEmployerHp.trim()) {
    payload.employerHp = newClientEmployerHp.trim();
  }
  if (newClientEmployerAddress.trim()) {
    payload.employerAddress = newClientEmployerAddress.trim();
  }
  if (newClientEmployerPhone.trim()) {
    payload.employerPhone = newClientEmployerPhone.trim();
  }

  setLoading(true);
  createClient(payload)
    .then((created) => {
      const summaryItem: ClientSummary = {
        id: created.id,
        fullName: created.fullName,
        idNumber: created.idNumber,
        totalAmount: 0,
        sources: "אין נתונים",
        rawSources: "אין נתונים",
        fundCount: 0,
        lastUpdate: null,
      };
      setClients((prev) => [...prev, summaryItem]);
      setClientDetailsMap((prev) => ({
        ...prev,
        [created.id]: created,
      }));
      setNewClientIdNumber("");
      setNewClientFullName("");
      setNewClientEmail("");
      setNewClientPhone("");
      setNewClientBirthDate("");
      setNewClientGender("");
      setNewClientMaritalStatus("");
      setNewClientEmployerName("");
      setNewClientEmployerHp("");
      setNewClientEmployerAddress("");
      setNewClientEmployerPhone("");
      setError(null);
    })
    .catch(() => {
      setError("שגיאה ביצירת לקוח חדש");
    })
    .finally(() => {
      setLoading(false);
    });
}

export type SaveClientDetailsArgs = {
  selectedClient: ClientSummary | null;
  editFirstName: string;
  editLastName: string;
  editEmail: string;
  editPhone: string;
  editBirthDate: string;
  editAddressStreet: string;
  editAddressCity: string;
  editAddressPostalCode: string;
  editGender: string;
  editMaritalStatus: string;
  editEmployerName: string;
  editEmployerHp: string;
  editEmployerAddress: string;
  editEmployerPhone: string;
  setLoading: Dispatch<SetStateAction<boolean>>;
  setClientDetailsMap: Dispatch<SetStateAction<Record<number, Client>>>;
  setSelectedClient: Dispatch<SetStateAction<ClientSummary | null>>;
  setClients: Dispatch<SetStateAction<ClientSummary[]>>;
  setError: Dispatch<SetStateAction<string | null>>;
};

export function saveClientDetailsAction({
  selectedClient,
  editFirstName,
  editLastName,
  editEmail,
  editPhone,
  editBirthDate,
  editAddressStreet,
  editAddressCity,
  editAddressPostalCode,
  editGender,
  editMaritalStatus,
  editEmployerName,
  editEmployerHp,
  editEmployerAddress,
  editEmployerPhone,
  setLoading,
  setClientDetailsMap,
  setSelectedClient,
  setClients,
  setError,
}: SaveClientDetailsArgs) {
  if (!selectedClient) {
    return;
  }

  const payload: ClientUpdatePayload = {};
  if (editFirstName.trim()) {
    payload.firstName = editFirstName.trim();
  }
  if (editLastName.trim()) {
    payload.lastName = editLastName.trim();
  }
  if (editEmail.trim()) {
    payload.email = editEmail.trim();
  }
  if (editPhone.trim()) {
    payload.phone = editPhone.trim();
  }
  if (editAddressStreet.trim()) {
    payload.addressStreet = editAddressStreet.trim();
  }
  if (editAddressCity.trim()) {
    payload.addressCity = editAddressCity.trim();
  }
  if (editAddressPostalCode.trim()) {
    payload.addressPostalCode = editAddressPostalCode.trim();
  }
  if (editBirthDate.trim()) {
    payload.birthDate = editBirthDate.trim();
  }
  if (editGender.trim()) {
    payload.gender = editGender.trim();
  }
  if (editMaritalStatus.trim()) {
    payload.maritalStatus = editMaritalStatus.trim();
  }
  if (editEmployerName.trim()) {
    payload.employerName = editEmployerName.trim();
  }
  if (editEmployerHp.trim()) {
    payload.employerHp = editEmployerHp.trim();
  }
  if (editEmployerAddress.trim()) {
    payload.employerAddress = editEmployerAddress.trim();
  }
  if (editEmployerPhone.trim()) {
    payload.employerPhone = editEmployerPhone.trim();
  }

  if (Object.keys(payload).length === 0) {
    return;
  }

  setLoading(true);
  updateClient(selectedClient.id, payload)
    .then((updated) => {
      setClientDetailsMap((prev) => ({
        ...prev,
        [updated.id]: updated,
      }));
      setSelectedClient((prev) =>
        prev && prev.id === updated.id
          ? {
              ...prev,
              fullName: updated.fullName,
              idNumber: updated.idNumber,
            }
          : prev
      );
      setClients((prev) =>
        prev.map((item) =>
          item.id === updated.id
            ? {
                ...item,
                fullName: updated.fullName,
                idNumber: updated.idNumber,
              }
            : item
        )
      );
      setError(null);
    })
    .catch(() => {
      setError("שגיאה בעדכון פרטי הלקוח");
    })
    .finally(() => {
      setLoading(false);
    });
}

export type DeleteClientArgs = {
  selectedClient: ClientSummary | null;
  setLoading: Dispatch<SetStateAction<boolean>>;
  setClients: Dispatch<SetStateAction<ClientSummary[]>>;
  setClientDetailsMap: Dispatch<SetStateAction<Record<number, Client>>>;
  setSnapshots: Dispatch<SetStateAction<Snapshot[]>>;
  setSelectedSnapshot: Dispatch<SetStateAction<Snapshot | null>>;
  setClientHistory: Dispatch<SetStateAction<HistoryPoint[]>>;
  setFundHistory: Dispatch<SetStateAction<FundHistoryPoint[]>>;
  setNotes: Dispatch<SetStateAction<ClientNote[]>>;
  setReminders: Dispatch<SetStateAction<Reminder[]>>;
  setSelectedClient: Dispatch<SetStateAction<ClientSummary | null>>;
  setViewMode: Dispatch<SetStateAction<ViewMode>>;
  setError: Dispatch<SetStateAction<string | null>>;
};

export function deleteClientAction({
  selectedClient,
  setLoading,
  setClients,
  setClientDetailsMap,
  setSnapshots,
  setSelectedSnapshot,
  setClientHistory,
  setFundHistory,
  setNotes,
  setReminders,
  setSelectedClient,
  setViewMode,
  setError,
}: DeleteClientArgs) {
  if (!selectedClient) {
    return;
  }

  const confirmDelete = window.confirm(
    "האם אתה בטוח שברצונך למחוק את הלקוח וכל הנתונים הקשורים אליו?"
  );
  if (!confirmDelete) {
    return;
  }

  const clientId = selectedClient.id;
  setLoading(true);
  deleteClient(clientId)
    .then(() => {
      setClients((prev) => prev.filter((client) => client.id !== clientId));
      setClientDetailsMap((prev) => {
        const next = { ...prev };
        delete next[clientId];
        return next;
      });
      setSnapshots([]);
      setSelectedSnapshot(null);
      setClientHistory([]);
      setFundHistory([]);
      setNotes([]);
      setReminders((prev) =>
        prev.filter((reminder) => reminder.clientId !== clientId)
      );
      setSelectedClient(null);
      setViewMode("main");
      setError(null);
    })
    .catch(() => {
      setError("שגיאה במחיקת הלקוח");
    })
    .finally(() => {
      setLoading(false);
    });
}
