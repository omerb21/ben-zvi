import { useEffect, useState, ChangeEvent } from "react";
import type { CSSProperties } from "react";
import {
  Client,
  ClientSummary,
  Snapshot,
  ClientNote,
  Reminder,
  SummaryResponse,
  ClientUpdatePayload,
  MonthlyChangePoint,
  ClientCreatePayload,
  SnapshotCreatePayload,
  HistoryPoint,
  FundHistoryPoint,
  fetchClientSummaries,
  fetchClientSnapshots,
  fetchClientNotes,
  fetchReminders,
  fetchSummary,
  fetchMonthlyChange,
  fetchHistory,
  fetchFundHistory,
  createClientNote,
  fetchClients,
  fetchClient,
  updateClient,
  dismissClientNote,
  clearNoteReminder,
  deleteClientNote,
  deleteClient,
  createClient,
  createSnapshotForClient,
} from "../api/crmApi";
import httpClient from "../api/httpClient";
import { importCrmExcel, clearCrmData } from "../api/adminApi";
import "../styles/crm.css";

function escapeCsvValue(value: string): string {
	const text = value ?? "";
	if (/[",\r\n]/.test(text)) {
		return `"${text.replace(/"/g, '""')}"`;
	}
	return text;
}

type Props = {
  onOpenJustification?: (clientId: number) => void;
};

function buildHistoryChartData(history: HistoryPoint[]): {
  path: string;
  points: { x: number; y: number }[];
} {
  if (!history || history.length < 2) {
    return { path: "", points: [] };
  }

  const maxAmount = Math.max(...history.map((point) => point.amount || 0));
  if (!Number.isFinite(maxAmount) || maxAmount <= 0) {
    return { path: "", points: [] };
  }

  const count = history.length;
  const points = history.map((point, index) => {
    const ratio = (point.amount || 0) / maxAmount;
    const x = count === 1 ? 50 : (index / (count - 1)) * 100;
    const y = 95 - ratio * 80;
    return { x, y };
  });

  const path = points
    .map((p, index) => `${index === 0 ? "M" : "L"} ${p.x},${p.y}`)
    .join(" ");

  return { path, points };
}

function buildMonthlyChangeChartData(points: MonthlyChangePoint[]): {
  path: string;
  points: { x: number; y: number }[];
} {
  if (!points || points.length < 2) {
    return { path: "", points: [] };
  }

  const maxTotal = Math.max(...points.map((p) => p.total || 0));
  if (!Number.isFinite(maxTotal) || maxTotal <= 0) {
    return { path: "", points: [] };
  }

  const count = points.length;
  const scaled = points.map((point, index) => {
    const ratio = (point.total || 0) / maxTotal;
    const x = count === 1 ? 50 : (index / (count - 1)) * 100;
    const y = 95 - ratio * 80;
    return { x, y };
  });

  const path = scaled
    .map((p, index) => `${index === 0 ? "M" : "L"} ${p.x},${p.y}`)
    .join(" ");

  return { path, points: scaled };
}

function CrmPage({ onOpenJustification }: Props) {
  const [clients, setClients] = useState<ClientSummary[]>([]);
  const [selectedClient, setSelectedClient] = useState<ClientSummary | null>(null);
  const [snapshots, setSnapshots] = useState<Snapshot[]>([]);
  const [selectedSnapshot, setSelectedSnapshot] = useState<Snapshot | null>(null);
  const [clientHistory, setClientHistory] = useState<HistoryPoint[]>([]);
  const [fundHistory, setFundHistory] = useState<FundHistoryPoint[]>([]);
  const [notes, setNotes] = useState<ClientNote[]>([]);
  const [reminders, setReminders] = useState<Reminder[]>([]);
  const [summary, setSummary] = useState<SummaryResponse | null>(null);
  const [monthlyChange, setMonthlyChange] = useState<MonthlyChangePoint[]>([]);
  const [clientDetailsMap, setClientDetailsMap] = useState<Record<number, Client>>({});
  const [clientFilter, setClientFilter] = useState("");
  const [newClientIdNumber, setNewClientIdNumber] = useState("");
  const [newClientFullName, setNewClientFullName] = useState("");
  const [newClientEmail, setNewClientEmail] = useState("");
  const [newClientPhone, setNewClientPhone] = useState("");
  const [newClientBirthDate, setNewClientBirthDate] = useState("");
  const [newClientGender, setNewClientGender] = useState("");
  const [newClientMaritalStatus, setNewClientMaritalStatus] = useState("");
  const [newClientEmployerName, setNewClientEmployerName] = useState("");
  const [newClientEmployerHp, setNewClientEmployerHp] = useState("");
  const [newClientEmployerAddress, setNewClientEmployerAddress] = useState("");
  const [newClientEmployerPhone, setNewClientEmployerPhone] = useState("");
  const [editFirstName, setEditFirstName] = useState("");
  const [editLastName, setEditLastName] = useState("");
  const [editEmail, setEditEmail] = useState("");
  const [editPhone, setEditPhone] = useState("");
  const [editBirthDate, setEditBirthDate] = useState("");
  const [editAddressStreet, setEditAddressStreet] = useState("");
  const [editAddressCity, setEditAddressCity] = useState("");
  const [editAddressPostalCode, setEditAddressPostalCode] = useState("");
  const [editGender, setEditGender] = useState("");
  const [editMaritalStatus, setEditMaritalStatus] = useState("");
  const [editEmployerName, setEditEmployerName] = useState("");
  const [editEmployerHp, setEditEmployerHp] = useState("");
  const [editEmployerAddress, setEditEmployerAddress] = useState("");
  const [editEmployerPhone, setEditEmployerPhone] = useState("");
  const [crmImportFiles, setCrmImportFiles] = useState<File[]>([]);
  const [crmImportMonth, setCrmImportMonth] = useState("");
  const [isCrmImporting, setIsCrmImporting] = useState(false);
  const [isCrmClearing, setIsCrmClearing] = useState(false);
  const [crmAdminMessage, setCrmAdminMessage] = useState<string | null>(null);
  const [crmAdminError, setCrmAdminError] = useState<string | null>(null);
  const [newNoteText, setNewNoteText] = useState("");
  const [newNoteReminder, setNewNoteReminder] = useState("");
  const [newSnapshotFundCode, setNewSnapshotFundCode] = useState("");
  const [newSnapshotFundName, setNewSnapshotFundName] = useState("");
  const [newSnapshotFundType, setNewSnapshotFundType] = useState("");
  const [newSnapshotAmount, setNewSnapshotAmount] = useState("");
  const [newSnapshotDate, setNewSnapshotDate] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [viewMode, setViewMode] = useState<"main" | "dashboard" | "clientDetail">(
    "main"
  );
  const [selectedMonth, setSelectedMonth] = useState<string | null>(null);
  const [showDashboard, setShowDashboard] = useState(false);

  useEffect(() => {
    setLoading(true);
    Promise.all([
      fetchClientSummaries(),
      fetchSummary(),
      fetchReminders(),
      fetchClients(),
      fetchMonthlyChange(),
    ])
      .then(([
        clientSummaries,
        summaryData,
        remindersData,
        clientsData,
        monthlyChangeData,
      ]) => {
        setClients(clientSummaries);
        setSummary(summaryData);
        setReminders(remindersData);
        setMonthlyChange(monthlyChangeData);
        const detailsMap: Record<number, Client> = {};
        clientsData.forEach((client) => {
          detailsMap[client.id] = client;
        });
        setClientDetailsMap(detailsMap);
        setError(null);
      })
      .catch(() => {
        setError("שגיאה בטעינת נתוני CRM");
      })
      .finally(() => {
        setLoading(false);
      });
  }, []);

  const reloadForMonth = (month: string) => {
    if (!month) {
      return;
    }
    setLoading(true);
    Promise.all([fetchClientSummaries(month), fetchSummary(month)])
      .then(([clientSummaries, summaryData]) => {
        setClients(clientSummaries);
        setSummary(summaryData);
        setSelectedMonth(summaryData.month);
        setError(null);
      })
      .catch(() => {
        setError("שגיאה בטעינת נתוני CRM");
      })
      .finally(() => {
        setLoading(false);
      });
  };

  const handleMonthInputChange = (value: string) => {
    if (!value) {
      return;
    }
    reloadForMonth(value);
  };

  const handleShiftMonth = (delta: number) => {
    const baseMonth = (selectedMonth || summary?.month || "").slice(0, 7);
    if (!baseMonth) {
      return;
    }
    const parts = baseMonth.split("-");
    if (parts.length !== 2) {
      return;
    }
    let year = parseInt(parts[0], 10);
    let month = parseInt(parts[1], 10);
    if (!Number.isFinite(year) || !Number.isFinite(month)) {
      return;
    }
    month += delta;
    if (month < 1) {
      month = 12;
      year -= 1;
    } else if (month > 12) {
      month = 1;
      year += 1;
    }
    const yearStr = year.toString().padStart(4, "0");
    const monthStr = month.toString().padStart(2, "0");
    reloadForMonth(`${yearStr}-${monthStr}`);
  };

  const effectiveMonth = selectedMonth || summary?.month || null;

  const totalClients = clients.length;
  const totalAssetsValue = clients.reduce(
    (sum, client) => sum + (client.totalAmount || 0),
    0
  );
  const totalFundsValue = clients.reduce(
    (sum, client) => sum + (client.fundCount || 0),
    0
  );
  const sourcesSet = new Set<string>();
  clients.forEach((client) => {
    if (client.rawSources && client.rawSources !== "אין נתונים") {
      client.rawSources.split(",").forEach((source) => {
        const trimmed = source.trim();
        if (trimmed) {
          sourcesSet.add(trimmed);
        }
      });
    }
  });
  const totalSourcesValue = sourcesSet.size;

  const latestSnapshotsByFund: Record<string, Snapshot> = {};
  snapshots.forEach((snapshot) => {
    const key = snapshot.fundCode;
    const existing = latestSnapshotsByFund[key];
    if (!existing || snapshot.snapshotDate > existing.snapshotDate) {
      latestSnapshotsByFund[key] = snapshot;
    }
  });
  const latestSnapshots: Snapshot[] = Object.values(latestSnapshotsByFund);

  const { path: historyChartPath, points: historyChartPoints } =
    buildHistoryChartData(clientHistory);

  const { path: monthlyTrendPath, points: monthlyTrendPoints } =
    buildMonthlyChangeChartData(monthlyChange);

  const loadClientDetails = (client: ClientSummary) => {
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
  };

  const handleSelectSnapshot = (snapshot: Snapshot) => {
    setSelectedSnapshot(snapshot);
    setFundHistory([]);

    const fundNumber = (snapshot as any).fundNumber as string | undefined;
    const fundIdentifier = fundNumber || snapshot.fundCode;
    if (!selectedClient || !fundIdentifier) {
      return;
    }

    setLoading(true);
    fetchFundHistory(selectedClient.id, fundIdentifier)
      .then((items) => {
        setFundHistory(items);
        setError(null);
      })
      .catch(() => {
        setError("שגיאה בטעינת היסטוריית קופה");
      })
      .finally(() => {
        setLoading(false);
      });
  };

  const handleCreateClient = () => {
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
  };

  const handleSaveClientDetails = () => {
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
  };

  const handleDeleteClient = () => {
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
  };

  const handleDismissNote = (noteId: number) => {
    if (!selectedClient) {
      return;
    }

    dismissClientNote(selectedClient.id, noteId)
      .then((updated) => {
        setNotes((prev) =>
          prev.map((note) => (note.id === updated.id ? updated : note))
        );
        setError(null);
      })
      .catch(() => {
        setError("שגיאה בסגירת תזכורת");
      });
  };

  const handleClearNoteReminder = (noteId: number) => {
    if (!selectedClient) {
      return;
    }

    clearNoteReminder(selectedClient.id, noteId)
      .then((updated) => {
        setNotes((prev) =>
          prev.map((note) => (note.id === updated.id ? updated : note))
        );
        setError(null);
      })
      .catch(() => {
        setError("שגיאה באיפוס תזכורת");
      });
  };

  const handleDeleteNote = (noteId: number) => {
    if (!selectedClient) {
      return;
    }

    deleteClientNote(selectedClient.id, noteId)
      .then(() => {
        setNotes((prev) => prev.filter((note) => note.id !== noteId));
        setError(null);
      })
      .catch(() => {
        setError("שגיאה במחיקת הערה");
      });
  };

  const handleExportClientReport = () => {
    if (!selectedClient || latestSnapshots.length === 0) {
      return;
    }

    const headers = [
      "תאריך צילום",
      "קוד קופה",
      "שם קופה",
      "סוג קופה",
      "סכום",
      "מקור",
    ];

    const rows = latestSnapshots.map((snapshot) => {
      const fundName = (snapshot as any).fundName || "";
      const fundType = (snapshot as any).fundType || "";
      const source = (snapshot as any).source || "";
      return [
        snapshot.snapshotDate || "",
        snapshot.fundCode || "",
        fundName,
        fundType,
        (snapshot.amount ?? 0).toString(),
        source,
      ];
    });

    const lines = [
      headers.map(escapeCsvValue).join(","),
      ...rows.map((row) => row.map(escapeCsvValue).join(",")),
    ];

    const csvContent = "\uFEFF" + lines.join("\r\n");
    const blob = new Blob([csvContent], {
      type: "text/csv;charset=utf-8;",
    });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    const safeName = (selectedClient.fullName || selectedClient.idNumber || "client").replace(
      /[^a-zA-Z0-9\u0590-\u05FF]+/g,
      "_"
    );
    link.href = url;
    link.download = `client_report_${safeName}.csv`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  };

  const handleExportClientPdf = () => {
    if (!selectedClient || latestSnapshots.length === 0) {
      return;
    }

    const baseUrl = (httpClient.defaults.baseURL || "").replace(/\/+$/, "");
    const reportUrl = `${baseUrl}/api/v1/crm/clients/${selectedClient.id}/report.pdf`;
    window.open(reportUrl, "_blank");
  };

  const handleCrmFileChange = (event: ChangeEvent<HTMLInputElement>) => {
    const files = event.target.files;
    if (!files || files.length === 0) {
      setCrmImportFiles([]);
      return;
    }
    const nextFiles: File[] = [];
    for (let i = 0; i < files.length; i += 1) {
      nextFiles.push(files[i]);
    }
    setCrmImportFiles(nextFiles);
  };

  const handleRunCrmImport = () => {
    if (
      crmImportFiles.length === 0 ||
      !crmImportMonth ||
      isCrmImporting ||
      isCrmClearing
    ) {
      return;
    }
    setIsCrmImporting(true);
    setCrmAdminMessage(null);
    setCrmAdminError(null);
    Promise.all(crmImportFiles.map((file) => importCrmExcel(file, crmImportMonth)))
      .then((results) => {
        if (results.length === 0) {
          return;
        }

        const aggregated = results.reduce(
          (acc, current) => {
            return {
              companyCode: current.companyCode,
              createdClients: acc.createdClients + current.createdClients,
              reusedClients: acc.reusedClients + current.reusedClients,
              createdSnapshots: acc.createdSnapshots + current.createdSnapshots,
              rowsProcessed: acc.rowsProcessed + current.rowsProcessed,
              duplicatesSkipped: acc.duplicatesSkipped + current.duplicatesSkipped,
            };
          },
          {
            companyCode: results[0].companyCode,
            createdClients: 0,
            reusedClients: 0,
            createdSnapshots: 0,
            rowsProcessed: 0,
            duplicatesSkipped: 0,
          }
        );

        setCrmAdminMessage(
          `ייבוא CRM (Excel) מתוך ${results.length} קבצים: נוצרו ${aggregated.createdClients} לקוחות, נעשה שימוש חוזר ב-${aggregated.reusedClients} לקוחות, נוצרו ${aggregated.createdSnapshots} צילומים (שורות: ${aggregated.rowsProcessed}, כפילויות שדולגו: ${aggregated.duplicatesSkipped})`
        );
      })
      .catch((error: any) => {
        const detail = error?.response?.data?.detail || error?.message;
        setCrmAdminError(detail || "שגיאה בייבוא CRM מקובצי Excel");
      })
      .finally(() => {
        setIsCrmImporting(false);
      });
  };

  const handleClearCrmDataLocal = () => {
    if (isCrmImporting || isCrmClearing) {
      return;
    }
    // eslint-disable-next-line no-alert
    const confirmed = window.confirm(
      "האם אתה בטוח שברצונך למחוק את כל נתוני ה-CRM (צילומים ותזכורות)?"
    );
    if (!confirmed) {
      return;
    }

    setIsCrmClearing(true);
    setCrmAdminMessage(null);
    setCrmAdminError(null);
    clearCrmData()
      .then((result) => {
        setCrmAdminMessage(
          `נמחקו נתוני CRM: ${result.deletedSnapshots} צילומים ו-${result.deletedClientNotes} תזכורות`
        );
      })
      .catch(() => {
        setCrmAdminError("שגיאה במחיקת נתוני CRM");
      })
      .finally(() => {
        setIsCrmClearing(false);
      });
  };

  const handleReminderGoToClient = (reminder: Reminder) => {
    const client = clients.find((c) => c.id === reminder.clientId) || null;
    if (!client) {
      return;
    }
    loadClientDetails(client);
  };

  const handleDismissReminder = (reminder: Reminder) => {
    dismissClientNote(reminder.clientId, reminder.id)
      .then(() => {
        setReminders((prev) => prev.filter((r) => r.id !== reminder.id));
        setError(null);
      })
      .catch(() => {
        setError("שגיאה בסגירת תזכורת");
      });
  };

  const handleClearReminderFromGlobal = (reminder: Reminder) => {
    clearNoteReminder(reminder.clientId, reminder.id)
      .then(() => {
        setReminders((prev) => prev.filter((r) => r.id !== reminder.id));
        setError(null);
      })
      .catch(() => {
        setError("שגיאה באיפוס תזכורת");
      });
  };

  const handleCreateSnapshot = () => {
    if (!selectedClient) {
      return;
    }

    const fundCode = newSnapshotFundCode.trim();
    const amountText = newSnapshotAmount.trim();
    const snapshotDate = newSnapshotDate.trim();

    if (!fundCode || !amountText || !snapshotDate) {
      return;
    }

    const amount = Number(amountText.replace(/,/g, ""));
    if (!Number.isFinite(amount)) {
      return;
    }

    const payload: SnapshotCreatePayload = {
      fundCode,
      amount,
      snapshotDate,
    };

    if (newSnapshotFundType.trim()) {
      payload.fundType = newSnapshotFundType.trim();
    }
    if (newSnapshotFundName.trim()) {
      payload.fundName = newSnapshotFundName.trim();
    }

    setLoading(true);
    createSnapshotForClient(selectedClient.id, payload)
      .then((created) => {
        setSnapshots((prev) => [created, ...prev]);
        setNewSnapshotFundCode("");
        setNewSnapshotFundName("");
        setNewSnapshotFundType("");
        setNewSnapshotAmount("");
        setNewSnapshotDate("");
        setError(null);
      })
      .catch(() => {
        setError("שגיאה ביצירת צילום מוצר");
      })
      .finally(() => {
        setLoading(false);
      });
  };

  const handleSubmitNote = (event: React.FormEvent) => {
    event.preventDefault();
    if (!selectedClient || !newNoteText.trim()) {
      return;
    }

    createClientNote(selectedClient.id, {
      note: newNoteText.trim(),
      reminderAt: newNoteReminder || undefined,
    })
      .then((created) => {
        setNotes((prev) => [created, ...prev]);
        setNewNoteText("");
        setNewNoteReminder("");
      })
      .catch(() => {
        setError("שגיאה ביצירת הערה חדשה");
      });
  };
  return (
    <div className="crm-page-root">
      {summary && (
        <section className="crm-panel crm-summary-panel">
          <div className="crm-summary-header">
            <div className="crm-month-controls">
              <button
                type="button"
                className="crm-month-button"
                onClick={() => handleShiftMonth(-1)}
              >
                חודש קודם
              </button>
              <div className="crm-month-input-wrapper">
                <div className="crm-summary-label">חודש הצגה</div>
                <input
                  type="month"
                  className="crm-month-input"
                  value={effectiveMonth || ""}
                  onChange={(e) => handleMonthInputChange(e.target.value)}
                />
              </div>
              <button
                type="button"
                className="crm-month-button"
                onClick={() => handleShiftMonth(1)}
              >
                חודש הבא
              </button>
            </div>
            <button
              type="button"
              className="crm-dashboard-toggle"
              onClick={() =>
                setViewMode(viewMode === "dashboard" ? "main" : "dashboard")
              }
            >
              {viewMode === "dashboard" ? "חזרה לרשימת לקוחות" : "דשבורד"}
            </button>
          </div>

          <div className="crm-summary-cards">
            <div className="crm-summary-card crm-summary-card-primary">
              <div className="crm-summary-card-label">סה"כ לקוחות</div>
              <div className="crm-summary-card-value">
                {totalClients.toLocaleString()}
              </div>
            </div>
            <div className="crm-summary-card crm-summary-card-success">
              <div className="crm-summary-card-label">סה"כ נכסים</div>
              <div className="crm-summary-card-value">
                {totalAssetsValue.toLocaleString()}
              </div>
            </div>
            <div className="crm-summary-card crm-summary-card-info">
              <div className="crm-summary-card-label">סה"כ קופות</div>
              <div className="crm-summary-card-value">
                {totalFundsValue.toLocaleString()}
              </div>
            </div>
            <div className="crm-summary-card crm-summary-card-warning">
              <div className="crm-summary-card-label">מקורות נתונים</div>
              <div className="crm-summary-card-value">
                {totalSourcesValue.toLocaleString()}
              </div>
            </div>
          </div>
        </section>
      )}

      <div className="crm-page">
        {viewMode === "main" && (
        <section className="crm-panel crm-panel-left">
          <h2 className="panel-title">לקוחות</h2>
          {loading && <div className="status-text">טוען נתונים…</div>}
          {error && <div className="status-text status-error">{error}</div>}
          <div className="crm-new-client">
            <div className="crm-new-client-grid">
              <input
                type="text"
                className="crm-new-client-input"
                placeholder="תעודת זהות"
                value={newClientIdNumber}
                onChange={(e) => setNewClientIdNumber(e.target.value)}
              />
              <input
                type="text"
                className="crm-new-client-input"
                placeholder="שם מלא"
                value={newClientFullName}
                onChange={(e) => setNewClientFullName(e.target.value)}
              />
              <input
                type="text"
                className="crm-new-client-input"
                placeholder="טלפון"
                value={newClientPhone}
                onChange={(e) => setNewClientPhone(e.target.value)}
              />
              <input
                type="email"
                className="crm-new-client-input"
                placeholder="אימייל"
                value={newClientEmail}
                onChange={(e) => setNewClientEmail(e.target.value)}
              />
              <input
                type="date"
                className="crm-new-client-input"
                placeholder="תאריך לידה"
                value={newClientBirthDate}
                onChange={(e) => setNewClientBirthDate(e.target.value)}
              />
              <select
                className="crm-new-client-input"
                value={newClientGender}
                onChange={(e) => setNewClientGender(e.target.value)}
              >
                <option value="">מין</option>
                <option value="male">זכר</option>
                <option value="female">נקבה</option>
              </select>
              <select
                className="crm-new-client-input"
                value={newClientMaritalStatus}
                onChange={(e) => setNewClientMaritalStatus(e.target.value)}
              >
                <option value="">סטטוס משפחתי</option>
                <option value="single">
                  רווק/ה
                </option>
                <option value="married">נשוי/אה</option>
                <option value="divorced">גרוש/ה</option>
                <option value="widowed">אלמן/ה</option>
              </select>
              <input
                type="text"
                className="crm-new-client-input"
                placeholder="שם מעסיק"
                value={newClientEmployerName}
                onChange={(e) => setNewClientEmployerName(e.target.value)}
              />
              <input
                type="text"
                className="crm-new-client-input"
                placeholder="ח.פ מעסיק"
                value={newClientEmployerHp}
                onChange={(e) => setNewClientEmployerHp(e.target.value)}
              />
              <input
                type="text"
                className="crm-new-client-input"
                placeholder="כתובת מעסיק"
                value={newClientEmployerAddress}
                onChange={(e) => setNewClientEmployerAddress(e.target.value)}
              />
              <input
                type="tel"
                className="crm-new-client-input"
                placeholder="טלפון מעסיק"
                value={newClientEmployerPhone}
                onChange={(e) => setNewClientEmployerPhone(e.target.value)}
              />
            </div>
            <button
              type="button"
              className="crm-new-client-button"
              onClick={handleCreateClient}
            >
              יצירת לקוח
            </button>
          </div>
          <div className="crm-client-search">
            <input
              type="text"
              className="crm-client-search-input"
              placeholder="חיפוש לפי שם או תעודת זהות"
              value={clientFilter}
              onChange={(e) => setClientFilter(e.target.value)}
            />
          </div>
          <ul className="client-list">
            {clients
              .filter((client) => {
                const term = clientFilter.trim();
                if (!term) {
                  return true;
                }
                return (
                  client.fullName.includes(term) ||
                  client.idNumber.includes(term)
                );
              })
              .map((client) => (
                <li
                  key={client.id}
                  className={
                    selectedClient && selectedClient.id === client.id
                      ? "client-item client-item-selected"
                      : "client-item"
                  }
                  onClick={() => loadClientDetails(client)}
                >
                  <div className="client-name">{client.fullName}</div>
                  <div className="client-id">{client.idNumber}</div>
                  <div className="client-meta-row">
                    <span>
                      {client.totalAmount
                        ? client.totalAmount.toLocaleString()
                        : "0"}
                    </span>
                    <span className="client-meta-small">
                      {client.fundCount} קופות
                    </span>
                  </div>
                </li>
              ))}
          </ul>
        </section>
        )}

        {viewMode === "dashboard" && summary && (
        <section className="crm-panel crm-dashboard-panel">
          <h2 className="panel-title">דשבורד תיק לקוחות</h2>
          {crmAdminMessage && (
            <div className="admin-import-status">{crmAdminMessage}</div>
          )}
          {crmAdminError && (
            <div className="admin-import-status admin-import-status-error">
              {crmAdminError}
            </div>
          )}
          <div className="crm-dashboard-grid">
            <div className="crm-dashboard-card crm-dashboard-import-card">
              <div className="crm-dashboard-card-header">
                <div className="crm-dashboard-card-title">ניהול קבצי CRM (Excel)</div>
              </div>
              <div className="crm-dashboard-card-body">
                <div className="admin-import-group crm-admin-import-group">
                  <input
                    type="month"
                    className="admin-import-month"
                    value={crmImportMonth}
                    onChange={(event) => setCrmImportMonth(event.target.value)}
                  />
                  <input
                    type="file"
                    accept=".xls,.xlsx"
                    multiple
                    className="admin-import-file"
                    onChange={handleCrmFileChange}
                  />
                  <button
                    type="button"
                    className="admin-import-button"
                    onClick={handleRunCrmImport}
                    disabled={
                      crmImportFiles.length === 0 ||
                      !crmImportMonth ||
                      isCrmImporting ||
                      isCrmClearing
                    }
                  >
                    ייבוא CRM (Excel)
                  </button>
                  <button
                    type="button"
                    className="admin-import-button"
                    onClick={handleClearCrmDataLocal}
                    disabled={isCrmImporting || isCrmClearing}
                  >
                    מחיקת נתוני CRM
                  </button>
                </div>
              </div>
            </div>
            <div className="crm-dashboard-card">
              <div className="crm-dashboard-card-header">
                <div className="crm-dashboard-card-title">התפלגות לפי מקור</div>
              </div>
              <div className="crm-dashboard-card-body">
                {summary && Object.keys(summary.bySource || {}).length > 0 ? (
                  Object.entries(summary.bySource || {}).map(([key, value]) => {
                    const total = Object.values(summary.bySource || {}).reduce(
                      (acc, v) => acc + (v || 0),
                      0
                    );
                    const ratio = total > 0 ? (value || 0) / total : 0;
                    const percent = Math.round(ratio * 100);
                    return (
                      <div
                        key={key || "unknown"}
                        className="crm-dashboard-bar-row"
                      >
                        <div className="crm-dashboard-bar-label">{key || "לא זמין"}</div>
                        <div className="crm-dashboard-bar-value">
                          {value?.toLocaleString() || "0"} ₪ ({percent}%)
                        </div>
                        <div className="crm-dashboard-bar-track">
                          <div
                            className="crm-dashboard-bar-fill"
                            style={{ "--crm-bar-width": `${Math.max(5, percent)}%` } as CSSProperties}
                          />
                        </div>
                      </div>
                    );
                  })
                ) : (
                  <div className="crm-dashboard-empty">אין נתונים להצגה</div>
                )}
              </div>
            </div>

            <div className="crm-dashboard-card">
              <div className="crm-dashboard-card-header">
                <div className="crm-dashboard-card-title">התפלגות לפי סוג מוצר</div>
              </div>
              <div className="crm-dashboard-card-body">
                {summary && Object.keys(summary.byFundType || {}).length > 0 ? (
                  Object.entries(summary.byFundType || {}).map(([key, value]) => {
                    const total = Object.values(summary.byFundType || {}).reduce(
                      (acc, v) => acc + (v || 0),
                      0
                    );
                    const ratio = total > 0 ? (value || 0) / total : 0;
                    const percent = Math.round(ratio * 100);
                    return (
                      <div
                        key={key || "unknown"}
                        className="crm-dashboard-bar-row"
                      >
                        <div className="crm-dashboard-bar-label">{key || "לא זמין"}</div>
                        <div className="crm-dashboard-bar-value">
                          {value?.toLocaleString() || "0"} ₪ ({percent}%)
                        </div>
                        <div className="crm-dashboard-bar-track">
                          <div
                            className="crm-dashboard-bar-fill crm-dashboard-bar-fill-type"
                            style={{ "--crm-bar-width": `${Math.max(5, percent)}%` } as CSSProperties}
                          />
                        </div>
                      </div>
                    );
                  })
                ) : (
                  <div className="crm-dashboard-empty">אין נתונים להצגה</div>
                )}
              </div>
            </div>

            <div className="crm-dashboard-card">
              <div className="crm-dashboard-card-header">
                <div className="crm-dashboard-card-title">מגמת נכסים חודשית</div>
              </div>
              <div className="crm-dashboard-card-body">
                {monthlyTrendPoints.length >= 2 ? (
                  <div className="crm-dashboard-trend">
                    <svg
                      viewBox="0 0 100 100"
                      className="crm-dashboard-trend-svg"
                      preserveAspectRatio="none"
                    >
                      <path
                        d={monthlyTrendPath}
                        className="crm-dashboard-trend-line"
                      />
                      {monthlyTrendPoints.map((point, index) => (
                        <circle
                          key={`${point.x}-${point.y}-${index}`}
                          cx={point.x}
                          cy={point.y}
                          r={1.7}
                          className="crm-dashboard-trend-point"
                        />
                      ))}
                    </svg>
                    <ul className="crm-dashboard-trend-list">
                      {monthlyChange.map((item) => (
                        <li key={item.month}>
                          <span>{item.month}</span>
                          <span>
                            {item.total.toLocaleString()} ₪
                          </span>
                        </li>
                      ))}
                    </ul>
                  </div>
                ) : (
                  <div className="crm-dashboard-empty">אין מספיק היסטוריה להצגת גרף</div>
                )}
              </div>
            </div>
          </div>
        </section>
        )}

        {viewMode === "clientDetail" && (
        <section className="crm-panel crm-panel-right">
          <div className="crm-client-detail-header">
            <button
              type="button"
              className="crm-client-detail-back"
              onClick={() => setViewMode("main")}
            >
              חזרה לרשימת לקוחות
            </button>
            {selectedClient && (
              <>
                {onOpenJustification && (
                  <button
                    type="button"
                    className="crm-client-justify-button"
                    onClick={() => onOpenJustification(selectedClient.id)}
                  >
                    מעבר למסך ההנמקה
                  </button>
                )}
                <button
                  type="button"
                  className="crm-client-delete-button"
                  onClick={handleDeleteClient}
                >
                  מחיקת לקוח
                </button>
              </>
            )}
          </div>
          <h2 className="panel-title">מוצרים והערות ללקוח</h2>
          {selectedClient ? (
            <div className="snapshots-wrapper">
              <div className="snapshots-header">
                <div className="snapshots-client-name">{selectedClient.fullName}</div>
                <div className="snapshots-client-id">{selectedClient.idNumber}</div>
              </div>
              <div className="crm-client-edit">
                <h3 className="panel-subtitle">פרטי לקוח</h3>
                <div className="crm-client-edit-grid">
                  <div className="crm-client-edit-field">
                    <label className="crm-client-edit-label">שם פרטי</label>
                    <input
                      type="text"
                      className="crm-client-edit-input"
                      value={editFirstName}
                      onChange={(e) => setEditFirstName(e.target.value)}
                    />
                  </div>
                  <div className="crm-client-edit-field">
                    <label className="crm-client-edit-label">שם משפחה</label>
                    <input
                      type="text"
                      className="crm-client-edit-input"
                      value={editLastName}
                      onChange={(e) => setEditLastName(e.target.value)}
                    />
                  </div>
                  <div className="crm-client-edit-field">
                    <label className="crm-client-edit-label">טלפון</label>
                    <input
                      type="tel"
                      className="crm-client-edit-input"
                      value={editPhone}
                      onChange={(e) => setEditPhone(e.target.value)}
                    />
                  </div>
                  <div className="crm-client-edit-field">
                    <label className="crm-client-edit-label">אימייל</label>
                    <input
                      type="email"
                      className="crm-client-edit-input"
                      value={editEmail}
                      onChange={(e) => setEditEmail(e.target.value)}
                    />
                  </div>
                  <div className="crm-client-edit-field">
                    <label className="crm-client-edit-label">תאריך לידה</label>
                    <input
                      type="date"
                      className="crm-client-edit-input"
                      value={editBirthDate}
                      onChange={(e) => setEditBirthDate(e.target.value)}
                    />
                  </div>
                  <div className="crm-client-edit-field">
                    <label className="crm-client-edit-label">רחוב</label>
                    <input
                      type="text"
                      className="crm-client-edit-input"
                      value={editAddressStreet}
                      onChange={(e) => setEditAddressStreet(e.target.value)}
                    />
                  </div>
                  <div className="crm-client-edit-field">
                    <label className="crm-client-edit-label">עיר</label>
                    <input
                      type="text"
                      className="crm-client-edit-input"
                      value={editAddressCity}
                      onChange={(e) => setEditAddressCity(e.target.value)}
                    />
                  </div>
                  <div className="crm-client-edit-field">
                    <label className="crm-client-edit-label">מיקוד</label>
                    <input
                      type="text"
                      className="crm-client-edit-input"
                      value={editAddressPostalCode}
                      onChange={(e) =>
                        setEditAddressPostalCode(e.target.value)
                      }
                    />
                  </div>
                  <div className="crm-client-edit-field">
                    <label className="crm-client-edit-label">מין</label>
                    <select
                      className="crm-client-edit-input"
                      value={editGender}
                      onChange={(e) => setEditGender(e.target.value)}
                    >
                      <option value="">לא מוגדר</option>
                      <option value="male">זכר</option>
                      <option value="female">נקבה</option>
                    </select>
                  </div>
                  <div className="crm-client-edit-field">
                    <label className="crm-client-edit-label">סטטוס משפחתי</label>
                    <select
                      className="crm-client-edit-input"
                      value={editMaritalStatus}
                      onChange={(e) => setEditMaritalStatus(e.target.value)}
                    >
                      <option value="">לא מוגדר</option>
                      <option value="single">רווק/ה</option>
                      <option value="married">נשוי/אה</option>
                      <option value="divorced">גרוש/ה</option>
                      <option value="widowed">אלמן/ה</option>
                    </select>
                  </div>
                  <div className="crm-client-edit-field">
                    <label className="crm-client-edit-label">שם מעסיק</label>
                    <input
                      type="text"
                      className="crm-client-edit-input"
                      value={editEmployerName}
                      onChange={(e) => setEditEmployerName(e.target.value)}
                    />
                  </div>
                  <div className="crm-client-edit-field">
                    <label className="crm-client-edit-label">ח.פ מעסיק</label>
                    <input
                      type="text"
                      className="crm-client-edit-input"
                      value={editEmployerHp}
                      onChange={(e) => setEditEmployerHp(e.target.value)}
                    />
                  </div>
                  <div className="crm-client-edit-field">
                    <label className="crm-client-edit-label">כתובת מעסיק</label>
                    <input
                      type="text"
                      className="crm-client-edit-input"
                      value={editEmployerAddress}
                      onChange={(e) =>
                        setEditEmployerAddress(e.target.value)
                      }
                    />
                  </div>
                  <div className="crm-client-edit-field">
                    <label className="crm-client-edit-label">טלפון מעסיק</label>
                    <input
                      type="tel"
                      className="crm-client-edit-input"
                      value={editEmployerPhone}
                      onChange={(e) => setEditEmployerPhone(e.target.value)}
                    />
                  </div>
                </div>
                <button
                  type="button"
                  className="crm-client-edit-button"
                  onClick={handleSaveClientDetails}
                >
                  שמירת פרטי לקוח
                </button>
              </div>
              <div className="crm-snapshot-create">
                <div className="crm-snapshot-create-grid">
                  <input
                    type="text"
                    className="crm-snapshot-input"
                    placeholder="קוד קופה"
                    value={newSnapshotFundCode}
                    onChange={(e) => setNewSnapshotFundCode(e.target.value)}
                  />
                  <input
                    type="text"
                    className="crm-snapshot-input"
                    placeholder="שם קופה"
                    value={newSnapshotFundName}
                    onChange={(e) => setNewSnapshotFundName(e.target.value)}
                  />
                  <input
                    type="text"
                    className="crm-snapshot-input"
                    placeholder="סוג קופה"
                    value={newSnapshotFundType}
                    onChange={(e) => setNewSnapshotFundType(e.target.value)}
                  />
                  <input
                    type="text"
                    className="crm-snapshot-input"
                    placeholder="סכום"
                    value={newSnapshotAmount}
                    onChange={(e) => setNewSnapshotAmount(e.target.value)}
                  />
                  <input
                    type="date"
                    className="crm-snapshot-input"
                    value={newSnapshotDate}
                    onChange={(e) => setNewSnapshotDate(e.target.value)}
                  />
                  <button
                    type="button"
                    className="crm-snapshot-button"
                    onClick={handleCreateSnapshot}
                  >
                    יצירת צילום
                  </button>
                </div>
                {latestSnapshots.length > 0 && (
                  <div className="crm-snapshot-actions">
                    <button
                      type="button"
                      className="crm-snapshot-export-button"
                      onClick={handleExportClientReport}
                    >
                      הורדת דוח לקוח (CSV)
                    </button>
                    <button
                      type="button"
                      className="crm-snapshot-export-button crm-snapshot-export-button-secondary"
                      onClick={handleExportClientPdf}
                    >
                      דוח PDF
                    </button>
                  </div>
                )}
              </div>
              <table className="snapshot-table">
                <thead>
                  <tr>
                    <th>תאריך צילום</th>
                    <th>קוד קופה</th>
                    <th>שם קופה</th>
                    <th>סוג קופה</th>
                    <th>סכום</th>
                  </tr>
                </thead>
                <tbody>
                  {latestSnapshots.map((snapshot) => (
                    <tr
                      key={snapshot.id}
                      className={
                        selectedSnapshot && selectedSnapshot.id === snapshot.id
                          ? "snapshot-row snapshot-row-selected"
                          : "snapshot-row"
                      }
                      onClick={() => handleSelectSnapshot(snapshot)}
                    >
                      <td>{snapshot.snapshotDate}</td>
                      <td>{snapshot.fundCode}</td>
                      <td>{snapshot.fundName}</td>
                      <td>{snapshot.fundType}</td>
                      <td>{snapshot.amount.toLocaleString()}</td>
                    </tr>
                  ))}
                  {latestSnapshots.length === 0 && !loading && (
                    <tr>
                      <td colSpan={5} className="status-text">
                        אין נתוני מוצרים ללקוח
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>

              <div className="crm-history-section">
                <h3 className="panel-subtitle">היסטוריה חודשית ללקוח</h3>
                <ul className="crm-history-list">
                  {clientHistory.map((point) => (
                    <li key={point.month}>
                      <span>{point.month}</span>
                      <span>{point.amount.toLocaleString()}</span>
                    </li>
                  ))}
                  {clientHistory.length === 0 && !loading && (
                    <li className="status-text">אין היסטוריה ללקוח</li>
                  )}
                </ul>
                {historyChartPoints.length >= 2 && (
                  <div className="crm-history-chart">
                    <svg
                      viewBox="0 0 100 100"
                      className="crm-history-chart-svg"
                      preserveAspectRatio="none"
                    >
                      <path
                        d={historyChartPath}
                        className="crm-history-chart-line"
                      />
                      {historyChartPoints.map((point, index) => (
                        <circle
                          key={`${point.x}-${point.y}-${index}`}
                          cx={point.x}
                          cy={point.y}
                          r={1.5}
                          className="crm-history-chart-point"
                        />
                      ))}
                    </svg>
                  </div>
                )}
              </div>

              <div className="crm-history-fund">
                <h3 className="panel-subtitle">היסטוריית קופה</h3>
                {selectedSnapshot ? (
                  <div>
                    <div className="crm-history-fund-header">
                      <span>{selectedSnapshot.fundName}</span>
                      <span>{selectedSnapshot.fundCode}</span>
                    </div>
                    <table className="crm-history-fund-table">
                      <thead>
                        <tr>
                          <th>תאריך</th>
                          <th>סכום</th>
                          <th>מקור</th>
                          <th>שינוי</th>
                        </tr>
                      </thead>
                      <tbody>
                        {fundHistory.map((row) => (
                          <tr key={row.date + row.source}>
                            <td>{row.date}</td>
                            <td>{row.amount.toLocaleString()}</td>
                            <td>{row.source}</td>
                            <td>
                              {row.change === null || row.change === undefined
                                ? "-"
                                : row.change.toLocaleString()}
                            </td>
                          </tr>
                        ))}
                        {fundHistory.length === 0 && !loading && (
                          <tr>
                            <td colSpan={4} className="status-text">
                              אין היסטוריה לקופה שנבחרה
                            </td>
                          </tr>
                        )}
                      </tbody>
                    </table>
                  </div>
                ) : (
                  <div className="status-text">בחר שורת צילום להצגת היסטוריית קופה</div>
                )}
              </div>

              <div className="crm-notes-section">
                <h3 className="panel-subtitle">הערות ותזכורות</h3>
                <form className="crm-note-form" onSubmit={handleSubmitNote}>
                  <textarea
                    className="crm-note-input"
                    value={newNoteText}
                    onChange={(e) => setNewNoteText(e.target.value)}
                    placeholder="הוסף הערה ללקוח..."
                  />
                  <div className="crm-note-form-row">
                    <input
                      type="date"
                      className="crm-note-date"
                      value={newNoteReminder}
                      onChange={(e) => setNewNoteReminder(e.target.value)}
                    />
                    <button type="submit" className="crm-note-button">
                      שמירת הערה
                    </button>
                  </div>
                </form>

                <ul className="crm-notes-list">
                  {notes.map((note) => (
                    <li key={note.id} className="crm-note-item">
                      <div className="crm-note-text">{note.note}</div>
                      <div className="crm-note-meta">
                        <span>{note.createdAt}</span>
                        {note.reminderAt && (
                          <span>תזכורת: {note.reminderAt}</span>
                        )}
                        {note.dismissedAt && (
                          <span>נסגרה: {note.dismissedAt}</span>
                        )}
                      </div>
                      <div className="crm-note-actions">
                        <button
                          type="button"
                          className="crm-note-action-button"
                          onClick={() => handleDismissNote(note.id)}
                        >
                          סגירת תזכורת
                        </button>
                        <button
                          type="button"
                          className="crm-note-action-button"
                          onClick={() => handleClearNoteReminder(note.id)}
                        >
                          איפוס תזכורת
                        </button>
                        <button
                          type="button"
                          className="crm-note-action-button crm-note-action-danger"
                          onClick={() => handleDeleteNote(note.id)}
                        >
                          מחיקת הערה
                        </button>
                      </div>
                    </li>
                  ))}
                  {notes.length === 0 && (
                    <li className="status-text">אין הערות ללקוח</li>
                  )}
                </ul>
              </div>
            </div>
          ) : (
            <div className="status-text">בחר לקוח כדי להציג נתוני מוצרים והערות</div>
          )}
        </section>
        )}
      </div>

      {reminders.length > 0 && (
        <section className="crm-panel crm-reminders-panel">
          <h3 className="panel-subtitle">תזכורות פתוחות</h3>
          <ul className="crm-reminders-list">
            {reminders.map((reminder) => (
              <li key={reminder.id} className="crm-reminder-item">
                <div
                  className="crm-reminder-text"
                  onClick={() => handleReminderGoToClient(reminder)}
                >
                  {reminder.note}
                </div>
                <div className="crm-reminder-meta">
                  <span>{reminder.clientName}</span>
                  {reminder.reminderAt && (
                    <span>עד {reminder.reminderAt}</span>
                  )}
                </div>
                <div className="crm-reminder-actions">
                  <button
                    type="button"
                    className="crm-reminder-action-button"
                    onClick={() => handleReminderGoToClient(reminder)}
                  >
                    מעבר ללקוח
                  </button>
                  <button
                    type="button"
                    className="crm-reminder-action-button"
                    onClick={() => handleDismissReminder(reminder)}
                  >
                    סגירה
                  </button>
                  <button
                    type="button"
                    className="crm-reminder-action-button crm-reminder-action-secondary"
                    onClick={() => handleClearReminderFromGlobal(reminder)}
                  >
                    איפוס
                  </button>
                </div>
              </li>
            ))}
          </ul>
        </section>
      )}
    </div>
  );
}

export default CrmPage;
