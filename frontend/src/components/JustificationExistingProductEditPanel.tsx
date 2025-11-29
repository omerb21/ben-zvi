import type { ExistingProduct, SavingProduct } from "../api/justificationApi";

type Props = {
  savingProducts: SavingProduct[];
  selectedExistingProduct: ExistingProduct | null;
  selectedSavingProduct: SavingProduct | null;
  selectedFundTypeFilter: string;
  savingProductSearch: string;
  editExistingPersonalNumber: string;
  editExistingAccumulatedAmount: string;
  editExistingManagementFeeBalance: string;
  editExistingManagementFeeContributions: string;
  editExistingEmploymentStatus: string;
  editExistingHasRegularContributions: string;
  onSetSelectedFundTypeFilter: (value: string) => void;
  onSetSavingProductSearch: (value: string) => void;
  onSetSelectedSavingProduct: (product: SavingProduct | null) => void;
  onSetEditExistingPersonalNumber: (value: string) => void;
  onSetEditExistingAccumulatedAmount: (value: string) => void;
  onSetEditExistingManagementFeeBalance: (value: string) => void;
  onSetEditExistingManagementFeeContributions: (value: string) => void;
  onSetEditExistingEmploymentStatus: (value: string) => void;
  onSetEditExistingHasRegularContributions: (value: string) => void;
  onUpdateExistingProduct: () => void;
  onDeleteExistingProduct: () => void;
};

