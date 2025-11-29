import type { Dispatch, SetStateAction } from "react";
import type {
  ExistingProduct,
  SavingProduct,
} from "../../api/justificationApi";
import {
  createExistingProductForClient,
  updateExistingProduct,
  deleteExistingProduct,
} from "../../api/justificationApi";
import type { ClientSummary } from "../../api/crmApi";

export type CreateExistingProductArgs = {
  selectedClient: ClientSummary | null;
  selectedSavingProduct: SavingProduct | null;
  newExistingPersonalNumber: string;
  newExistingAccumulatedAmount: string;
  newExistingManagementFeeBalance: string;
  newExistingManagementFeeContributions: string;
  newExistingEmploymentStatus: string;
  newExistingHasRegularContributions: string;
  setLoading: Dispatch<SetStateAction<boolean>>;
  setExistingProducts: Dispatch<SetStateAction<ExistingProduct[]>>;
  setNewExistingPersonalNumber: Dispatch<SetStateAction<string>>;
  setNewExistingAccumulatedAmount: Dispatch<SetStateAction<string>>;
  setNewExistingManagementFeeBalance: Dispatch<SetStateAction<string>>;
  setNewExistingManagementFeeContributions: Dispatch<SetStateAction<string>>;
  setNewExistingEmploymentStatus: Dispatch<SetStateAction<string>>;
  setNewExistingHasRegularContributions: Dispatch<SetStateAction<string>>;
  setError: Dispatch<SetStateAction<string | null>>;
};

export function createExistingProductAction({
  selectedClient,
  selectedSavingProduct,
  newExistingPersonalNumber,
  newExistingAccumulatedAmount,
  newExistingManagementFeeBalance,
  newExistingManagementFeeContributions,
  newExistingEmploymentStatus,
  newExistingHasRegularContributions,
  setLoading,
  setExistingProducts,
  setNewExistingPersonalNumber,
  setNewExistingAccumulatedAmount,
  setNewExistingManagementFeeBalance,
  setNewExistingManagementFeeContributions,
  setNewExistingEmploymentStatus,
  setNewExistingHasRegularContributions,
  setError,
}: CreateExistingProductArgs) {
  if (!selectedClient || !selectedSavingProduct) {
    return;
  }
  if (!newExistingPersonalNumber.trim()) {
    return;
  }

  setLoading(true);
  const accumulatedRaw = newExistingAccumulatedAmount.trim();
  const accumulatedValue = accumulatedRaw
    ? Number(accumulatedRaw.replace(/,/g, ""))
    : null;
  const mgmtBalanceRaw = newExistingManagementFeeBalance.trim();
  const mgmtBalanceValue = mgmtBalanceRaw
    ? Number(mgmtBalanceRaw.replace(/,/g, ""))
    : null;
  const mgmtContribRaw = newExistingManagementFeeContributions.trim();
  const mgmtContribValue = mgmtContribRaw
    ? Number(mgmtContribRaw.replace(/,/g, ""))
    : null;

  const employmentStatus = newExistingEmploymentStatus.trim() || null;
  let hasRegularContributions: boolean | null = null;
  if (newExistingHasRegularContributions === "yes") {
    hasRegularContributions = true;
  } else if (newExistingHasRegularContributions === "no") {
    hasRegularContributions = false;
  }

  createExistingProductForClient(selectedClient.id, {
    fundType: selectedSavingProduct.fundType,
    companyName: selectedSavingProduct.companyName,
    fundName: selectedSavingProduct.fundName,
    fundCode: selectedSavingProduct.fundCode,
    yield1yr: null,
    yield3yr: null,
    personalNumber: newExistingPersonalNumber.trim(),
    managementFeeBalance: mgmtBalanceValue,
    managementFeeContributions: mgmtContribValue,
    accumulatedAmount: accumulatedValue,
    employmentStatus,
    hasRegularContributions,
  })
    .then((created) => {
      setExistingProducts((prev: ExistingProduct[]) => [...prev, created]);
      setNewExistingPersonalNumber("");
      setNewExistingAccumulatedAmount("");
      setNewExistingManagementFeeBalance("");
      setNewExistingManagementFeeContributions("");
      setNewExistingEmploymentStatus("");
      setNewExistingHasRegularContributions("");
      setError(null);
    })
    .catch(() => {
      setError("שגיאה בהוספת קופה קיימת");
    })
    .finally(() => {
      setLoading(false);
    });
}

export type UpdateExistingProductArgs = {
  selectedClient: ClientSummary | null;
  selectedExistingProduct: ExistingProduct | null;
  selectedSavingProduct: SavingProduct | null;
  editExistingFundType: string;
  editExistingCompanyName: string;
  editExistingFundName: string;
  editExistingFundCode: string;
  editExistingPersonalNumber: string;
  editExistingAccumulatedAmount: string;
  editExistingManagementFeeBalance: string;
  editExistingManagementFeeContributions: string;
  editExistingEmploymentStatus: string;
  editExistingHasRegularContributions: string;
  setLoading: Dispatch<SetStateAction<boolean>>;
  setExistingProducts: Dispatch<SetStateAction<ExistingProduct[]>>;
  setSelectedExistingProduct: Dispatch<
    SetStateAction<ExistingProduct | null>
  >;
  setError: Dispatch<SetStateAction<string | null>>;
};

