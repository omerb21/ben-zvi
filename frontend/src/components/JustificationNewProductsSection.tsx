import { Fragment } from "react";
import type { NewProduct } from "../api/justificationApi";
import type { ClientSummary } from "../api/crmApi";

type Props = {
  sortedNewProducts: NewProduct[];
  newProducts: NewProduct[];
  selectedNewProduct: NewProduct | null;
  loading: boolean;
  selectedClient: ClientSummary | null;
  findExistingForNew: (product: NewProduct) => any;
  onSelectNewProduct: (product: NewProduct) => void;
  onDownloadKitPdf: (product: NewProduct) => void;
  onDeleteNewProduct: (productId: number) => void;
};

function JustificationNewProductsSection({
  sortedNewProducts,
  newProducts,
  selectedNewProduct,
  loading,
  selectedClient,
  findExistingForNew,
  onSelectNewProduct,
  onDownloadKitPdf,
  onDeleteNewProduct,
}: Props) {
  return (
    <section className="new-products-section">
      <h3 className="panel-subtitle">מוצרים חדשים ללקוח</h3>
      <ul className="new-products-list">
        {sortedNewProducts.map((product, index) => {
          const prev = index > 0 ? sortedNewProducts[index - 1] : null;
          const prevExisting = prev ? prev.existingProductId ?? null : null;
          const currentExisting = product.existingProductId ?? null;
          const isNewGroup = index === 0 || prevExisting !== currentExisting;

          const existingForGroup = findExistingForNew(product);

          return (
            <Fragment key={product.id}>
              {isNewGroup && (
                <li className="new-product-group-header">
                  {currentExisting != null && existingForGroup && (
                    <>
                      <span className="new-product-group-title">קופה קיימת:</span>
                      <span className="new-product-group-main">
                        {existingForGroup.companyName} - {existingForGroup.fundName}
                      </span>
                      <span className="new-product-group-meta">
                        מס' אישי: {existingForGroup.personalNumber || "-"}
                      </span>
                    </>
                  )}
                  {currentExisting != null && !existingForGroup && (
                    <span className="new-product-group-main">
                      קופה קיימת (הנתונים לא נטענו)
                    </span>
                  )}
                  {currentExisting == null && (
                    <span className="new-product-group-main">
                      מוצרים חדשים ללא קופה קיימת
                    </span>
                  )}
                </li>
              )}
              <li
                className={
                  selectedNewProduct && selectedNewProduct.id === product.id
                    ? "new-product-item new-product-item-selected"
                    : "new-product-item"
                }
                onClick={() => onSelectNewProduct(product)}
              >
                <div className="new-product-main">
                  <div className="new-product-name">{product.fundName}</div>
                  <div className="new-product-meta">{product.companyName}</div>
                </div>
                <div className="new-product-existing">
                  {(() => {
                    const existing = findExistingForNew(product);
                    if (product.existingProductId != null && existing) {
                      return (
                        <>
                          <div className="new-product-existing-title">קופה קיימת</div>
                          <div className="new-product-existing-meta">
                            {existing.companyName} - {existing.fundName}
                          </div>
                          <div className="new-product-existing-personal">
                            מס' אישי: {existing.personalNumber || "-"}
                          </div>
                        </>
                      );
                    }
                    if (product.existingProductId != null && !existing) {
                      return (
                        <div className="new-product-existing-placeholder">
                          מוצר חדש (קופה חלופית - קופה קיימת לא נטענה)
                        </div>
                      );
                    }
                    return (
                      <div className="new-product-existing-placeholder">
                        מוצר חדש ללא קופה קיימת
                      </div>
                    );
                  })()}
                </div>
                <div className="new-product-actions">
                  <button
                    type="button"
                    className="new-product-kit-button"
                    onClick={(event) => {
                      event.stopPropagation();
                      onDownloadKitPdf(product);
                    }}
                  >
                    הורדת קיט
                  </button>
                  <button
                    type="button"
                    className="new-product-delete-button"
                    onClick={(event) => {
                      event.stopPropagation();
                      onDeleteNewProduct(product.id);
                    }}
                  >
                    מחק
                  </button>
                </div>
              </li>
            </Fragment>
          );
        })}
        {newProducts.length === 0 && !loading && selectedClient && (
          <li className="status-text">אין מוצרים חדשים ללקוח זה</li>
        )}
        {newProducts.length === 0 && !loading && !selectedClient && (
          <li className="status-text">בחר לקוח כדי להציג מוצרים חדשים</li>
        )}
      </ul>
    </section>
  );
}

export default JustificationNewProductsSection;
