import type { FormEvent } from "react";
import type {
  ClientSummary,
  Snapshot,
  HistoryPoint,
  FundHistoryPoint,
  ClientNote,
} from "../api/crmApi";

type HistoryChartPoint = {
  x: number;
  y: number;
};

type Props = {
  selectedClient: ClientSummary | null;
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
  loading: boolean;
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
  editFirstName: string;
  editLastName: string;
  editPhone: string;
  editEmail: string;
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
  onSaveClientDetails: () => void;
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
};

function CrmClientDetailPanel({
  selectedClient,
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
  loading,
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
  editFirstName,
  editLastName,
  editPhone,
  editEmail,
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
  onSaveClientDetails,
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
}: Props) {
  return (
    <section className="crm-panel crm-panel-right">
      <div className="crm-client-detail-header">
        <button
          type="button"
          className="crm-client-detail-back"
          onClick={onBackToMain}
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
              onClick={onDeleteClient}
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
                  onChange={(event) => onEditFirstNameChange(event.target.value)}
                />
              </div>
              <div className="crm-client-edit-field">
                <label className="crm-client-edit-label">שם משפחה</label>
                <input
                  type="text"
                  className="crm-client-edit-input"
                  value={editLastName}
                  onChange={(event) => onEditLastNameChange(event.target.value)}
                />
              </div>
              <div className="crm-client-edit-field">
                <label className="crm-client-edit-label">טלפון</label>
                <input
                  type="tel"
                  className="crm-client-edit-input"
                  value={editPhone}
                  onChange={(event) => onEditPhoneChange(event.target.value)}
                />
              </div>
              <div className="crm-client-edit-field">
                <label className="crm-client-edit-label">אימייל</label>
                <input
                  type="email"
                  className="crm-client-edit-input"
                  value={editEmail}
                  onChange={(event) => onEditEmailChange(event.target.value)}
                />
              </div>
              <div className="crm-client-edit-field">
                <label className="crm-client-edit-label">תאריך לידה</label>
                <input
                  type="date"
                  className="crm-client-edit-input"
                  value={editBirthDate}
                  onChange={(event) => onEditBirthDateChange(event.target.value)}
                />
              </div>
              <div className="crm-client-edit-field">
                <label className="crm-client-edit-label">רחוב</label>
                <input
                  type="text"
                  className="crm-client-edit-input"
                  value={editAddressStreet}
                  onChange={(event) =>
                    onEditAddressStreetChange(event.target.value)
                  }
                />
              </div>
              <div className="crm-client-edit-field">
                <label className="crm-client-edit-label">עיר</label>
                <input
                  type="text"
                  className="crm-client-edit-input"
                  value={editAddressCity}
                  onChange={(event) => onEditAddressCityChange(event.target.value)}
                />
              </div>
              <div className="crm-client-edit-field">
                <label className="crm-client-edit-label">מיקוד</label>
                <input
                  type="text"
                  className="crm-client-edit-input"
                  value={editAddressPostalCode}
                  onChange={(event) =>
                    onEditAddressPostalCodeChange(event.target.value)
                  }
                />
              </div>
              <div className="crm-client-edit-field">
                <label className="crm-client-edit-label">מין</label>
                <select
                  className="crm-client-edit-input"
                  value={editGender}
                  onChange={(event) => onEditGenderChange(event.target.value)}
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
                  onChange={(event) =>
                    onEditMaritalStatusChange(event.target.value)
                  }
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
                  onChange={(event) =>
                    onEditEmployerNameChange(event.target.value)
                  }
                />
              </div>
              <div className="crm-client-edit-field">
                <label className="crm-client-edit-label">ח.פ מעסיק</label>
                <input
                  type="text"
                  className="crm-client-edit-input"
                  value={editEmployerHp}
                  onChange={(event) => onEditEmployerHpChange(event.target.value)}
                />
              </div>
              <div className="crm-client-edit-field">
                <label className="crm-client-edit-label">כתובת מעסיק</label>
                <input
                  type="text"
                  className="crm-client-edit-input"
                  value={editEmployerAddress}
                  onChange={(event) =>
                    onEditEmployerAddressChange(event.target.value)
                  }
                />
              </div>
              <div className="crm-client-edit-field">
                <label className="crm-client-edit-label">טלפון מעסיק</label>
                <input
                  type="tel"
                  className="crm-client-edit-input"
                  value={editEmployerPhone}
                  onChange={(event) =>
                    onEditEmployerPhoneChange(event.target.value)
                  }
                />
              </div>
            </div>
            <button
              type="button"
              className="crm-client-edit-button"
              onClick={onSaveClientDetails}
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
                onChange={(event) =>
                  onNewSnapshotFundCodeChange(event.target.value)
                }
              />
              <input
                type="text"
                className="crm-snapshot-input"
                placeholder="שם קופה"
                value={newSnapshotFundName}
                onChange={(event) =>
                  onNewSnapshotFundNameChange(event.target.value)
                }
              />
              <input
                type="text"
                className="crm-snapshot-input"
                placeholder="סוג קופה"
                value={newSnapshotFundType}
                onChange={(event) =>
                  onNewSnapshotFundTypeChange(event.target.value)
                }
              />
              <input
                type="text"
                className="crm-snapshot-input"
                placeholder="סכום"
                value={newSnapshotAmount}
                onChange={(event) =>
                  onNewSnapshotAmountChange(event.target.value)
                }
              />
              <input
                type="date"
                className="crm-snapshot-input"
                value={newSnapshotDate}
                onChange={(event) =>
                  onNewSnapshotDateChange(event.target.value)
                }
              />
              <button
                type="button"
                className="crm-snapshot-button"
                onClick={onCreateSnapshot}
              >
                יצירת צילום
              </button>
            </div>
            {latestSnapshots.length > 0 && (
              <div className="crm-snapshot-actions">
                <button
                  type="button"
                  className="crm-snapshot-export-button"
                  onClick={onExportClientReport}
                >
                  הורדת דוח לקוח (CSV)
                </button>
                <button
                  type="button"
                  className="crm-snapshot-export-button crm-snapshot-export-button-secondary"
                  onClick={onExportClientPdf}
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
                  onClick={() => onSelectSnapshot(snapshot)}
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
            <form className="crm-note-form" onSubmit={onSubmitNote}>
              <textarea
                className="crm-note-input"
                value={newNoteText}
                onChange={(event) =>
                  onNewNoteTextChange(event.target.value)
                }
                placeholder="הוסף הערה ללקוח..."
              />
              <div className="crm-note-form-row">
                <input
                  type="date"
                  className="crm-note-date"
                  value={newNoteReminder}
                  onChange={(event) =>
                    onNewNoteReminderChange(event.target.value)
                  }
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
                      onClick={() => onDismissNote(note.id)}
                    >
                      סגירת תזכורת
                    </button>
                    <button
                      type="button"
                      className="crm-note-action-button"
                      onClick={() => onClearNoteReminder(note.id)}
                    >
                      איפוס תזכורת
                    </button>
                    <button
                      type="button"
                      className="crm-note-action-button crm-note-action-danger"
                      onClick={() => onDeleteNote(note.id)}
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
  );
}

export default CrmClientDetailPanel;