export function updateExistingProductAction({
  selectedClient,
  selectedExistingProduct,
  selectedSavingProduct,
  editExistingFundType,
  editExistingCompanyName,
  editExistingFundName,
  editExistingFundCode,
  editExistingPersonalNumber,
  editExistingAccumulatedAmount,
  editExistingManagementFeeBalance,
  editExistingManagementFeeContributions,
  editExistingEmploymentStatus,
  editExistingHasRegularContributions,
  setLoading,
  setExistingProducts,
  setSelectedExistingProduct,
  setError,
}: UpdateExistingProductArgs) {
  if (!selectedExistingProduct) {
    return;
  }

  const accumulatedRaw = editExistingAccumulatedAmount.trim();
  const accumulatedValue = accumulatedRaw
    ? Number(accumulatedRaw.replace(/,/g, ""))
    : null;
  const mgmtBalanceRaw = editExistingManagementFeeBalance.trim();
  const mgmtBalanceValue = mgmtBalanceRaw
    ? Number(mgmtBalanceRaw.replace(/,/g, ""))
    : null;
  const mgmtContribRaw = editExistingManagementFeeContributions.trim();
  const mgmtContribValue = mgmtContribRaw
    ? Number(mgmtContribRaw.replace(/,/g, ""))
    : null;

  const employmentStatus = editExistingEmploymentStatus.trim() || null;
  let hasRegularContributions: boolean | null = null;
  if (editExistingHasRegularContributions === "yes") {
    hasRegularContributions = true;
  } else if (editExistingHasRegularContributions === "no") {
    hasRegularContributions = false;
  }

  setLoading(true);

  if (selectedExistingProduct.isVirtual) {
    if (!selectedClient || !selectedSavingProduct) {
      setError("בחר קופה מהשוק לפני עדכון קופה מ-CRM");
      setLoading(false);
      return;
    }

    const resolvedPersonalNumber =
      editExistingPersonalNumber.trim() || selectedExistingProduct.personalNumber;

    createExistingProductForClient(selectedClient.id, {
      fundType: selectedSavingProduct.fundType,
      companyName: selectedSavingProduct.companyName,
      fundName: selectedSavingProduct.fundName,
      fundCode: selectedSavingProduct.fundCode,
      yield1yr: selectedSavingProduct.yield1yr ?? null,
      yield3yr: selectedSavingProduct.yield3yr ?? null,
      personalNumber: resolvedPersonalNumber,
      managementFeeBalance: mgmtBalanceValue,
      managementFeeContributions: mgmtContribValue,
      accumulatedAmount: accumulatedValue,
      employmentStatus,
      hasRegularContributions,
    })
      .then((created) => {
        setExistingProducts((prev: ExistingProduct[]) =>
          prev.map((product) =>
            product.id === selectedExistingProduct.id ? created : product
          )
        );
        setSelectedExistingProduct(created);
        setError(null);
      })
      .catch(() => {
        setError("שגיאה בעדכון קופה קיימת");
      })
      .finally(() => {
        setLoading(false);
      });

    return;
  }

  const updatePayload = {
    personalNumber: editExistingPersonalNumber.trim() || null,
    accumulatedAmount: accumulatedValue,
    managementFeeBalance: mgmtBalanceValue,
    managementFeeContributions: mgmtContribValue,
    employmentStatus,
    hasRegularContributions,
  } as const;

  const finalPayload: any = {
    ...updatePayload,
    fundType: editExistingFundType.trim() || selectedExistingProduct.fundType,
    companyName:
      editExistingCompanyName.trim() || selectedExistingProduct.companyName,
    fundName: editExistingFundName.trim() || selectedExistingProduct.fundName,
    fundCode: editExistingFundCode.trim() || selectedExistingProduct.fundCode,
  };

  if (selectedSavingProduct) {
    finalPayload.fundType = selectedSavingProduct.fundType;
    finalPayload.companyName = selectedSavingProduct.companyName;
    finalPayload.fundName = selectedSavingProduct.fundName;
    finalPayload.fundCode = selectedSavingProduct.fundCode;
  }

  updateExistingProduct(selectedExistingProduct.id, finalPayload)
    .then((updated) => {
      setExistingProducts((prev: ExistingProduct[]) =>
        prev.map((product) => (product.id === updated.id ? { ...updated } : product))
      );
      setSelectedExistingProduct(updated);
      setError(null);
    })
    .catch(() => {
      setError("שגיאה בעדכון קופה קיימת");
    })
    .finally(() => {
      setLoading(false);
    });
}

export type DeleteExistingProductArgs = {
  selectedExistingProduct: ExistingProduct | null;
  setLoading: Dispatch<SetStateAction<boolean>>;
  setExistingProducts: Dispatch<SetStateAction<ExistingProduct[]>>;
  setSelectedExistingProduct: Dispatch<
    SetStateAction<ExistingProduct | null>
  >;
  setError: Dispatch<SetStateAction<string | null>>;
};

export function deleteExistingProductAction({
  selectedExistingProduct,
  setLoading,
  setExistingProducts,
  setSelectedExistingProduct,
  setError,
}: DeleteExistingProductArgs) {
  if (!selectedExistingProduct) {
    return;
  }

  if (selectedExistingProduct.isVirtual) {
    setExistingProducts((prev: ExistingProduct[]) =>
      prev.filter((product) => product.id !== selectedExistingProduct.id)
    );
    setSelectedExistingProduct(null);
    setError(null);
    return;
  }

  setLoading(true);
  deleteExistingProduct(selectedExistingProduct.id)
    .then(() => {
      setExistingProducts((prev: ExistingProduct[]) =>
        prev.filter((product) => product.id !== selectedExistingProduct.id)
      );
      setSelectedExistingProduct(null);
      setError(null);
    })
    .catch(() => {
      setError("שגיאה במחיקת קופה קיימת");
    })
    .finally(() => {
      setLoading(false);
    });
}
