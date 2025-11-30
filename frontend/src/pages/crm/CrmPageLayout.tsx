import type { ChangeEvent, FormEvent } from "react";
import type {
  Client,
  ClientSummary,
  Snapshot,
  HistoryPoint,
  FundHistoryPoint,
  ClientNote,
  Reminder,
  SummaryResponse,
  MonthlyChangePoint,
} from "../../api/crmApi";
import CrmSummaryPanel from "../../components/CrmSummaryPanel";
import CrmClientListPanel from "../../components/CrmClientListPanel";
import CrmDashboardPanel from "../../components/CrmDashboardPanel";
import CrmRemindersPanel from "../../components/CrmRemindersPanel";
import CrmClientDetailPanel from "../../components/CrmClientDetailPanel.tsx";
import type { ViewMode } from "./crmClients";
import type { BeneficiaryFormRow } from "./crmBeneficiaries";

type HistoryChartPoint = {
  x: number;
  y: number;
};

type Props = {
  summary: SummaryResponse | null;
  effectiveMonth: string | null;
  viewMode: ViewMode;
  totalClients: number;
  totalAssetsValue: number;
  totalFundsValue: number;
  totalSourcesValue: number;
  clients: ClientSummary[];
  selectedClient: ClientSummary | null;
  clientFilter: string;
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
  loading: boolean;
  error: string | null;
  crmAdminMessage: string | null;
  crmAdminError: string | null;
  crmImportMonth: string;
  crmImportFiles: File[];
  isCrmImporting: boolean;
  isCrmClearing: boolean;
  monthlyTrendPath: string;
  monthlyTrendPoints: { x: number; y: number }[];
  monthlyChange: MonthlyChangePoint[];
  latestSnapshots: Snapshot[];
  selectedSnapshot: Snapshot | null;
  clientHistory: HistoryPoint[];
  fundHistory: FundHistoryPoint[];
  historyChartPath: string;
  historyChartPoints: HistoryChartPoint[];
  notes: ClientNote[];
  newNoteText: string;
  newNoteReminder: string;
  newSnapshotFundCode: string;
  newSnapshotFundName: string;
  newSnapshotFundType: string;
  newSnapshotAmount: string;
  newSnapshotDate: string;
  reminders: Reminder[];
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
  beneficiaries: BeneficiaryFormRow[];
  onShiftMonth: (delta: number) => void;
  onMonthChange: (value: string) => void;
  onToggleDashboard: () => void;
  onChangeClientFilter: (value: string) => void;
  onChangeNewClientIdNumber: (value: string) => void;
  onChangeNewClientFullName: (value: string) => void;
  onChangeNewClientPhone: (value: string) => void;
  onChangeNewClientEmail: (value: string) => void;
  onChangeNewClientBirthDate: (value: string) => void;
  onChangeNewClientGender: (value: string) => void;
  onChangeNewClientMaritalStatus: (value: string) => void;
  onChangeNewClientEmployerName: (value: string) => void;
  onChangeNewClientEmployerHp: (value: string) => void;
  onChangeNewClientEmployerAddress: (value: string) => void;
  onChangeNewClientEmployerPhone: (value: string) => void;
  onCreateClient: () => void;
  onSelectClient: (client: ClientSummary) => void;
  onCrmMonthChange: (value: string) => void;
  onCrmFileChange: (event: ChangeEvent<HTMLInputElement>) => void;
  onRunCrmImport: () => void;
  onClearCrmDataLocal: () => void;
  onBackToMain: () => void;
  onOpenJustification?: (clientId: number) => void;
  onDeleteClient: () => void;
  onEditFirstNameChange: (value: string) => void;
  onEditLastNameChange: (value: string) => void;
  onEditPhoneChange: (value: string) => void;
  onEditEmailChange: (value: string) => void;
  onEditBirthDateChange: (value: string) => void;
  onEditAddressStreetChange: (value: string) => void;
  onEditAddressCityChange: (value: string) => void;
  onEditAddressPostalCodeChange: (value: string) => void;
  onEditGenderChange: (value: string) => void;
  onEditMaritalStatusChange: (value: string) => void;
  onEditEmployerNameChange: (value: string) => void;
  onEditEmployerHpChange: (value: string) => void;
  onEditEmployerAddressChange: (value: string) => void;
  onEditEmployerPhoneChange: (value: string) => void;
  onSaveClientDetails: () => void;
  onBeneficiaryChange: (
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
  ) => void;
  onNewSnapshotFundCodeChange: (value: string) => void;
  onNewSnapshotFundNameChange: (value: string) => void;
  onNewSnapshotFundTypeChange: (value: string) => void;
  onNewSnapshotAmountChange: (value: string) => void;
  onNewSnapshotDateChange: (value: string) => void;
  onCreateSnapshot: () => void;
  onSelectSnapshot: (snapshot: Snapshot) => void;
  onExportClientReport: () => void;
  onExportClientPdf: () => void;
  onSubmitNote: (event: FormEvent) => void;
  onNewNoteTextChange: (value: string) => void;
  onNewNoteReminderChange: (value: string) => void;
  onDismissNote: (noteId: number) => void;
  onClearNoteReminder: (noteId: number) => void;
  onDeleteNote: (noteId: number) => void;
  onGoToClient: (reminder: Reminder) => void;
  onDismissReminder: (reminder: Reminder) => void;
  onClearReminder: (reminder: Reminder) => void;
};

