import type { ExistingProduct, SavingProduct } from "../api/justificationApi";
import type { ClientSummary } from "../api/crmApi";

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
          </tr>
        </thead>
        <tbody>
          {existingProducts.map((product) => {
            const matchingSavingProduct = findMatchingSavingProductForExisting(product);
            const hasCompleteCoreData = !!product.personalNumber && !!matchingSavingProduct;

            return (
              <tr
                key={product.id}
                className={
                  selectedExistingProduct && selectedExistingProduct.id === product.id
                    ? "existing-row existing-row-selected"
                    : "existing-row"
                }
                onClick={() => {
                  onSetSelectedExistingProduct(product);
                  onSetExistingFormMode("edit");
                  onSetReplacementExistingId(null);
                }}
              >
                <td className="existing-row-status-cell">
                  {hasCompleteCoreData && (
                    <span className="existing-row-status-icon">✔</span>
                  )}
                </td>
                <td>{product.companyName}</td>
                <td>{product.fundName}</td>
                <td>{product.fundType}</td>
                <td>{product.fundCode}</td>
                <td>{product.personalNumber}</td>
                <td>
                  {product.accumulatedAmount != null
                    ? product.accumulatedAmount.toLocaleString()
                    : "-"}
                </td>
                <td>
                  <div className="existing-row-actions">
                    <button
                      type="button"
                      className="existing-row-action-button"
                      onClick={(event) => {
                        event.stopPropagation();
                        onSetSelectedExistingProduct(product);
                        onSetExistingFormMode("edit");
                        onSetReplacementExistingId(null);
                        onSetCreateMode("existing");
                        const match = findMatchingSavingProductForExisting(product);
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
                        onSetSelectedExistingProduct(product);
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
                        onSetSelectedExistingProduct(product);
                        onSetReplacementExistingId(product.id);
                        const match = findMatchingSavingProductForExisting(product);
                        if (match) {
                          onSetSelectedFundTypeFilter(match.fundType);
                          onSetSelectedSavingProduct(match);
                        } else {
                          if (product.fundType) {
                            onSetSelectedFundTypeFilter(product.fundType);
                          }
                          onSetSelectedSavingProduct(null);
                        }
                        const accValue =
                          product.accumulatedAmount != null
                            ? String(product.accumulatedAmount)
                            : "";
                        onSetNewExistingAccumulatedAmount(accValue);
                        onSetNewExistingEmploymentStatus(product.employmentStatus || "");
                        onSetNewExistingHasRegularContributions(
                          product.hasRegularContributions === true
                            ? "yes"
                            : product.hasRegularContributions === false
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
              </tr>
            );
          })}
          {existingProducts.length === 0 && !loading && selectedClient && (
            <tr>
              <td colSpan={8} className="status-text">
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
