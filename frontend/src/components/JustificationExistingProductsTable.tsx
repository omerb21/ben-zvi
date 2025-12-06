import React, { useMemo, useState } from "react";
import type { ExistingProduct, SavingProduct } from "../api/justificationApi";
import type { ClientSummary } from "../api/crmApi";

interface CanonicalExistingProduct {
  fundCode: string;
  canonicalProduct: ExistingProduct;
  totalAmount: number;
  allProducts: ExistingProduct[];
}

type Props = {
  existingProducts: ExistingProduct[];
  selectedExistingProduct: ExistingProduct | null;
  loading: boolean;
  selectedClient: ClientSummary | null;
  onSetExistingFormMode: (mode: "none" | "create" | "edit") => void;
  onSetReplacementExistingId: (id: number | null) => void;
  onSetSelectedExistingProduct: (product: ExistingProduct | null) => void;
  onSetCreateMode: (mode: "existing" | "new") => void;
  onSetSelectedFundTypeFilter: (value: string) => void;
  onSetSelectedSavingProduct: (product: SavingProduct | null) => void;
  onSetSavingProductSearch: (value: string) => void;
  onSetNewExistingAccumulatedAmount: (value: string) => void;
  onSetNewExistingEmploymentStatus: (value: string) => void;
  onSetNewExistingHasRegularContributions: (value: string) => void;
  onDeleteExistingProduct: () => void;
  findMatchingSavingProductForExisting: (
    product: ExistingProduct | null
  ) => SavingProduct | null;
};

