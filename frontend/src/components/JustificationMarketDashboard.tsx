import type { ChangeEvent } from "react";
import type { SavingProduct } from "../api/justificationApi";

type Props = {
  savingProducts: SavingProduct[];
  selectedSavingProduct: SavingProduct | null;
  onSelectSavingProduct: (product: SavingProduct) => void;
  importStatus: string | null;
  importError: string | null;
  loading: boolean;
  error: string | null;
  gemelFile: File | null;
  isGemelImporting: boolean;
  isJustificationClearing: boolean;
  onGemelFileChange: (event: ChangeEvent<HTMLInputElement>) => void;
  onRunGemelImport: () => void;
  onClearJustificationData: () => void;
};

function JustificationMarketDashboard({
  savingProducts,
  selectedSavingProduct,
  onSelectSavingProduct,
  importStatus,
  importError,
  loading,
  error,
  gemelFile,
  isGemelImporting,
  isJustificationClearing,
  onGemelFileChange,
  onRunGemelImport,
  onClearJustificationData,
}: Props) {
  return (
    <section className="just-panel">
      <h2 className="panel-title">דשבורד הנמקה</h2>
      {importStatus && <div className="admin-import-status">{importStatus}</div>}
      {importError && (
        <div className="admin-import-status admin-import-status-error">{importError}</div>
      )}
      <div className="just-dashboard-import-card">
        <div className="just-dashboard-import-title">
          ניהול קבצי הנמקה (גמל-נט / מחיקת נתונים)
        </div>
        <div className="admin-import-group">
          <input
            type="file"
            accept=".xml"
            className="admin-import-file"
            onChange={onGemelFileChange}
          />
          <button
            type="button"
            className="admin-import-button"
            onClick={onRunGemelImport}
            disabled={!gemelFile || isGemelImporting || isJustificationClearing}
          >
            ייבוא גמל-נט (XML)
          </button>
          <button
            type="button"
            className="admin-import-button"
            onClick={onClearJustificationData}
            disabled={isGemelImporting || isJustificationClearing}
          >
            מחיקת נתוני הנמקה
          </button>
        </div>
      </div>
      {loading && <div className="status-text">טוען נתונים…</div>}
      {error && <div className="status-text status-error">{error}</div>}
      <table className="saving-table">
        <thead>
          <tr>
            <th>חברה</th>
            <th>שם קופה</th>
            <th>סוג</th>
            <th>קוד</th>
            <th>תשואה 12 חודשים</th>
            <th>תשואה 36 חודשים</th>
          </tr>
        </thead>
        <tbody>
          {savingProducts.map((product) => (
            <tr
              key={product.id}
              className={
                selectedSavingProduct && selectedSavingProduct.id === product.id
                  ? "saving-row saving-row-selected"
                  : "saving-row"
              }
              onClick={() => onSelectSavingProduct(product)}
            >
              <td>{product.companyName}</td>
              <td>{product.fundName}</td>
              <td>{product.fundType}</td>
              <td>{product.fundCode}</td>
              <td>{product.yield1yr ?? "-"}</td>
              <td>{product.yield3yr ?? "-"}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </section>
  );
}

export default JustificationMarketDashboard;
