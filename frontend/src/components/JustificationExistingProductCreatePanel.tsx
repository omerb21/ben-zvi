import type { SavingProduct } from "../api/justificationApi";
import type { ClientSummary } from "../api/crmApi";

type Props = {
  createMode: "existing" | "new";
  replacementExistingId: number | null;
  savingProducts: SavingProduct[];
  selectedFundTypeFilter: string;
  savingProductSearch: string;
  selectedSavingProduct: SavingProduct | null;
  replacementLockFundType: string | null;
  newExistingPersonalNumber: string;
  newExistingAccumulatedAmount: string;
  newExistingManagementFeeBalance: string;
  newExistingManagementFeeContributions: string;
  newExistingEmploymentStatus: string;
  newExistingHasRegularContributions: string;
  selectedClient: ClientSummary | null;
  onSetSelectedFundTypeFilter: (value: string) => void;
  onSetSavingProductSearch: (value: string) => void;
  onSetSelectedSavingProduct: (product: SavingProduct | null) => void;
  onSetNewExistingPersonalNumber: (value: string) => void;
  onSetNewExistingAccumulatedAmount: (value: string) => void;
  onSetNewExistingManagementFeeBalance: (value: string) => void;
  onSetNewExistingManagementFeeContributions: (value: string) => void;
  onSetNewExistingEmploymentStatus: (value: string) => void;
  onSetNewExistingHasRegularContributions: (value: string) => void;
  onCreateExistingProduct: () => void;
  onCreateNewProduct: (existingProductIdOverride?: number | null) => void;
};

