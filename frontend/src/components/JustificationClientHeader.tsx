import type { ChangeEvent } from "react";
import type { Client, ClientSummary } from "../api/crmApi";

type Props = {
  clients: ClientSummary[];
  selectedClientId: number | null;
  clientFilter: string;
  selectedClientDetails: Client | null;
  onClientFilterChange: (value: string) => void;
  onClientChange: (clientId: number | null) => void;
};

function JustificationClientHeader({
  clients,
  selectedClientId,
  clientFilter,
  selectedClientDetails,
  onClientFilterChange,
  onClientChange,
}: Props) {
  const handleFilterChange = (event: ChangeEvent<HTMLInputElement>) => {
    onClientFilterChange(event.target.value);
  };

  const handleClientChange = (event: ChangeEvent<HTMLSelectElement>) => {
    const value = event.target.value;
    if (!value) {
      onClientChange(null);
      return;
    }
    const id = Number(value);
    if (Number.isNaN(id)) {
      onClientChange(null);
      return;
    }
    onClientChange(id);
  };

  const filteredClients = clients.filter((client) => {
    const term = clientFilter.trim();
    if (!term) {
      return true;
    }
    return client.fullName.includes(term) || client.idNumber.includes(term);
  });

  return (
    <>
      <div className="just-client-search">
        <input
          type="text"
          className="just-client-search-input"
          placeholder="חיפוש לקוח לפי שם או תעודת זהות"
          value={clientFilter}
          onChange={handleFilterChange}
        />
      </div>
      <div className="just-client-selector">
        <span className="just-client-label">בחר לקוח:</span>
        <select
          className="just-client-select"
          value={selectedClientId ?? ""}
          onChange={handleClientChange}
        >
          {filteredClients.map((client) => (
            <option key={client.id} value={client.id}>
              {client.fullName} ({client.idNumber})
            </option>
          ))}
          {clients.length === 0 && <option value="">אין לקוחות זמינים</option>}
        </select>
      </div>

      {selectedClientDetails && (
        <div className="just-client-details">
          <div className="just-client-details-row">
            <span className="just-client-details-label">שם מלא:</span>
            <span className="just-client-details-value">
              {selectedClientDetails.fullName}
            </span>
          </div>
          <div className="just-client-details-row">
            <span className="just-client-details-label">ת.ז:</span>
            <span className="just-client-details-value">
              {selectedClientDetails.idNumber}
            </span>
          </div>
          <div className="just-client-details-row">
            <span className="just-client-details-label">תאריך לידה:</span>
            <span className="just-client-details-value">
              {selectedClientDetails.birthDate || "-"}
            </span>
          </div>
          <div className="just-client-details-row">
            <span className="just-client-details-label">מין:</span>
            <span className="just-client-details-value">
              {selectedClientDetails.gender || "-"}
            </span>
          </div>
          <div className="just-client-details-row">
            <span className="just-client-details-label">סטטוס:</span>
            <span className="just-client-details-value">
              {selectedClientDetails.maritalStatus || "-"}
            </span>
          </div>
          <div className="just-client-details-row">
            <span className="just-client-details-label">ארץ לידה:</span>
            <span className="just-client-details-value">
              {selectedClientDetails.birthCountry || "-"}
            </span>
          </div>
          <div className="just-client-details-row">
            <span className="just-client-details-label">טלפון:</span>
            <span className="just-client-details-value">
              {selectedClientDetails.phone || "-"}
            </span>
          </div>
          <div className="just-client-details-row">
            <span className="just-client-details-label">אימייל:</span>
            <span className="just-client-details-value">
              {selectedClientDetails.email || "-"}
            </span>
          </div>
          <div className="just-client-details-row">
            <span className="just-client-details-label">כתובת:</span>
            <span className="just-client-details-value">
              {[
                selectedClientDetails.addressCity,
                [
                  selectedClientDetails.addressStreet,
                  selectedClientDetails.addressHouseNumber,
                ]
                  .filter(Boolean)
                  .join(" "),
                selectedClientDetails.addressApartment
                  ? `דירה ${selectedClientDetails.addressApartment}`
                  : null,
                selectedClientDetails.addressPostalCode,
              ]
                .filter(Boolean)
                .join(", ") || "-"}
            </span>
          </div>
          <div className="just-client-details-row">
            <span className="just-client-details-label">מעסיק:</span>
            <span className="just-client-details-value">
              {selectedClientDetails.employerName || "-"}
            </span>
          </div>
          <div className="just-client-details-row">
            <span className="just-client-details-label">ח"פ מעסיק:</span>
            <span className="just-client-details-value">
              {selectedClientDetails.employerHp || "-"}
            </span>
          </div>
          <div className="just-client-details-row">
            <span className="just-client-details-label">טלפון מעסיק:</span>
            <span className="just-client-details-value">
              {selectedClientDetails.employerPhone || "-"}
            </span>
          </div>
          <div className="just-client-details-row">
            <span className="just-client-details-label">כתובת מעסיק:</span>
            <span className="just-client-details-value">
              {selectedClientDetails.employerAddress || "-"}
            </span>
          </div>
        </div>
      )}
    </>
  );
}

export default JustificationClientHeader;
