import { useEffect, useState } from "react";
import type {
  Client,
  ClientSummary,
  ClientNote,
  Reminder,
  SummaryResponse,
  MonthlyChangePoint,
} from "../../api/crmApi";
import {
  fetchClientSummaries,
  fetchSummary,
  fetchReminders,
  fetchClients,
  fetchMonthlyChange,
} from "../../api/crmApi";
import "../../styles/crm.css";
import CrmPageLayout from "./CrmPageLayout.tsx";
import { buildHistoryChartData, buildMonthlyChangeChartData } from "./crmCharts";
import {
  loadClientDetailsAction,
  createClientAction,
  saveClientDetailsAction,
  deleteClientAction,
  type ViewMode,
} from "./crmClients";
import type { BeneficiaryFormRow } from "./crmBeneficiaries";
import { useCrmAdmin } from "./useCrmAdmin";
import { useCrmSnapshots } from "./useCrmSnapshots";
import { useCrmNotesAndReminders } from "./useCrmNotesAndReminders";

export type Props = {
  onOpenJustification?: (clientId: number) => void;
};

function CrmPageRoot({ onOpenJustification }: Props) {
  const [clients, setClients] = useState<ClientSummary[]>([]);
  const [selectedClient, setSelectedClient] = useState<ClientSummary | null>(null);
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
  const [editAddressHouseNumber, setEditAddressHouseNumber] = useState("");
  const [editAddressApartment, setEditAddressApartment] = useState("");
  const [editAddressCity, setEditAddressCity] = useState("");
  const [editAddressPostalCode, setEditAddressPostalCode] = useState("");
  const [editGender, setEditGender] = useState("");
  const [editMaritalStatus, setEditMaritalStatus] = useState("");
  const [editEmployerName, setEditEmployerName] = useState("");
  const [editEmployerHp, setEditEmployerHp] = useState("");
  const [editEmployerAddress, setEditEmployerAddress] = useState("");
  const [editEmployerPhone, setEditEmployerPhone] = useState("");
  const [beneficiaries, setBeneficiaries] = useState<BeneficiaryFormRow[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [viewMode, setViewMode] = useState<ViewMode>("main");
  const [selectedMonth, setSelectedMonth] = useState<string | null>(null);

  const {
    crmImportFiles,
    crmImportMonth,
    isCrmImporting,
    isCrmClearing,
    crmAdminMessage,
    crmAdminError,
    setCrmImportMonth,
    handleCrmFileChange,
    handleRunCrmImport,
    handleClearCrmDataLocal,
  } = useCrmAdmin();

  const {
    snapshots,
    selectedSnapshot,
    clientHistory,
    fundHistory,
    newSnapshotFundCode,
    newSnapshotFundName,
    newSnapshotFundType,
    newSnapshotAmount,
    newSnapshotDate,
    latestSnapshots,
    setSnapshots,
    setSelectedSnapshot,
    setClientHistory,
    setFundHistory,
    setNewSnapshotFundCode,
    setNewSnapshotFundName,
    setNewSnapshotFundType,
    setNewSnapshotAmount,
    setNewSnapshotDate,
    handleSelectSnapshot,
    handleCreateSnapshot,
    handleExportClientReport,
    handleExportClientPdf,
  } = useCrmSnapshots({
    selectedClient,
    setLoading,
    setError,
  });

  const {
    notes,
    reminders,
    newNoteText,
    newNoteReminder,
    setNotes,
    setReminders,
    setNewNoteText,
    setNewNoteReminder,
    handleDismissNote,
    handleClearNoteReminder,
    handleDeleteNote,
    handleSubmitNote,
    handleDismissReminder,
    handleClearReminderFromGlobal,
  } = useCrmNotesAndReminders({
    selectedClient,
    setError,
  });

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
      setEditAddressHouseNumber,
      setEditAddressApartment,
      setEditAddressCity,
      setEditAddressPostalCode,
      setEditGender,
      setEditMaritalStatus,
      setEditEmployerName,
      setEditEmployerHp,
      setEditEmployerAddress,
      setEditEmployerPhone,
      setError,
      setBeneficiaries,
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
      editAddressHouseNumber,
      editAddressApartment,
      editAddressCity,
      editAddressPostalCode,
      editGender,
      editMaritalStatus,
      editEmployerName,
      editEmployerHp,
      editEmployerAddress,
      editEmployerPhone,
      beneficiaries,
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

  const handleReminderGoToClient = (reminder: Reminder) => {
    const client = clients.find((c) => c.id === reminder.clientId) || null;
    if (!client) {
      return;
    }
    handleLoadClientDetails(client);
  };

  const handleBackToMain = () => {
    setViewMode("main");
  };

  const handleToggleDashboard = () => {
    setViewMode(viewMode === "dashboard" ? "main" : "dashboard");
  };

  const handleBeneficiaryChange = (
    index: number,
    field:
      | "firstName"
      | "lastName"
      | "idNumber"
      | "birthDate"
      | "address"
      | "relation"
      | "percentage",
    value: string
  ) => {
    setBeneficiaries((prev) =>
      prev.map((row) =>
        row.index === index
          ? {
              ...row,
              [field]: value,
            }
          : row
      )
    );
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
      editAddressHouseNumber={editAddressHouseNumber}
      editAddressApartment={editAddressApartment}
      editAddressCity={editAddressCity}
      editAddressPostalCode={editAddressPostalCode}
      editGender={editGender}
      editMaritalStatus={editMaritalStatus}
      editEmployerName={editEmployerName}
      editEmployerHp={editEmployerHp}
      editEmployerAddress={editEmployerAddress}
      editEmployerPhone={editEmployerPhone}
      beneficiaries={beneficiaries}
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
      onEditAddressHouseNumberChange={setEditAddressHouseNumber}
      onEditAddressApartmentChange={setEditAddressApartment}
      onEditAddressCityChange={setEditAddressCity}
      onEditAddressPostalCodeChange={setEditAddressPostalCode}
      onEditGenderChange={setEditGender}
      onEditMaritalStatusChange={setEditMaritalStatus}
      onEditEmployerNameChange={setEditEmployerName}
      onEditEmployerHpChange={setEditEmployerHp}
      onEditEmployerAddressChange={setEditEmployerAddress}
      onEditEmployerPhoneChange={setEditEmployerPhone}
      onSaveClientDetails={handleSaveClientDetails}
      onBeneficiaryChange={handleBeneficiaryChange}
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
