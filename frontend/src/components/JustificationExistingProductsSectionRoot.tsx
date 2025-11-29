import type { ExistingProduct, SavingProduct } from "../api/justificationApi";
import type { ClientSummary } from "../api/crmApi";
import JustificationExistingProductsTable from "./JustificationExistingProductsTable";
import JustificationExistingProductCreatePanel from "./JustificationExistingProductCreatePanel";
import JustificationExistingProductEditPanel from "./JustificationExistingProductEditPanel";

type Props = {
  existingProducts: ExistingProduct[];
  selectedExistingProduct: ExistingProduct | null;
  loading: boolean;
  selectedClient: ClientSummary | null;
  existingFormMode: "none" | "create" | "edit";
  createMode: "existing" | "new";
  replacementExistingId: number | null;
  savingProducts: SavingProduct[];
  selectedFundTypeFilter: string;
  savingProductSearch: string;
  selectedSavingProduct: SavingProduct | null;
  newExistingPersonalNumber: string;
  newExistingAccumulatedAmount: string;
  newExistingManagementFeeBalance: string;
  newExistingManagementFeeContributions: string;
  newExistingEmploymentStatus: string;
  newExistingHasRegularContributions: string;
  editExistingPersonalNumber: string;
  editExistingAccumulatedAmount: string;
  editExistingManagementFeeBalance: string;
  editExistingManagementFeeContributions: string;
  editExistingEmploymentStatus: string;
  editExistingHasRegularContributions: string;
  replacementLockFundType: string | null;
  onSetExistingFormMode: (mode: "none" | "create" | "edit") => void;
  onSetReplacementExistingId: (id: number | null) => void;
  onSetSelectedExistingProduct: (product: ExistingProduct | null) => void;
  onSetCreateMode: (mode: "existing" | "new") => void;
  onSetSelectedFundTypeFilter: (value: string) => void;
  onSetSelectedSavingProduct: (product: SavingProduct | null) => void;
  onSetSavingProductSearch: (value: string) => void;
  onSetNewExistingPersonalNumber: (value: string) => void;
  onSetNewExistingAccumulatedAmount: (value: string) => void;
  onSetNewExistingManagementFeeBalance: (value: string) => void;
  onSetNewExistingManagementFeeContributions: (value: string) => void;
  onSetNewExistingEmploymentStatus: (value: string) => void;
  onSetNewExistingHasRegularContributions: (value: string) => void;
  onSetEditExistingPersonalNumber: (value: string) => void;
  onSetEditExistingAccumulatedAmount: (value: string) => void;
  onSetEditExistingManagementFeeBalance: (value: string) => void;
  onSetEditExistingManagementFeeContributions: (value: string) => void;
  onSetEditExistingEmploymentStatus: (value: string) => void;
  onSetEditExistingHasRegularContributions: (value: string) => void;
  onCreateExistingProduct: () => void;
  onCreateNewProduct: (existingProductIdOverride?: number | null) => void;
  onUpdateExistingProduct: () => void;
  onDeleteExistingProduct: () => void;
  findMatchingSavingProductForExisting: (
    product: ExistingProduct | null
  ) => SavingProduct | null;
};