function JustificationExistingProductsTable({
  existingProducts,
  selectedExistingProduct,
  loading,
  selectedClient,
  onSetExistingFormMode,
  onSetReplacementExistingId,
  onSetSelectedExistingProduct,
  onSetCreateMode,
  onSetSelectedFundTypeFilter,
  onSetSelectedSavingProduct,
  onSetSavingProductSearch,
  onSetNewExistingAccumulatedAmount,
  onSetNewExistingEmploymentStatus,
  onSetNewExistingHasRegularContributions,
  onDeleteExistingProduct,
  findMatchingSavingProductForExisting,
}: Props) {
  const [expandedFundCodes, setExpandedFundCodes] = useState<string[]>([]);

  const toggleFundCodeExpansion = (fundCode: string) => {
    setExpandedFundCodes((current) =>
      current.includes(fundCode)
        ? current.filter((code) => code !== fundCode)
        : [...current, fundCode]
    );
  };

  const canonicalProducts = useMemo((): CanonicalExistingProduct[] => {
    const byFundCode: Record<string, ExistingProduct[]> = {};

    // Extract the core fund code from personalNumber (מס' אישי) - same logic as CRM
    // Format is "(6077380) 827-274-196980" - extract the number in parentheses
    const extractCoreFundCode = (personalNum: string): string => {
      const match = personalNum.match(/\((\d+)\)/);
      if (match) {
        return match[1];
      }
      return personalNum.trim();
    };

    existingProducts.forEach((product) => {
      const rawCode = product.personalNumber || "unknown";
      const coreCode = extractCoreFundCode(rawCode);
      if (!byFundCode[coreCode]) {
        byFundCode[coreCode] = [];
      }
      byFundCode[coreCode].push(product);
    });

    return Object.entries(byFundCode).map(([fundCode, products]) => {
      const totalAmount = products.reduce(
        (sum, p) => sum + (p.accumulatedAmount || 0),
        0
      );
      const sortedByAmount = [...products].sort(
        (a, b) => (b.accumulatedAmount || 0) - (a.accumulatedAmount || 0)
      );
      const canonicalProduct = sortedByAmount[0];

      return {
        fundCode,
        canonicalProduct,
        totalAmount,
        allProducts: sortedByAmount,
      };
    });
  }, [existingProducts]);

  const totalCanonicalAmount = useMemo(() => {
    return canonicalProducts.reduce((sum, item) => sum + item.totalAmount, 0);
  }, [canonicalProducts]);

  return (
    <>
      <div className="existing-products-header">
        <h3 className="panel-subtitle">מוצרים קיימים ללקוח</h3>
        <div className="existing-products-actions">
          <button
            type="button"
            className="existing-row-action-button"
            onClick={() => {
              onSetExistingFormMode("create");
              onSetReplacementExistingId(null);
              onSetSelectedExistingProduct(null);
              onSetCreateMode("existing");
            }}
          >
            צור קופה קיימת
          </button>
          <button
            type="button"
            className="existing-row-action-button"
            disabled={!selectedClient}
            onClick={() => {
              onSetExistingFormMode("create");
              onSetReplacementExistingId(null);
              onSetCreateMode("new");
            }}
          >
            צור קופה חדשה
          </button>
        </div>
      </div>
      <table className="existing-products-table">
        <thead>
          <tr>
            <th></th>
            <th>חברה</th>
            <th>שם קופה</th>
            <th>סוג קופה</th>
            <th>קוד קופה</th>
            <th>מס' אישי</th>
            <th>יתרה</th>
            <th>פעולות</th>
            <th className="existing-expand-header" />
          </tr>
        </thead>
        <tbody>
          {canonicalProducts.map((canonical) => {
            const { fundCode, canonicalProduct, totalAmount, allProducts } = canonical;
            const isExpanded = expandedFundCodes.includes(fundCode);
            const hasMultipleNames = allProducts.length > 1;
            const isSelected =
              selectedExistingProduct &&
              allProducts.some((p) => p.id === selectedExistingProduct.id);
            const matchingSavingProduct = findMatchingSavingProductForExisting(canonicalProduct);
            const hasCompleteCoreData = !!canonicalProduct.personalNumber && !!matchingSavingProduct;

            return (
              <React.Fragment key={fundCode}>
                <tr
                  className={`existing-row existing-row-collapsible${
                    isSelected ? " existing-row-selected" : ""
                  }${isExpanded ? " existing-row-expanded" : ""}`}
                  onClick={() => {
                    onSetSelectedExistingProduct(canonicalProduct);
                    onSetExistingFormMode("edit");
                    onSetReplacementExistingId(null);
                  }}
                >
                  <td className="existing-row-status-cell">
                    {hasCompleteCoreData && (
                      <span className="existing-row-status-icon">✔</span>
                    )}
                  </td>
                  <td>{canonicalProduct.companyName}</td>
                  <td>
                    {canonicalProduct.fundName}
                    {hasMultipleNames && (
                      <span className="existing-cell-badge">
                        +{allProducts.length - 1}
                      </span>
                    )}
                  </td>
                  <td>{canonicalProduct.fundType}</td>
                  <td>{canonicalProduct.fundCode}</td>
                  <td>{canonicalProduct.personalNumber}</td>
                  <td>{totalAmount.toLocaleString()}</td>
                  <td>
                    <div className="existing-row-actions">
                      <button
                        type="button"
                        className="existing-row-action-button"
                        onClick={(event) => {
                          event.stopPropagation();
                          onSetSelectedExistingProduct(canonicalProduct);
                          onSetExistingFormMode("edit");
                          onSetReplacementExistingId(null);
                          onSetCreateMode("existing");
                          const match = findMatchingSavingProductForExisting(canonicalProduct);
                          if (match) {
                            onSetSelectedFundTypeFilter(match.fundType);
                            onSetSelectedSavingProduct(match);
                          } else {
                            onSetSelectedSavingProduct(null);
                          }
                          onSetSavingProductSearch("");
                        }}
                      >
                        עריכה
                      </button>
                      <button
                        type="button"
                        className="existing-row-action-button"
                        onClick={(event) => {
                          event.stopPropagation();
                          onSetSelectedExistingProduct(canonicalProduct);
                          onDeleteExistingProduct();
                        }}
                      >
                        מחק
                      </button>
                      <button
                        type="button"
                        className="existing-row-action-button"
                        disabled={!selectedClient}
                        onClick={(event) => {
                          event.stopPropagation();
                          onSetSelectedExistingProduct(canonicalProduct);
                          onSetReplacementExistingId(canonicalProduct.id);
                          const match = findMatchingSavingProductForExisting(canonicalProduct);
                          if (match) {
                            onSetSelectedFundTypeFilter(match.fundType);
                            onSetSelectedSavingProduct(match);
                          } else {
                            if (canonicalProduct.fundType) {
                              onSetSelectedFundTypeFilter(canonicalProduct.fundType);
                            }
                            onSetSelectedSavingProduct(null);
                          }
                          const accValue =
                            canonicalProduct.accumulatedAmount != null
                              ? String(canonicalProduct.accumulatedAmount)
                              : "";
                          onSetNewExistingAccumulatedAmount(accValue);
                          onSetNewExistingEmploymentStatus(canonicalProduct.employmentStatus || "");
                          onSetNewExistingHasRegularContributions(
                            canonicalProduct.hasRegularContributions === true
                              ? "yes"
                              : canonicalProduct.hasRegularContributions === false
                              ? "no"
                              : ""
                          );
                          onSetSavingProductSearch("");
                          onSetExistingFormMode("create");
                          onSetCreateMode("new");
                        }}
                      >
                        קופה חלופית
                      </button>
                    </div>
                  </td>
                  <td
                    className="existing-cell-expand"
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
                  <tr className="existing-row-names">
                    <td colSpan={9}>
                      <div className="existing-names-list">
                        <div className="existing-names-title">
                          כל שמות הקופות לקוד {fundCode}:
                        </div>
                        <ul className="existing-names-items">
                          {allProducts.map((product) => (
                            <li
                              key={product.id}
                              className={`existing-names-item${
                                selectedExistingProduct?.id === product.id
                                  ? " existing-names-item-selected"
                                  : ""
                              }`}
                              onClick={() => {
                                onSetSelectedExistingProduct(product);
                                onSetExistingFormMode("edit");
                                onSetReplacementExistingId(null);
                              }}
                            >
                              <span className="existing-names-name">
                                {product.fundName || "(ללא שם)"}
                              </span>
                              <span className="existing-names-amount">
                                {product.accumulatedAmount != null
                                  ? product.accumulatedAmount.toLocaleString()
                                  : "-"}
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
          {canonicalProducts.length > 0 && (
            <tr className="existing-total-row">
              <td colSpan={6} className="existing-total-label">
                סה"כ יתרות ללקוח
              </td>
              <td>{totalCanonicalAmount.toLocaleString()}</td>
              <td colSpan={2} />
            </tr>
          )}
          {existingProducts.length === 0 && !loading && selectedClient && (
            <tr>
              <td colSpan={9} className="status-text">
                אין מוצרים קיימים ללקוח זה
              </td>
            </tr>
          )}
        </tbody>
      </table>
    </>
  );
}

export default JustificationExistingProductsTable;
