import React, { type ChangeEvent, useMemo, useState } from "react";
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

interface CanonicalProduct {
  fundCode: string;
  canonicalProduct: SavingProduct;
  allProducts: SavingProduct[];
}

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
  const [expandedFundCodes, setExpandedFundCodes] = useState<string[]>([]);

  const toggleFundCodeExpansion = (fundCode: string) => {
    setExpandedFundCodes((current) =>
      current.includes(fundCode)
        ? current.filter((code) => code !== fundCode)
        : [...current, fundCode]
    );
  };

  const canonicalProducts = useMemo((): CanonicalProduct[] => {
    const byFundCode: Record<string, SavingProduct[]> = {};

    // Extract the core fund code from formats like "658-274-196980 (6077380)"
    const extractCoreFundCode = (fullCode: string): string => {
      const match = fullCode.match(/\((\d+)\)/);
      if (match) {
        return match[1];
      }
      return fullCode.trim();
    };

    savingProducts.forEach((product) => {
      const rawCode = product.fundCode || "unknown";
      const coreCode = extractCoreFundCode(rawCode);
      if (!byFundCode[coreCode]) {
        byFundCode[coreCode] = [];
      }
      byFundCode[coreCode].push(product);
    });

    return Object.entries(byFundCode).map(([fundCode, products]) => {
      const sortedByYield = [...products].sort((a, b) => {
        const aYield = a.yield1yr ?? a.yield3yr ?? -Infinity;
        const bYield = b.yield1yr ?? b.yield3yr ?? -Infinity;
        return bYield - aYield;
      });

      return {
        fundCode,
        canonicalProduct: sortedByYield[0],
        allProducts: sortedByYield,
      };
    });
  }, [savingProducts]);

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
            <th className="saving-table-expand-header" />
          </tr>
        </thead>
        <tbody>
          {canonicalProducts.map((canonical) => {
            const { fundCode, canonicalProduct, allProducts } = canonical;
            const isExpanded = expandedFundCodes.includes(fundCode);
            const hasMultipleNames = allProducts.length > 1;
            const isSelected =
              selectedSavingProduct &&
              allProducts.some((p) => p.id === selectedSavingProduct.id);

            return (
              <React.Fragment key={fundCode}>
                <tr
                  className={`saving-row saving-row-collapsible${
                    isSelected ? " saving-row-selected" : ""
                  }${isExpanded ? " saving-row-expanded" : ""}`}
                  onClick={() => onSelectSavingProduct(canonicalProduct)}
                >
                  <td>{canonicalProduct.companyName}</td>
                  <td>
                    {canonicalProduct.fundName}
                    {hasMultipleNames && (
                      <span className="saving-cell-badge">
                        +{allProducts.length - 1}
                      </span>
                    )}
                  </td>
                  <td>{canonicalProduct.fundType}</td>
                  <td>{canonicalProduct.fundCode}</td>
                  <td>{canonicalProduct.yield1yr ?? "-"}</td>
                  <td>{canonicalProduct.yield3yr ?? "-"}</td>
                  <td
                    className="saving-cell-expand"
                    onClick={(e) => {
                      e.stopPropagation();
                      if (hasMultipleNames) {
                        toggleFundCodeExpansion(fundCode);
                      }
                    }}
                  >
                    {hasMultipleNames && (isExpanded ? "▲" : "▼")}
                  </td>
                </tr>
                {isExpanded && hasMultipleNames && (
                  <tr key={`${fundCode}-names`} className="saving-row-names">
                    <td colSpan={7}>
                      <div className="saving-names-list">
                        <div className="saving-names-title">
                          כל שמות הקופות לקוד {fundCode}:
                        </div>
                        <ul className="saving-names-items">
                          {allProducts.map((product) => (
                            <li
                              key={product.id}
                              className={`saving-names-item${
                                selectedSavingProduct?.id === product.id
                                  ? " saving-names-item-selected"
                                  : ""
                              }`}
                              onClick={() => onSelectSavingProduct(product)}
                            >
                              <span className="saving-names-name">
                                {product.fundName}
                              </span>
                              <span className="saving-names-company">
                                {product.companyName}
                              </span>
                              <span className="saving-names-yield">
                                תשואה: {product.yield1yr ?? "-"}
                              </span>
                            </li>
                          ))}
                        </ul>
                      </div>
                    </td>
                  </tr>
                )}
              </React.Fragment>
            );
          })}
        </tbody>
      </table>
    </section>
  );
}

export default JustificationMarketDashboard;