function CrmPageLayout({
  summary,
  effectiveMonth,
  viewMode,
  totalClients,
  totalAssetsValue,
  totalFundsValue,
  totalSourcesValue,
  clients,
  selectedClient,
  clientFilter,
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
  loading,
  error,
  crmAdminMessage,
  crmAdminError,
  crmImportMonth,
  crmImportFiles,
  isCrmImporting,
  isCrmClearing,
  monthlyTrendPath,
  monthlyTrendPoints,
  monthlyChange,
  latestSnapshots,
  selectedSnapshot,
  clientHistory,
  fundHistory,
  historyChartPath,
  historyChartPoints,
  notes,
  newNoteText,
  newNoteReminder,
  newSnapshotFundCode,
  newSnapshotFundName,
  newSnapshotFundType,
  newSnapshotAmount,
  newSnapshotDate,
  reminders,
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
  beneficiaries,
  onShiftMonth,
  onMonthChange,
  onToggleDashboard,
  onChangeClientFilter,
  onChangeNewClientIdNumber,
  onChangeNewClientFullName,
  onChangeNewClientPhone,
  onChangeNewClientEmail,
  onChangeNewClientBirthDate,
  onChangeNewClientGender,
  onChangeNewClientMaritalStatus,
  onChangeNewClientEmployerName,
  onChangeNewClientEmployerHp,
  onChangeNewClientEmployerAddress,
  onChangeNewClientEmployerPhone,
  onCreateClient,
  onSelectClient,
  onCrmMonthChange,
  onCrmFileChange,
  onRunCrmImport,
  onClearCrmDataLocal,
  onBackToMain,
  onOpenJustification,
  onDeleteClient,
  onEditFirstNameChange,
  onEditLastNameChange,
  onEditPhoneChange,
  onEditEmailChange,
  onEditBirthDateChange,
  onEditAddressStreetChange,
  onEditAddressCityChange,
  onEditAddressPostalCodeChange,
  onEditGenderChange,
  onEditMaritalStatusChange,
  onEditEmployerNameChange,
  onEditEmployerHpChange,
  onEditEmployerAddressChange,
  onEditEmployerPhoneChange,
  onSaveClientDetails,
  onBeneficiaryChange,
  onNewSnapshotFundCodeChange,
  onNewSnapshotFundNameChange,
  onNewSnapshotFundTypeChange,
  onNewSnapshotAmountChange,
  onNewSnapshotDateChange,
  onCreateSnapshot,
  onSelectSnapshot,
  onExportClientReport,
  onExportClientPdf,
  onSubmitNote,
  onNewNoteTextChange,
  onNewNoteReminderChange,
  onDismissNote,
  onClearNoteReminder,
  onDeleteNote,
  onGoToClient,
  onDismissReminder,
  onClearReminder,
}: Props) {
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
          onShiftMonth={onShiftMonth}
          onMonthChange={onMonthChange}
          onToggleDashboard={onToggleDashboard}
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
            onChangeClientFilter={onChangeClientFilter}
            onChangeNewClientIdNumber={onChangeNewClientIdNumber}
            onChangeNewClientFullName={onChangeNewClientFullName}
            onChangeNewClientPhone={onChangeNewClientPhone}
            onChangeNewClientEmail={onChangeNewClientEmail}
            onChangeNewClientBirthDate={onChangeNewClientBirthDate}
            onChangeNewClientGender={onChangeNewClientGender}
            onChangeNewClientMaritalStatus={onChangeNewClientMaritalStatus}
            onChangeNewClientEmployerName={onChangeNewClientEmployerName}
            onChangeNewClientEmployerHp={onChangeNewClientEmployerHp}
            onChangeNewClientEmployerAddress={onChangeNewClientEmployerAddress}
            onChangeNewClientEmployerPhone={onChangeNewClientEmployerPhone}
            onCreateClient={onCreateClient}
            onSelectClient={onSelectClient}
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
            onCrmMonthChange={onCrmMonthChange}
            onCrmFileChange={onCrmFileChange}
            onRunCrmImport={onRunCrmImport}
            onClearCrmDataLocal={onClearCrmDataLocal}
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
            onBackToMain={onBackToMain}
            onOpenJustification={onOpenJustification}
            onDeleteClient={onDeleteClient}
            onEditFirstNameChange={onEditFirstNameChange}
            onEditLastNameChange={onEditLastNameChange}
            onEditPhoneChange={onEditPhoneChange}
            onEditEmailChange={onEditEmailChange}
            onEditBirthDateChange={onEditBirthDateChange}
            onEditAddressStreetChange={onEditAddressStreetChange}
            onEditAddressCityChange={onEditAddressCityChange}
            onEditAddressPostalCodeChange={onEditAddressPostalCodeChange}
            onEditGenderChange={onEditGenderChange}
            onEditMaritalStatusChange={onEditMaritalStatusChange}
            onEditEmployerNameChange={onEditEmployerNameChange}
            onEditEmployerHpChange={onEditEmployerHpChange}
            onEditEmployerAddressChange={onEditEmployerAddressChange}
            onEditEmployerPhoneChange={onEditEmployerPhoneChange}
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
            onSaveClientDetails={onSaveClientDetails}
            beneficiaries={beneficiaries}
            onBeneficiaryChange={onBeneficiaryChange}
            onNewSnapshotFundCodeChange={onNewSnapshotFundCodeChange}
            onNewSnapshotFundNameChange={onNewSnapshotFundNameChange}
            onNewSnapshotFundTypeChange={onNewSnapshotFundTypeChange}
            onNewSnapshotAmountChange={onNewSnapshotAmountChange}
            onNewSnapshotDateChange={onNewSnapshotDateChange}
            onCreateSnapshot={onCreateSnapshot}
            onSelectSnapshot={onSelectSnapshot}
            onExportClientReport={onExportClientReport}
            onExportClientPdf={onExportClientPdf}
            onSubmitNote={onSubmitNote}
            onNewNoteTextChange={onNewNoteTextChange}
            onNewNoteReminderChange={onNewNoteReminderChange}
            onDismissNote={onDismissNote}
            onClearNoteReminder={onClearNoteReminder}
            onDeleteNote={onDeleteNote}
          />
        )}
      </div>

      <CrmRemindersPanel
        reminders={reminders}
        onGoToClient={onGoToClient}
        onDismissReminder={onDismissReminder}
        onClearReminder={onClearReminder}
      />
    </div>
  );
}

export default CrmPageLayout;
