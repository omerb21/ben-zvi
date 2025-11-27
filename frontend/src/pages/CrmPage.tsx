import { useEffect, useState, ChangeEvent } from "react";
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
import CrmSummaryPanel from "../components/CrmSummaryPanel";
import CrmClientListPanel from "../components/CrmClientListPanel";
import CrmDashboardPanel from "../components/CrmDashboardPanel";
import CrmRemindersPanel from "../components/CrmRemindersPanel";
import CrmClientDetailPanel from "../components/CrmClientDetailPanel";

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
        <CrmSummaryPanel
          summary={summary}
          effectiveMonth={effectiveMonth}
          viewMode={viewMode}
          totalClients={totalClients}
          totalAssetsValue={totalAssetsValue}
          totalFundsValue={totalFundsValue}
          totalSourcesValue={totalSourcesValue}
          onShiftMonth={handleShiftMonth}
          onMonthChange={handleMonthInputChange}
          onToggleDashboard={() =>
            setViewMode(viewMode === "dashboard" ? "main" : "dashboard")
          }
        />
      )}

      <div className="crm-page">
        {viewMode === "main" && (
          <CrmClientListPanel
            clients={clients}
            selectedClient={selectedClient}
            clientFilter={clientFilter}
            newClientIdNumber={newClientIdNumber}
            newClientFullName={newClientFullName}
            newClientPhone={newClientPhone}
            newClientEmail={newClientEmail}
            newClientBirthDate={newClientBirthDate}
            newClientGender={newClientGender}
            newClientMaritalStatus={newClientMaritalStatus}
            newClientEmployerName={newClientEmployerName}
            newClientEmployerHp={newClientEmployerHp}
            newClientEmployerAddress={newClientEmployerAddress}
            newClientEmployerPhone={newClientEmployerPhone}
            loading={loading}
            error={error}
            onChangeClientFilter={setClientFilter}
            onChangeNewClientIdNumber={setNewClientIdNumber}
            onChangeNewClientFullName={setNewClientFullName}
            onChangeNewClientPhone={setNewClientPhone}
            onChangeNewClientEmail={setNewClientEmail}
            onChangeNewClientBirthDate={setNewClientBirthDate}
            onChangeNewClientGender={setNewClientGender}
            onChangeNewClientMaritalStatus={setNewClientMaritalStatus}
            onChangeNewClientEmployerName={setNewClientEmployerName}
            onChangeNewClientEmployerHp={setNewClientEmployerHp}
            onChangeNewClientEmployerAddress={setNewClientEmployerAddress}
            onChangeNewClientEmployerPhone={setNewClientEmployerPhone}
            onCreateClient={handleCreateClient}
            onSelectClient={loadClientDetails}
          />
        )}

        {viewMode === "dashboard" && summary && (
          <CrmDashboardPanel
            summary={summary}
            crmAdminMessage={crmAdminMessage}
            crmAdminError={crmAdminError}
            crmImportMonth={crmImportMonth}
            crmImportFiles={crmImportFiles}
            isCrmImporting={isCrmImporting}
            isCrmClearing={isCrmClearing}
            monthlyTrendPath={monthlyTrendPath}
            monthlyTrendPoints={monthlyTrendPoints}
            monthlyChange={monthlyChange}
            onCrmMonthChange={setCrmImportMonth}
            onCrmFileChange={handleCrmFileChange}
            onRunCrmImport={handleRunCrmImport}
            onClearCrmDataLocal={handleClearCrmDataLocal}
          />
        )}

        {viewMode === "clientDetail" && (
          <CrmClientDetailPanel
            selectedClient={selectedClient}
            latestSnapshots={latestSnapshots}
            selectedSnapshot={selectedSnapshot}
            clientHistory={clientHistory}
            fundHistory={fundHistory}
            historyChartPath={historyChartPath}
            historyChartPoints={historyChartPoints}
            notes={notes}
            newNoteText={newNoteText}
            newNoteReminder={newNoteReminder}
            newSnapshotFundCode={newSnapshotFundCode}
            newSnapshotFundName={newSnapshotFundName}
            newSnapshotFundType={newSnapshotFundType}
            newSnapshotAmount={newSnapshotAmount}
            newSnapshotDate={newSnapshotDate}
            loading={loading}
            onBackToMain={() => setViewMode("main")}
            onOpenJustification={onOpenJustification}
            onDeleteClient={handleDeleteClient}
            onEditFirstNameChange={setEditFirstName}
            onEditLastNameChange={setEditLastName}
            onEditPhoneChange={setEditPhone}
            onEditEmailChange={setEditEmail}
            onEditBirthDateChange={setEditBirthDate}
            onEditAddressStreetChange={setEditAddressStreet}
            onEditAddressCityChange={setEditAddressCity}
            onEditAddressPostalCodeChange={setEditAddressPostalCode}
            onEditGenderChange={setEditGender}
            onEditMaritalStatusChange={setEditMaritalStatus}
            onEditEmployerNameChange={setEditEmployerName}
            onEditEmployerHpChange={setEditEmployerHp}
            onEditEmployerAddressChange={setEditEmployerAddress}
            onEditEmployerPhoneChange={setEditEmployerPhone}
            editFirstName={editFirstName}
            editLastName={editLastName}
            editPhone={editPhone}
            editEmail={editEmail}
            editBirthDate={editBirthDate}
            editAddressStreet={editAddressStreet}
            editAddressCity={editAddressCity}
            editAddressPostalCode={editAddressPostalCode}
            editGender={editGender}
            editMaritalStatus={editMaritalStatus}
            editEmployerName={editEmployerName}
            editEmployerHp={editEmployerHp}
            editEmployerAddress={editEmployerAddress}
            editEmployerPhone={editEmployerPhone}
            onSaveClientDetails={handleSaveClientDetails}
            onNewSnapshotFundCodeChange={setNewSnapshotFundCode}
            onNewSnapshotFundNameChange={setNewSnapshotFundName}
            onNewSnapshotFundTypeChange={setNewSnapshotFundType}
            onNewSnapshotAmountChange={setNewSnapshotAmount}
            onNewSnapshotDateChange={setNewSnapshotDate}
            onCreateSnapshot={handleCreateSnapshot}
            onSelectSnapshot={handleSelectSnapshot}
            onExportClientReport={handleExportClientReport}
            onExportClientPdf={handleExportClientPdf}
            onSubmitNote={handleSubmitNote}
            onNewNoteTextChange={setNewNoteText}
            onNewNoteReminderChange={setNewNoteReminder}
            onDismissNote={handleDismissNote}
            onClearNoteReminder={handleClearNoteReminder}
            onDeleteNote={handleDeleteNote}
          />
        )}
      </div>

      <CrmRemindersPanel
        reminders={reminders}
        onGoToClient={handleReminderGoToClient}
        onDismissReminder={handleDismissReminder}
        onClearReminder={handleClearReminderFromGlobal}
      />
    </div>
  );
}

export default CrmPage;