function JustificationExistingProductCreatePanel({
  createMode,
  replacementExistingId,
  savingProducts,
  selectedFundTypeFilter,
  savingProductSearch,
  selectedSavingProduct,
  replacementLockFundType,
  newExistingPersonalNumber,
  newExistingAccumulatedAmount,
  newExistingManagementFeeBalance,
  newExistingManagementFeeContributions,
  newExistingEmploymentStatus,
  newExistingHasRegularContributions,
  selectedClient,
  onSetSelectedFundTypeFilter,
  onSetSavingProductSearch,
  onSetSelectedSavingProduct,
  onSetNewExistingPersonalNumber,
  onSetNewExistingAccumulatedAmount,
  onSetNewExistingManagementFeeBalance,
  onSetNewExistingManagementFeeContributions,
  onSetNewExistingEmploymentStatus,
  onSetNewExistingHasRegularContributions,
  onCreateExistingProduct,
  onCreateNewProduct,
}: Props) {
  return (
    <div className="existing-edit-group">
      <div className="existing-edit-title">
        {createMode === "existing"
          ? "הוספת קופה קיימת ידנית"
          : replacementExistingId
          ? "יצירת קופה חלופית"
          : "צור קופה חדשה"}
      </div>
      {savingProducts.length > 0 && (
        <div className="just-saving-filter">
          <div className="just-saving-filter-header">
            <span className="just-saving-filter-title">בחירת סוג מוצר וקופה מהשוק</span>
            <span className="just-saving-filter-hint">
              בחר סוג קופה, ולאחר מכן קופה מהרשימה. הנתונים של החברה, שם הקופה, סוג וקוד ייקבעו
              אוטומטית.
            </span>
          </div>
          <div className="just-saving-type-radios">
            {Array.from(new Set(savingProducts.map((product) => product.fundType))).map(
              (type) => (
                <label key={type} className="just-saving-type-option">
                  <input
                    type="radio"
                    name="saving-fund-type"
                    value={type}
                    checked={selectedFundTypeFilter === type}
                    onChange={(event) => onSetSelectedFundTypeFilter(event.target.value)}
                    disabled={!!replacementLockFundType && replacementLockFundType !== type}
                  />
                  <span>{type}</span>
                </label>
              )
            )}
          </div>
          {selectedFundTypeFilter && (
            <div className="just-saving-filter-table-wrapper">
              <input
                className="existing-edit-input"
                placeholder="חיפוש קופה לפי שם / חברה / קוד"
                value={savingProductSearch}
                onChange={(event) => onSetSavingProductSearch(event.target.value)}
              />
              <select
                className="just-saving-select"
                value={
                  selectedSavingProduct &&
                  selectedSavingProduct.fundType === selectedFundTypeFilter
                    ? String(selectedSavingProduct.id)
                    : ""
                }
                onChange={(event) => {
                  const value = event.target.value;
                  if (!value) {
                    onSetSelectedSavingProduct(null);
                    return;
                  }
                  const id = Number(value);
                  const product =
                    savingProducts.find(
                      (p) => p.id === id && p.fundType === selectedFundTypeFilter
                    ) || null;
                  onSetSelectedSavingProduct(product);
                }}
              >
                <option value="">בחר קופה מהרשימה</option>
                {savingProducts
                  .filter((product) => product.fundType === selectedFundTypeFilter)
                  .filter((product) => {
                    const term = savingProductSearch.trim().toLowerCase();
                    if (!term) {
                      return true;
                    }
                    const company = (product.companyName || "").toLowerCase();
                    const name = (product.fundName || "").toLowerCase();
                    const code = (product.fundCode || "").toLowerCase();
                    return (
                      company.includes(term) ||
                      name.includes(term) ||
                      code.includes(term)
                    );
                  })
                  .map((product) => (
                    <option key={product.id} value={String(product.id)}>
                      {product.companyName} - {product.fundName} ({product.fundCode})
                    </option>
                  ))}
              </select>
            </div>
          )}
        </div>
      )}
      <div className="status-text">
        בחר קודם קופה מטבלת הקופות מעל. שדות החברה/שם/סוג/קוד ייקבעו אוטומטית.
      </div>
      <div className="existing-edit-row">
        <label className="existing-edit-label">חברה</label>
        <div className="existing-edit-value">
          {selectedSavingProduct ? selectedSavingProduct.companyName : "לא נבחרה קופה"}
        </div>
      </div>
      <div className="existing-edit-row">
        <label className="existing-edit-label">שם קופה</label>
        <div className="existing-edit-value">
          {selectedSavingProduct ? selectedSavingProduct.fundName : ""}
        </div>
      </div>
      <div className="existing-edit-row">
        <label className="existing-edit-label">סוג קופה</label>
        <div className="existing-edit-value">
          {selectedSavingProduct ? selectedSavingProduct.fundType : ""}
        </div>
      </div>
      <div className="existing-edit-row">
        <label className="existing-edit-label">קוד קופה</label>
        <div className="existing-edit-value">
          {selectedSavingProduct ? selectedSavingProduct.fundCode : ""}
        </div>
      </div>
      <div className="existing-edit-row">
        <label className="existing-edit-label">מס' אישי</label>
        <input
          className="existing-edit-input"
          value={newExistingPersonalNumber}
          onChange={(event) => onSetNewExistingPersonalNumber(event.target.value)}
        />
      </div>
      <div className="existing-edit-row">
        <label className="existing-edit-label">יתרה</label>
        <input
          className="existing-edit-input"
          value={newExistingAccumulatedAmount}
          onChange={(event) => onSetNewExistingAccumulatedAmount(event.target.value)}
        />
      </div>
      <div className="existing-edit-row">
        <label className="existing-edit-label">דמי ניהול מצבירה</label>
        <input
          className="existing-edit-input"
          value={newExistingManagementFeeBalance}
          onChange={(event) => onSetNewExistingManagementFeeBalance(event.target.value)}
        />
      </div>
      <div className="existing-edit-row">
        <label className="existing-edit-label">דמי ניהול מהפקדה</label>
        <input
          className="existing-edit-input"
          value={newExistingManagementFeeContributions}
          onChange={(event) =>
            onSetNewExistingManagementFeeContributions(event.target.value)
          }
        />
      </div>
      <div className="existing-edit-row">
        <label className="existing-edit-label">מעמד</label>
        <div className="existing-edit-radio-group">
          <label className="existing-edit-radio-option">
            <input
              type="radio"
              name="new-existing-employment"
              value="שכיר"
              checked={newExistingEmploymentStatus === "שכיר"}
              onChange={(event) => onSetNewExistingEmploymentStatus(event.target.value)}
            />
            <span>שכיר</span>
          </label>
          <label className="existing-edit-radio-option">
            <input
              type="radio"
              name="new-existing-employment"
              value="עצמאי"
              checked={newExistingEmploymentStatus === "עצמאי"}
              onChange={(event) => onSetNewExistingEmploymentStatus(event.target.value)}
            />
            <span>עצמאי</span>
          </label>
        </div>
      </div>
      <div className="existing-edit-row">
        <label className="existing-edit-label">האם יש הפקדות שוטפות</label>
        <div className="existing-edit-radio-group">
          <label className="existing-edit-radio-option">
            <input
              type="radio"
              name="new-existing-regular"
              value="yes"
              checked={newExistingHasRegularContributions === "yes"}
              onChange={(event) =>
                onSetNewExistingHasRegularContributions(event.target.value)
              }
            />
            <span>כן</span>
          </label>
          <label className="existing-edit-radio-option">
            <input
              type="radio"
              name="new-existing-regular"
              value="no"
              checked={newExistingHasRegularContributions === "no"}
              onChange={(event) =>
                onSetNewExistingHasRegularContributions(event.target.value)
              }
            />
            <span>לא</span>
          </label>
        </div>
      </div>
      <div className="existing-edit-actions">
        <button
          type="button"
          className="existing-edit-save-button"
          disabled={
            !selectedClient ||
            !selectedSavingProduct ||
            (createMode === "existing" && !newExistingPersonalNumber.trim())
          }
          onClick={() => {
            if (createMode === "existing") {
              onCreateExistingProduct();
            } else {
              const existingId = replacementExistingId ?? null;
              onCreateNewProduct(existingId);
            }
          }}
        >
          {createMode === "existing"
            ? "הוסף קופה קיימת"
            : replacementExistingId
            ? "צור קופה חלופית"
            : "צור קופה חדשה"}
        </button>
      </div>
    </div>
  );
}

export default JustificationExistingProductCreatePanel;