function JustificationExistingProductsSectionRoot({
  existingProducts,
  selectedExistingProduct,
  loading,
  selectedClient,
  existingFormMode,
  createMode,
  replacementExistingId,
  savingProducts,
  selectedFundTypeFilter,
  savingProductSearch,
  selectedSavingProduct,
  newExistingPersonalNumber,
  newExistingAccumulatedAmount,
  newExistingManagementFeeBalance,
  newExistingManagementFeeContributions,
  newExistingEmploymentStatus,
  newExistingHasRegularContributions,
  editExistingPersonalNumber,
  editExistingAccumulatedAmount,
  editExistingManagementFeeBalance,
  editExistingManagementFeeContributions,
  editExistingEmploymentStatus,
  editExistingHasRegularContributions,
  replacementLockFundType,
  onSetExistingFormMode,
  onSetReplacementExistingId,
  onSetSelectedExistingProduct,
  onSetCreateMode,
  onSetSelectedFundTypeFilter,
  onSetSelectedSavingProduct,
  onSetSavingProductSearch,
  onSetNewExistingPersonalNumber,
  onSetNewExistingAccumulatedAmount,
  onSetNewExistingManagementFeeBalance,
  onSetNewExistingManagementFeeContributions,
  onSetNewExistingEmploymentStatus,
  onSetNewExistingHasRegularContributions,
  onSetEditExistingPersonalNumber,
  onSetEditExistingAccumulatedAmount,
  onSetEditExistingManagementFeeBalance,
  onSetEditExistingManagementFeeContributions,
  onSetEditExistingEmploymentStatus,
  onSetEditExistingHasRegularContributions,
  onCreateExistingProduct,
  onCreateNewProduct,
  onUpdateExistingProduct,
  onDeleteExistingProduct,
  findMatchingSavingProductForExisting,
}: Props) {
  return (
    <div className="existing-products-section">
      <JustificationExistingProductsTable
        existingProducts={existingProducts}
        selectedExistingProduct={selectedExistingProduct}
        loading={loading}
        selectedClient={selectedClient}
        onSetExistingFormMode={onSetExistingFormMode}
        onSetReplacementExistingId={onSetReplacementExistingId}
        onSetSelectedExistingProduct={onSetSelectedExistingProduct}
        onSetCreateMode={onSetCreateMode}
        onSetSelectedFundTypeFilter={onSetSelectedFundTypeFilter}
        onSetSelectedSavingProduct={onSetSelectedSavingProduct}
        onSetSavingProductSearch={onSetSavingProductSearch}
        onSetNewExistingAccumulatedAmount={onSetNewExistingAccumulatedAmount}
        onSetNewExistingEmploymentStatus={onSetNewExistingEmploymentStatus}
        onSetNewExistingHasRegularContributions={
          onSetNewExistingHasRegularContributions
        }
        onDeleteExistingProduct={onDeleteExistingProduct}
        findMatchingSavingProductForExisting={findMatchingSavingProductForExisting}
      />
      {existingFormMode !== "none" && (
        <div className="existing-edit-panel">
          {existingFormMode === "create" && (
            <JustificationExistingProductCreatePanel
              createMode={createMode}
              replacementExistingId={replacementExistingId}
              savingProducts={savingProducts}
              selectedFundTypeFilter={selectedFundTypeFilter}
              savingProductSearch={savingProductSearch}
              selectedSavingProduct={selectedSavingProduct}
              replacementLockFundType={replacementLockFundType}
              newExistingPersonalNumber={newExistingPersonalNumber}
              newExistingAccumulatedAmount={newExistingAccumulatedAmount}
              newExistingManagementFeeBalance={newExistingManagementFeeBalance}
              newExistingManagementFeeContributions={
                newExistingManagementFeeContributions
              }
              newExistingEmploymentStatus={newExistingEmploymentStatus}
              newExistingHasRegularContributions={
                newExistingHasRegularContributions
              }
              selectedClient={selectedClient}
              onSetSelectedFundTypeFilter={onSetSelectedFundTypeFilter}
              onSetSavingProductSearch={onSetSavingProductSearch}
              onSetSelectedSavingProduct={onSetSelectedSavingProduct}
              onSetNewExistingPersonalNumber={onSetNewExistingPersonalNumber}
              onSetNewExistingAccumulatedAmount={
                onSetNewExistingAccumulatedAmount
              }
              onSetNewExistingManagementFeeBalance={
                onSetNewExistingManagementFeeBalance
              }
              onSetNewExistingManagementFeeContributions={
                onSetNewExistingManagementFeeContributions
              }
              onSetNewExistingEmploymentStatus={
                onSetNewExistingEmploymentStatus
              }
              onSetNewExistingHasRegularContributions={
                onSetNewExistingHasRegularContributions
              }
              onCreateExistingProduct={onCreateExistingProduct}
              onCreateNewProduct={onCreateNewProduct}
            />
          )}
          {existingFormMode === "edit" && (
            <JustificationExistingProductEditPanel
              savingProducts={savingProducts}
              selectedExistingProduct={selectedExistingProduct}
              selectedSavingProduct={selectedSavingProduct}
              selectedFundTypeFilter={selectedFundTypeFilter}
              savingProductSearch={savingProductSearch}
              editExistingPersonalNumber={editExistingPersonalNumber}
              editExistingAccumulatedAmount={editExistingAccumulatedAmount}
              editExistingManagementFeeBalance={editExistingManagementFeeBalance}
              editExistingManagementFeeContributions={
                editExistingManagementFeeContributions
              }
              editExistingEmploymentStatus={editExistingEmploymentStatus}
              editExistingHasRegularContributions={
                editExistingHasRegularContributions
              }
              onSetSelectedFundTypeFilter={onSetSelectedFundTypeFilter}
              onSetSavingProductSearch={onSetSavingProductSearch}
              onSetSelectedSavingProduct={onSetSelectedSavingProduct}
              onSetEditExistingPersonalNumber={onSetEditExistingPersonalNumber}
              onSetEditExistingAccumulatedAmount={
                onSetEditExistingAccumulatedAmount
              }
              onSetEditExistingManagementFeeBalance={
                onSetEditExistingManagementFeeBalance
              }
              onSetEditExistingManagementFeeContributions={
                onSetEditExistingManagementFeeContributions
              }
              onSetEditExistingEmploymentStatus={
                onSetEditExistingEmploymentStatus
              }
              onSetEditExistingHasRegularContributions={
                onSetEditExistingHasRegularContributions
              }
              onUpdateExistingProduct={onUpdateExistingProduct}
              onDeleteExistingProduct={onDeleteExistingProduct}
            />
          )}
        </div>
      )}
    </div>
  );
}

export default JustificationExistingProductsSectionRoot;
