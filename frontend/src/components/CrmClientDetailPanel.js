"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
function CrmClientDetailPanel(_a) {
    var selectedClient = _a.selectedClient, latestSnapshots = _a.latestSnapshots, selectedSnapshot = _a.selectedSnapshot, clientHistory = _a.clientHistory, fundHistory = _a.fundHistory, historyChartPath = _a.historyChartPath, historyChartPoints = _a.historyChartPoints, notes = _a.notes, newNoteText = _a.newNoteText, newNoteReminder = _a.newNoteReminder, newSnapshotFundCode = _a.newSnapshotFundCode, newSnapshotFundName = _a.newSnapshotFundName, newSnapshotFundType = _a.newSnapshotFundType, newSnapshotAmount = _a.newSnapshotAmount, newSnapshotDate = _a.newSnapshotDate, loading = _a.loading, onBackToMain = _a.onBackToMain, onOpenJustification = _a.onOpenJustification, onDeleteClient = _a.onDeleteClient, onEditFirstNameChange = _a.onEditFirstNameChange, onEditLastNameChange = _a.onEditLastNameChange, onEditPhoneChange = _a.onEditPhoneChange, onEditEmailChange = _a.onEditEmailChange, onEditBirthDateChange = _a.onEditBirthDateChange, onEditAddressStreetChange = _a.onEditAddressStreetChange, onEditAddressCityChange = _a.onEditAddressCityChange, onEditAddressPostalCodeChange = _a.onEditAddressPostalCodeChange, onEditGenderChange = _a.onEditGenderChange, onEditMaritalStatusChange = _a.onEditMaritalStatusChange, onEditEmployerNameChange = _a.onEditEmployerNameChange, onEditEmployerHpChange = _a.onEditEmployerHpChange, onEditEmployerAddressChange = _a.onEditEmployerAddressChange, onEditEmployerPhoneChange = _a.onEditEmployerPhoneChange, onBeneficiaryChange = _a.onBeneficiaryChange, editFirstName = _a.editFirstName, editLastName = _a.editLastName, editPhone = _a.editPhone, editEmail = _a.editEmail, editBirthDate = _a.editBirthDate, editAddressStreet = _a.editAddressStreet, editAddressCity = _a.editAddressCity, editAddressPostalCode = _a.editAddressPostalCode, editGender = _a.editGender, editMaritalStatus = _a.editMaritalStatus, editEmployerName = _a.editEmployerName, editEmployerHp = _a.editEmployerHp, editEmployerAddress = _a.editEmployerAddress, editEmployerPhone = _a.editEmployerPhone, beneficiaries = _a.beneficiaries, onSaveClientDetails = _a.onSaveClientDetails, onNewSnapshotFundCodeChange = _a.onNewSnapshotFundCodeChange, onNewSnapshotFundNameChange = _a.onNewSnapshotFundNameChange, onNewSnapshotFundTypeChange = _a.onNewSnapshotFundTypeChange, onNewSnapshotAmountChange = _a.onNewSnapshotAmountChange, onNewSnapshotDateChange = _a.onNewSnapshotDateChange, onCreateSnapshot = _a.onCreateSnapshot, onSelectSnapshot = _a.onSelectSnapshot, onExportClientReport = _a.onExportClientReport, onExportClientPdf = _a.onExportClientPdf, onSubmitNote = _a.onSubmitNote, onNewNoteTextChange = _a.onNewNoteTextChange, onNewNoteReminderChange = _a.onNewNoteReminderChange, onDismissNote = _a.onDismissNote, onClearNoteReminder = _a.onClearNoteReminder, onDeleteNote = _a.onDeleteNote;
    return (<section className="crm-panel crm-panel-right">
      <div className="crm-client-detail-header">
        <button type="button" className="crm-client-detail-back" onClick={onBackToMain}>
          חזרה לרשימת לקוחות
        </button>
        {selectedClient && (<>
            {onOpenJustification && (<button type="button" className="crm-client-justify-button" onClick={function () { return onOpenJustification(selectedClient.id); }}>
                מעבר למסך ההנמקה
              </button>)}
            <button type="button" className="crm-client-delete-button" onClick={onDeleteClient}>
              מחיקת לקוח
            </button>
          </>)}
      </div>
      <h2 className="panel-title">מוצרים והערות ללקוח</h2>
      {selectedClient ? (<div className="snapshots-wrapper">
          <div className="snapshots-header">
            <div className="snapshots-client-name">{selectedClient.fullName}</div>
            <div className="snapshots-client-id">{selectedClient.idNumber}</div>
          </div>
          <div className="crm-client-edit">
            <h3 className="panel-subtitle">פרטי לקוח</h3>
            <div className="crm-client-edit-grid">
              <div className="crm-client-edit-field">
                <label className="crm-client-edit-label">שם פרטי</label>
                <input type="text" className="crm-client-edit-input" value={editFirstName} onChange={function (event) { return onEditFirstNameChange(event.target.value); }}/>
              </div>
              <div className="crm-client-edit-field">
                <label className="crm-client-edit-label">שם משפחה</label>
                <input type="text" className="crm-client-edit-input" value={editLastName} onChange={function (event) { return onEditLastNameChange(event.target.value); }}/>
              </div>
              <div className="crm-client-edit-field">
                <label className="crm-client-edit-label">טלפון</label>
                <input type="tel" className="crm-client-edit-input" value={editPhone} onChange={function (event) { return onEditPhoneChange(event.target.value); }}/>
              </div>
              <div className="crm-client-edit-field">
                <label className="crm-client-edit-label">אימייל</label>
                <input type="email" className="crm-client-edit-input" value={editEmail} onChange={function (event) { return onEditEmailChange(event.target.value); }}/>
              </div>
              <div className="crm-client-edit-field">
                <label className="crm-client-edit-label">תאריך לידה</label>
                <input type="date" className="crm-client-edit-input" value={editBirthDate} onChange={function (event) { return onEditBirthDateChange(event.target.value); }}/>
              </div>
              <div className="crm-client-edit-field">
                <label className="crm-client-edit-label">רחוב</label>
                <input type="text" className="crm-client-edit-input" value={editAddressStreet} onChange={function (event) {
                return onEditAddressStreetChange(event.target.value);
            }}/>
              </div>
              <div className="crm-client-edit-field">
                <label className="crm-client-edit-label">עיר</label>
                <input type="text" className="crm-client-edit-input" value={editAddressCity} onChange={function (event) { return onEditAddressCityChange(event.target.value); }}/>
              </div>
              <div className="crm-client-edit-field">
                <label className="crm-client-edit-label">מיקוד</label>
                <input type="text" className="crm-client-edit-input" value={editAddressPostalCode} onChange={function (event) {
                return onEditAddressPostalCodeChange(event.target.value);
            }}/>
              </div>
              <div className="crm-client-edit-field">
                <label className="crm-client-edit-label">מין</label>
                <select className="crm-client-edit-input" value={editGender} onChange={function (event) { return onEditGenderChange(event.target.value); }}>
                  <option value="">לא מוגדר</option>
                  <option value="male">זכר</option>
                  <option value="female">נקבה</option>
                </select>
              </div>
              <div className="crm-client-edit-field">
                <label className="crm-client-edit-label">סטטוס משפחתי</label>
                <select className="crm-client-edit-input" value={editMaritalStatus} onChange={function (event) {
                return onEditMaritalStatusChange(event.target.value);
            }}>
                  <option value="">לא מוגדר</option>
                  <option value="single">רווק/ה</option>
                  <option value="married">נשוי/אה</option>
                  <option value="divorced">גרוש/ה</option>
                  <option value="widowed">אלמן/ה</option>
                </select>
              </div>
              <div className="crm-client-edit-field">
                <label className="crm-client-edit-label">שם מעסיק</label>
                <input type="text" className="crm-client-edit-input" value={editEmployerName} onChange={function (event) {
                return onEditEmployerNameChange(event.target.value);
            }}/>
              </div>
              <div className="crm-client-edit-field">
                <label className="crm-client-edit-label">ח.פ מעסיק</label>
                <input type="text" className="crm-client-edit-input" value={editEmployerHp} onChange={function (event) { return onEditEmployerHpChange(event.target.value); }}/>
              </div>
              <div className="crm-client-edit-field">
                <label className="crm-client-edit-label">כתובת מעסיק</label>
                <input type="text" className="crm-client-edit-input" value={editEmployerAddress} onChange={function (event) {
                return onEditEmployerAddressChange(event.target.value);
            }}/>
              </div>
              <div className="crm-client-edit-field">
                <label className="crm-client-edit-label">טלפון מעסיק</label>
                <input type="tel" className="crm-client-edit-input" value={editEmployerPhone} onChange={function (event) {
                return onEditEmployerPhoneChange(event.target.value);
            }}/>
              </div>
            </div>
            <button type="button" className="crm-client-edit-button" onClick={onSaveClientDetails}>
              שמירת פרטי לקוח
            </button>
          </div>

          <div className="crm-beneficiaries">
            <h3 className="panel-subtitle">מוטבים</h3>
            <table className="crm-beneficiaries-table">
              <thead>
                <tr>
                  <th>שם פרטי *</th>
                  <th>שם משפחה *</th>
                  <th>תאריך לידה *</th>
                  <th>מס׳ תעודת זהות/דרכון *</th>
                  <th>כתובת *</th>
                  <th>קרבת משפחה *</th>
                  <th>חלק ב-% *</th>
                </tr>
              </thead>
              <tbody>
                {beneficiaries.map(function (row) { return (<tr key={row.index}>
                    <td>
                      <input type="text" className="crm-beneficiaries-input" value={row.firstName} onChange={function (event) {
                    return onBeneficiaryChange(row.index, "firstName", event.target.value);
                }}/>
                    </td>
                    <td>
                      <input type="text" className="crm-beneficiaries-input" value={row.lastName} onChange={function (event) {
                    return onBeneficiaryChange(row.index, "lastName", event.target.value);
                }}/>
                    </td>
                    <td>
                      <input type="date" className="crm-beneficiaries-input" value={row.birthDate} onChange={function (event) {
                    return onBeneficiaryChange(row.index, "birthDate", event.target.value);
                }}/>
                    </td>
                    <td>
                      <input type="text" className="crm-beneficiaries-input" value={row.idNumber} onChange={function (event) {
                    return onBeneficiaryChange(row.index, "idNumber", event.target.value);
                }}/>
                    </td>
                    <td>
                      <input type="text" className="crm-beneficiaries-input" value={row.address} onChange={function (event) {
                    return onBeneficiaryChange(row.index, "address", event.target.value);
                }}/>
                    </td>
                    <td>
                      <input type="text" className="crm-beneficiaries-input" value={row.relation} onChange={function (event) {
                    return onBeneficiaryChange(row.index, "relation", event.target.value);
                }}/>
                    </td>
                    <td>
                      <input type="text" className="crm-beneficiaries-input" value={row.percentage} onChange={function (event) {
                    return onBeneficiaryChange(row.index, "percentage", event.target.value);
                }}/>
                    </td>
                  </tr>); })}
              </tbody>
            </table>
          </div>

          <div className="crm-snapshot-create">
            <div className="crm-snapshot-create-grid">
              <input type="text" className="crm-snapshot-input" placeholder="קוד קופה" value={newSnapshotFundCode} onChange={function (event) {
                return onNewSnapshotFundCodeChange(event.target.value);
            }}/>
              <input type="text" className="crm-snapshot-input" placeholder="שם קופה" value={newSnapshotFundName} onChange={function (event) {
                return onNewSnapshotFundNameChange(event.target.value);
            }}/>
              <input type="text" className="crm-snapshot-input" placeholder="סוג קופה" value={newSnapshotFundType} onChange={function (event) {
                return onNewSnapshotFundTypeChange(event.target.value);
            }}/>
              <input type="text" className="crm-snapshot-input" placeholder="סכום" value={newSnapshotAmount} onChange={function (event) {
                return onNewSnapshotAmountChange(event.target.value);
            }}/>
              <input type="date" className="crm-snapshot-input" value={newSnapshotDate} onChange={function (event) {
                return onNewSnapshotDateChange(event.target.value);
            }}/>
              <button type="button" className="crm-snapshot-button" onClick={onCreateSnapshot}>
                יצירת צילום
              </button>
            </div>
            {latestSnapshots.length > 0 && (<div className="crm-snapshot-actions">
                <button type="button" className="crm-snapshot-export-button" onClick={onExportClientReport}>
                  הורדת דוח לקוח (CSV)
                </button>
                <button type="button" className="crm-snapshot-export-button crm-snapshot-export-button-secondary" onClick={onExportClientPdf}>
                  דוח PDF
                </button>
              </div>)}
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
              {latestSnapshots.map(function (snapshot) { return (<tr key={snapshot.id} className={selectedSnapshot && selectedSnapshot.id === snapshot.id
                    ? "snapshot-row snapshot-row-selected"
                    : "snapshot-row"} onClick={function () { return onSelectSnapshot(snapshot); }}>
                  <td>{snapshot.snapshotDate}</td>
                  <td>{snapshot.fundCode}</td>
                  <td>{snapshot.fundName}</td>
                  <td>{snapshot.fundType}</td>
                  <td>{snapshot.amount.toLocaleString()}</td>
                </tr>); })}
              {latestSnapshots.length === 0 && !loading && (<tr>
                  <td colSpan={5} className="status-text">
                    אין נתוני מוצרים ללקוח
                  </td>
                </tr>)}
            </tbody>
          </table>

          <div className="crm-history-section">
            <h3 className="panel-subtitle">היסטוריה חודשית ללקוח</h3>
            <ul className="crm-history-list">
              {clientHistory.map(function (point) { return (<li key={point.month}>
                  <span>{point.month}</span>
                  <span>{point.amount.toLocaleString()}</span>
                </li>); })}
              {clientHistory.length === 0 && !loading && (<li className="status-text">אין היסטוריה ללקוח</li>)}
            </ul>
            {historyChartPoints.length >= 2 && (<div className="crm-history-chart">
                <svg viewBox="0 0 100 100" className="crm-history-chart-svg" preserveAspectRatio="none">
                  <path d={historyChartPath} className="crm-history-chart-line"/>
                  {historyChartPoints.map(function (point, index) { return (<circle key={"".concat(point.x, "-").concat(point.y, "-").concat(index)} cx={point.x} cy={point.y} r={1.5} className="crm-history-chart-point"/>); })}
                </svg>
              </div>)}
          </div>

          <div className="crm-history-fund">
            <h3 className="panel-subtitle">היסטוריית קופה</h3>
            {selectedSnapshot ? (<div>
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
                    {fundHistory.map(function (row) { return (<tr key={row.date + row.source}>
                        <td>{row.date}</td>
                        <td>{row.amount.toLocaleString()}</td>
                        <td>{row.source}</td>
                        <td>
                          {row.change === null || row.change === undefined
                        ? "-"
                        : row.change.toLocaleString()}
                        </td>
                      </tr>); })}
                    {fundHistory.length === 0 && !loading && (<tr>
                        <td colSpan={4} className="status-text">
                          אין היסטוריה לקופה שנבחרה
                        </td>
                      </tr>)}
                  </tbody>
                </table>
              </div>) : (<div className="status-text">בחר שורת צילום להצגת היסטוריית קופה</div>)}
          </div>

          <div className="crm-notes-section">
            <h3 className="panel-subtitle">הערות ותזכורות</h3>
            <form className="crm-note-form" onSubmit={onSubmitNote}>
              <textarea className="crm-note-input" value={newNoteText} onChange={function (event) {
                return onNewNoteTextChange(event.target.value);
            }} placeholder="הוסף הערה ללקוח..."/>
              <div className="crm-note-form-row">
                <input type="date" className="crm-note-date" value={newNoteReminder} onChange={function (event) {
                return onNewNoteReminderChange(event.target.value);
            }}/>
                <button type="submit" className="crm-note-button">
                  שמירת הערה
                </button>
              </div>
            </form>

            <ul className="crm-notes-list">
              {notes.map(function (note) { return (<li key={note.id} className="crm-note-item">
                  <div className="crm-note-text">{note.note}</div>
                  <div className="crm-note-meta">
                    <span>{note.createdAt}</span>
                    {note.reminderAt && (<span>תזכורת: {note.reminderAt}</span>)}
                    {note.dismissedAt && (<span>נסגרה: {note.dismissedAt}</span>)}
                  </div>
                  <div className="crm-note-actions">
                    <button type="button" className="crm-note-action-button" onClick={function () { return onDismissNote(note.id); }}>
                      סגירת תזכורת
                    </button>
                    <button type="button" className="crm-note-action-button" onClick={function () { return onClearNoteReminder(note.id); }}>
                      איפוס תזכורת
                    </button>
                    <button type="button" className="crm-note-action-button crm-note-action-danger" onClick={function () { return onDeleteNote(note.id); }}>
                      מחיקת הערה
                    </button>
                  </div>
                </li>); })}
              {notes.length === 0 && (<li className="status-text">אין הערות ללקוח</li>)}
            </ul>
          </div>
        </div>) : (<div className="status-text">בחר לקוח כדי להציג נתוני מוצרים והערות</div>)}
    </section>);
}
exports.default = CrmClientDetailPanel;
