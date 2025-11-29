import { useEffect, useState, ChangeEvent, FormEvent } from "react";
import type {
  Client,
  ClientSummary,
  Snapshot,
  ClientNote,
  Reminder,
  SummaryResponse,
  MonthlyChangePoint,
  HistoryPoint,
  FundHistoryPoint,
} from "../../api/crmApi";
import {
  fetchClientSummaries,
  fetchSummary,
  fetchReminders,
  fetchClients,
  fetchMonthlyChange,
} from "../../api/crmApi";
import "../../styles/crm.css";
import CrmPageLayout from "./CrmPageLayout";
import { buildHistoryChartData, buildMonthlyChangeChartData } from "./crmCharts";
import {
  loadClientDetailsAction,
  createClientAction,
  saveClientDetailsAction,
  deleteClientAction,
  type ViewMode,
} from "./crmClients";
import {
  selectSnapshotAction,
  createSnapshotAction,
  exportClientReportAction,
  exportClientPdfAction,
} from "./crmSnapshotsAndExport";
import {
  dismissNoteAction,
  clearNoteReminderAction,
  deleteNoteAction,
  submitNoteAction,
  dismissReminderAction,
  clearReminderGlobalAction,
} from "./crmNotesAndReminders";
import {
  crmFileChangeHandler,
  runCrmImportAction,
  clearCrmDataLocalAction,
} from "./crmAdminActions";

export type Props = {
  onOpenJustification?: (clientId: number) => void;
};

function CrmPageRoot({ onOpenJustification }: Props) {
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
  const [viewMode, setViewMode] = useState<ViewMode>("main");
  const [selectedMonth, setSelectedMonth] = useState<string | null>(null);

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

  const handleLoadClientDetails = (client: ClientSummary) => {
    loadClientDetailsAction({
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
    });
  };

  const handleCreateClient = () => {
    createClientAction({
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
    });
  };

  const handleSaveClientDetails = () => {
    saveClientDetailsAction({
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
    });
  };

  const handleDeleteClient = () => {
    deleteClientAction({
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
    });
  };

  const handleSelectSnapshot = (snapshot: Snapshot) => {
    selectSnapshotAction({
      snapshot,
      selectedClient,
      setSelectedSnapshot,
      setFundHistory,
      setLoading,
      setError,
    });
  };

  const handleCreateSnapshot = () => {
    createSnapshotAction({
      selectedClient,
      newSnapshotFundCode,
      newSnapshotAmount,
      newSnapshotDate,
      newSnapshotFundType,
      newSnapshotFundName,
      setLoading,
      setSnapshots,
      setNewSnapshotFundCode,
      setNewSnapshotFundName,
      setNewSnapshotFundType,
      setNewSnapshotAmount,
      setNewSnapshotDate,
      setError,
    });
  };

  const handleExportClientReport = () => {
    exportClientReportAction({
      selectedClient,
      latestSnapshots,
    });
  };

  const handleExportClientPdf = () => {
    exportClientPdfAction({
      selectedClient,
      latestSnapshots,
    });
  };

  const handleDismissNote = (noteId: number) => {
    dismissNoteAction({
      selectedClient,
      noteId,
      setNotes,
      setError,
    });
  };

  const handleClearNoteReminder = (noteId: number) => {
    clearNoteReminderAction({
      selectedClient,
      noteId,
      setNotes,
      setError,
    });
  };

  const handleDeleteNote = (noteId: number) => {
    deleteNoteAction({
      selectedClient,
      noteId,
      setNotes,
      setError,
    });
  };

  const handleSubmitNote = (event: FormEvent) => {
    event.preventDefault();
    submitNoteAction({
      selectedClient,
      newNoteText,
      newNoteReminder,
      setNotes,
      setNewNoteText,
      setNewNoteReminder,
      setError,
    });
  };

  const handleReminderGoToClient = (reminder: Reminder) => {
    const client = clients.find((c) => c.id === reminder.clientId) || null;
    if (!client) {
      return;
    }
    handleLoadClientDetails(client);
  };

  const handleDismissReminder = (reminder: Reminder) => {
    dismissReminderAction({
      reminder,
      setReminders,
      setError,
    });
  };

  const handleClearReminderFromGlobal = (reminder: Reminder) => {
    clearReminderGlobalAction({
      reminder,
      setReminders,
      setError,
    });
  };

  const handleCrmFileChange = (event: ChangeEvent<HTMLInputElement>) => {
    crmFileChangeHandler({
      event,
      setCrmImportFiles,
    });
  };

  const handleRunCrmImport = () => {
    runCrmImportAction({
      crmImportFiles,
      crmImportMonth,
      isCrmImporting,
      isCrmClearing,
      setIsCrmImporting,
      setCrmAdminMessage,
      setCrmAdminError,
    });
  };

  const handleClearCrmDataLocal = () => {
    clearCrmDataLocalAction({
      isCrmImporting,
      isCrmClearing,
      setIsCrmClearing,
      setCrmAdminMessage,
      setCrmAdminError,
    });
  };

  const handleBackToMain = () => {
    setViewMode("main");
  };

  const handleToggleDashboard = () => {
    setViewMode(viewMode === "dashboard" ? "main" : "dashboard");
  };

  return (
    <CrmPageLayout
      summary={summary}
      effectiveMonth={effectiveMonth}
      viewMode={viewMode}
      totalClients={totalClients}
      totalAssetsValue={totalAssetsValue}
      totalFundsValue={totalFundsValue}
      totalSourcesValue={totalSourcesValue}
      clients={clients}
      selectedClient={selectedClient}
      clientFilter={clientFilter}
      newClientIdNumber={newClientIdNumber}
      newClientFullName={newClientFullName}
      newClientEmail={newClientEmail}
      newClientPhone={newClientPhone}
      newClientBirthDate={newClientBirthDate}
      newClientGender={newClientGender}
      newClientMaritalStatus={newClientMaritalStatus}
      newClientEmployerName={newClientEmployerName}
      newClientEmployerHp={newClientEmployerHp}
      newClientEmployerAddress={newClientEmployerAddress}
      newClientEmployerPhone={newClientEmployerPhone}
      loading={loading}
      error={error}
      crmAdminMessage={crmAdminMessage}
      crmAdminError={crmAdminError}
      crmImportMonth={crmImportMonth}
      crmImportFiles={crmImportFiles}
      isCrmImporting={isCrmImporting}
      isCrmClearing={isCrmClearing}
      monthlyTrendPath={monthlyTrendPath}
      monthlyTrendPoints={monthlyTrendPoints}
      monthlyChange={monthlyChange}
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
      reminders={reminders}
      editFirstName={editFirstName}
      editLastName={editLastName}
      editEmail={editEmail}
      editPhone={editPhone}
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
      onShiftMonth={handleShiftMonth}
      onMonthChange={handleMonthInputChange}
      onToggleDashboard={handleToggleDashboard}
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
      onSelectClient={handleLoadClientDetails}
      onCrmMonthChange={setCrmImportMonth}
      onCrmFileChange={handleCrmFileChange}
      onRunCrmImport={handleRunCrmImport}
      onClearCrmDataLocal={handleClearCrmDataLocal}
      onBackToMain={handleBackToMain}
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
      onGoToClient={handleReminderGoToClient}
      onDismissReminder={handleDismissReminder}
      onClearReminder={handleClearReminderFromGlobal}
    />
  );
}

export default CrmPageRoot;