function JustificationExistingProductEditPanel({
  savingProducts,
  selectedExistingProduct,
  selectedSavingProduct,
  selectedFundTypeFilter,
  savingProductSearch,
  editExistingPersonalNumber,
  editExistingAccumulatedAmount,
  editExistingManagementFeeBalance,
  editExistingManagementFeeContributions,
  editExistingEmploymentStatus,
  editExistingHasRegularContributions,
  onSetSelectedFundTypeFilter,
  onSetSavingProductSearch,
  onSetSelectedSavingProduct,
  onSetEditExistingPersonalNumber,
  onSetEditExistingAccumulatedAmount,
  onSetEditExistingManagementFeeBalance,
  onSetEditExistingManagementFeeContributions,
  onSetEditExistingEmploymentStatus,
  onSetEditExistingHasRegularContributions,
  onUpdateExistingProduct,
  onDeleteExistingProduct,
}: Props) {
  return (
    <div className="existing-edit-group">
      <div className="existing-edit-title">עריכה / מחיקה של קופה קיימת</div>
      {!selectedExistingProduct && (
        <div className="status-text">בחר קופה קיימת מתוך הטבלה לעריכה</div>
      )}
      {selectedExistingProduct && selectedExistingProduct.isVirtual && (
        <div className="status-text">
          קופה זו נוצרה אוטומטית מנתוני ה‑CRM. ניתן לערוך את הנתונים כדי להתאים לקופה בשוק.
        </div>
      )}
      {selectedExistingProduct && (
        <>
          {savingProducts.length > 0 && (
            <div className="just-saving-filter">
              <div className="just-saving-filter-header">
                <span className="just-saving-filter-title">בחירת סוג מוצר וקופה מהשוק</span>
                <span className="just-saving-filter-hint">
                  בחר סוג קופה, ולאחר מכן קופה מהרשימה. הנתונים של החברה, שם הקופה, סוג וקוד
                  ייקבעו אוטומטית.
                </span>
              </div>
              <div className="just-saving-type-radios">
                {Array.from(new Set(savingProducts.map((product) => product.fundType))).map(
                  (type) => (
                    <label key={type} className="just-saving-type-option">
                      <input
                        type="radio"
                        name="saving-fund-type-edit"
                        value={type}
                        checked={selectedFundTypeFilter === type}
                        onChange={(event) =>
                          onSetSelectedFundTypeFilter(event.target.value)
                        }
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
          <div className="existing-edit-row">
            <label className="existing-edit-label">חברה</label>
            <div className="existing-edit-value">
              {selectedSavingProduct
                ? selectedSavingProduct.companyName
                : selectedExistingProduct.companyName}
            </div>
          </div>
          <div className="existing-edit-row">
            <label className="existing-edit-label">שם קופה</label>
            <div className="existing-edit-value">
              {selectedSavingProduct
                ? selectedSavingProduct.fundName
                : selectedExistingProduct.fundName}
            </div>
          </div>
          <div className="existing-edit-row">
            <label className="existing-edit-label">סוג קופה</label>
            <div className="existing-edit-value">
              {selectedSavingProduct
                ? selectedSavingProduct.fundType
                : selectedExistingProduct.fundType}
            </div>
          </div>
          <div className="existing-edit-row">
            <label className="existing-edit-label">קוד קופה</label>
            <div className="existing-edit-value">
              {selectedSavingProduct
                ? selectedSavingProduct.fundCode
                : selectedExistingProduct.fundCode}
            </div>
          </div>
          <div className="existing-edit-row">
            <label className="existing-edit-label">מס' אישי</label>
            <input
              className="existing-edit-input"
              value={editExistingPersonalNumber}
              onChange={(event) =>
                onSetEditExistingPersonalNumber(event.target.value)
              }
            />
          </div>
          <div className="existing-edit-row">
            <label className="existing-edit-label">יתרה</label>
            <input
              className="existing-edit-input"
              value={editExistingAccumulatedAmount}
              onChange={(event) =>
                onSetEditExistingAccumulatedAmount(event.target.value)
              }
            />
          </div>
          <div className="existing-edit-row">
            <label className="existing-edit-label">דמי ניהול מצבירה</label>
            <input
              className="existing-edit-input"
              value={editExistingManagementFeeBalance}
              onChange={(event) =>
                onSetEditExistingManagementFeeBalance(event.target.value)
              }
            />
          </div>
          <div className="existing-edit-row">
            <label className="existing-edit-label">דמי ניהול מהפקדה</label>
            <input
              className="existing-edit-input"
              value={editExistingManagementFeeContributions}
              onChange={(event) =>
                onSetEditExistingManagementFeeContributions(event.target.value)
              }
            />
          </div>
          <div className="existing-edit-row">
            <label className="existing-edit-label">מעמד</label>
            <div className="existing-edit-radio-group">
              <label className="existing-edit-radio-option">
                <input
                  type="radio"
                  name="edit-existing-employment"
                  value="שכיר"
                  checked={editExistingEmploymentStatus === "שכיר"}
                  onChange={(event) =>
                    onSetEditExistingEmploymentStatus(event.target.value)
                  }
                />
                <span>שכיר</span>
              </label>
              <label className="existing-edit-radio-option">
                <input
                  type="radio"
                  name="edit-existing-employment"
                  value="עצמאי"
                  checked={editExistingEmploymentStatus === "עצמאי"}
                  onChange={(event) =>
                    onSetEditExistingEmploymentStatus(event.target.value)
                  }
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
                  name="edit-existing-regular"
                  value="yes"
                  checked={editExistingHasRegularContributions === "yes"}
                  onChange={(event) =>
                    onSetEditExistingHasRegularContributions(event.target.value)
                  }
                />
                <span>כן</span>
              </label>
              <label className="existing-edit-radio-option">
                <input
                  type="radio"
                  name="edit-existing-regular"
                  value="no"
                  checked={editExistingHasRegularContributions === "no"}
                  onChange={(event) =>
                    onSetEditExistingHasRegularContributions(event.target.value)
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
              onClick={onUpdateExistingProduct}
            >
              שמור שינויים
            </button>
            <button
              type="button"
              className="existing-edit-delete-button"
              onClick={onDeleteExistingProduct}
            >
              מחיקת קופה
            </button>
          </div>
        </>
      )}
    </div>
  );
}

export default JustificationExistingProductEditPanel;
