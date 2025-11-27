import type { ClientSummary } from "../api/crmApi";

type Props = {
  clients: ClientSummary[];
  selectedClient: ClientSummary | null;
  clientFilter: string;
  newClientIdNumber: string;
  newClientFullName: string;
  newClientPhone: string;
  newClientEmail: string;
  newClientBirthDate: string;
  newClientGender: string;
  newClientMaritalStatus: string;
  newClientEmployerName: string;
  newClientEmployerHp: string;
  newClientEmployerAddress: string;
  newClientEmployerPhone: string;
  loading: boolean;
  error: string | null;
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
};

function CrmClientListPanel({
  clients,
  selectedClient,
  clientFilter,
  newClientIdNumber,
  newClientFullName,
  newClientPhone,
  newClientEmail,
  newClientBirthDate,
  newClientGender,
  newClientMaritalStatus,
  newClientEmployerName,
  newClientEmployerHp,
  newClientEmployerAddress,
  newClientEmployerPhone,
  loading,
  error,
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
}: Props) {
  return (
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
            onChange={(e) => onChangeNewClientIdNumber(e.target.value)}
          />
          <input
            type="text"
            className="crm-new-client-input"
            placeholder="שם מלא"
            value={newClientFullName}
            onChange={(e) => onChangeNewClientFullName(e.target.value)}
          />
          <input
            type="text"
            className="crm-new-client-input"
            placeholder="טלפון"
            value={newClientPhone}
            onChange={(e) => onChangeNewClientPhone(e.target.value)}
          />
          <input
            type="email"
            className="crm-new-client-input"
            placeholder="אימייל"
            value={newClientEmail}
            onChange={(e) => onChangeNewClientEmail(e.target.value)}
          />
          <input
            type="date"
            className="crm-new-client-input"
            placeholder="תאריך לידה"
            value={newClientBirthDate}
            onChange={(e) => onChangeNewClientBirthDate(e.target.value)}
          />
          <select
            className="crm-new-client-input"
            value={newClientGender}
            onChange={(e) => onChangeNewClientGender(e.target.value)}
          >
            <option value="">מין</option>
            <option value="male">זכר</option>
            <option value="female">נקבה</option>
          </select>
          <select
            className="crm-new-client-input"
            value={newClientMaritalStatus}
            onChange={(e) => onChangeNewClientMaritalStatus(e.target.value)}
          >
            <option value="">סטטוס משפחתי</option>
            <option value="single">רווק/ה</option>
            <option value="married">נשוי/אה</option>
            <option value="divorced">גרוש/ה</option>
            <option value="widowed">אלמן/ה</option>
          </select>
          <input
            type="text"
            className="crm-new-client-input"
            placeholder="שם מעסיק"
            value={newClientEmployerName}
            onChange={(e) => onChangeNewClientEmployerName(e.target.value)}
          />
          <input
            type="text"
            className="crm-new-client-input"
            placeholder="ח.פ מעסיק"
            value={newClientEmployerHp}
            onChange={(e) => onChangeNewClientEmployerHp(e.target.value)}
          />
          <input
            type="text"
            className="crm-new-client-input"
            placeholder="כתובת מעסיק"
            value={newClientEmployerAddress}
            onChange={(e) => onChangeNewClientEmployerAddress(e.target.value)}
          />
          <input
            type="tel"
            className="crm-new-client-input"
            placeholder="טלפון מעסיק"
            value={newClientEmployerPhone}
            onChange={(e) => onChangeNewClientEmployerPhone(e.target.value)}
          />
        </div>
        <button
          type="button"
          className="crm-new-client-button"
          onClick={onCreateClient}
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
          onChange={(e) => onChangeClientFilter(e.target.value)}
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
              client.fullName.includes(term) || client.idNumber.includes(term)
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
              onClick={() => onSelectClient(client)}
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
  );
}

export default CrmClientListPanel;
