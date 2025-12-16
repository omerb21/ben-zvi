import { useEffect, useState } from "react";
import type { Dispatch, SetStateAction } from "react";
import type {
  SavingProduct,
  ExistingProduct,
  NewProduct,
  FormInstance,
} from "../../api/justificationApi";
import { fetchSavingProducts } from "../../api/justificationApi";
import type { ClientSummary } from "../../api/crmApi";
import {
  createExistingProductAction,
  updateExistingProductAction,
  deleteExistingProductAction,
} from "./justExistingProductsActions";
import {
  selectNewProductAction,
  createFormInstanceAction,
  createNewProductAction,
  deleteNewProductAction,
  deleteFormInstanceAction,
} from "./justNewProductsAndFormsActions";
import {
  findMatchingSavingProductForExisting as findMatchingSavingProductForExistingUtil,
} from "../../components/justification/justificationMatching";

export type UseJustificationProductsArgs = {
  savingProductsReloadKey: number;
  selectedClient: ClientSummary | null;
  existingProducts: ExistingProduct[];
  newProducts: NewProduct[];
  selectedExistingProduct: ExistingProduct | null;
  selectedNewProduct: NewProduct | null;
  existingFormMode: "none" | "create" | "edit";
  setExistingProducts: Dispatch<SetStateAction<ExistingProduct[]>>;
  setNewProducts: Dispatch<SetStateAction<NewProduct[]>>;
  setFormInstances: Dispatch<SetStateAction<FormInstance[]>>;
  setSelectedExistingProduct: Dispatch<SetStateAction<ExistingProduct | null>>;
  setSelectedNewProduct: Dispatch<SetStateAction<NewProduct | null>>;
  setLoading: Dispatch<SetStateAction<boolean>>;
  setError: Dispatch<SetStateAction<string | null>>;
};

export function useJustificationProducts({
  savingProductsReloadKey,
  selectedClient,
  existingProducts,
  newProducts,
  selectedExistingProduct,
  selectedNewProduct,
  existingFormMode,
  setExistingProducts,
  setNewProducts,
  setFormInstances,
  setSelectedExistingProduct,
  setSelectedNewProduct,
  setLoading,
  setError,
}: UseJustificationProductsArgs) {
  const [savingProducts, setSavingProducts] = useState<SavingProduct[]>([]);
  const [selectedSavingProduct, setSelectedSavingProduct] =
    useState<SavingProduct | null>(null);
  const [newFormTemplate, setNewFormTemplate] = useState("");
  const [selectedFundTypeFilter, setSelectedFundTypeFilter] = useState("");
  const [savingProductSearch, setSavingProductSearch] = useState("");
  const [replacementExistingId, setReplacementExistingId] =
    useState<number | null>(null);
  const [createMode, setCreateMode] = useState<"existing" | "new">("existing");
  const [newExistingFundType, setNewExistingFundType] = useState("");
  const [newExistingCompanyName, setNewExistingCompanyName] = useState("");
  const [newExistingFundName, setNewExistingFundName] = useState("");
  const [newExistingFundCode, setNewExistingFundCode] = useState("");
  const [newExistingPersonalNumber, setNewExistingPersonalNumber] =
    useState("");
  const [newExistingAccumulatedAmount, setNewExistingAccumulatedAmount] =
    useState("");
  const [newExistingManagementFeeBalance, setNewExistingManagementFeeBalance] =
    useState("");
  const [
    newExistingManagementFeeContributions,
    setNewExistingManagementFeeContributions,
  ] = useState("");
  const [newExistingEmploymentStatus, setNewExistingEmploymentStatus] =
    useState("");
  const [
    newExistingHasRegularContributions,
    setNewExistingHasRegularContributions,
  ] = useState("");
  const [editExistingFundType, setEditExistingFundType] = useState("");
  const [editExistingCompanyName, setEditExistingCompanyName] = useState("");
  const [editExistingFundName, setEditExistingFundName] = useState("");
  const [editExistingFundCode, setEditExistingFundCode] = useState("");
  const [editExistingPersonalNumber, setEditExistingPersonalNumber] =
    useState("");
  const [editExistingAccumulatedAmount, setEditExistingAccumulatedAmount] =
    useState("");
  const [
    editExistingManagementFeeBalance,
    setEditExistingManagementFeeBalance,
  ] = useState("");
  const [
    editExistingManagementFeeContributions,
    setEditExistingManagementFeeContributions,
  ] = useState("");
  const [editExistingEmploymentStatus, setEditExistingEmploymentStatus] =
    useState("");
  const [
    editExistingHasRegularContributions,
    setEditExistingHasRegularContributions,
  ] = useState("");

  useEffect(() => {
    setLoading(true);
    fetchSavingProducts()
      .then((products) => {
        setSavingProducts(products);
        setError(null);
      })
      .catch(() => {
        setError("שגיאה בטעינת טבלת קופות");
      })
      .finally(() => {
        setLoading(false);
      });
  }, [savingProductsReloadKey, setError, setLoading]);

  useEffect(() => {
    if (!selectedExistingProduct) {
      setEditExistingFundType("");
      setEditExistingCompanyName("");
      setEditExistingFundName("");
      setEditExistingFundCode("");
      setEditExistingPersonalNumber("");
      setEditExistingAccumulatedAmount("");
      setEditExistingManagementFeeBalance("");
      setEditExistingManagementFeeContributions("");
      setEditExistingEmploymentStatus("");
      setEditExistingHasRegularContributions("");
      return;
    }

    setEditExistingFundType(selectedExistingProduct.fundType || "");
    setEditExistingCompanyName(selectedExistingProduct.companyName || "");
    setEditExistingFundName(selectedExistingProduct.fundName || "");
    setEditExistingFundCode(selectedExistingProduct.fundCode || "");
    setEditExistingPersonalNumber(
      selectedExistingProduct.personalNumber || "",
    );
    setEditExistingAccumulatedAmount(
      selectedExistingProduct.accumulatedAmount != null
        ? String(selectedExistingProduct.accumulatedAmount)
        : "",
    );
    setEditExistingManagementFeeBalance("");
    setEditExistingManagementFeeContributions(
      selectedExistingProduct.managementFeeContributions != null
        ? String(selectedExistingProduct.managementFeeContributions)
        : "",
    );
    setEditExistingEmploymentStatus(
      selectedExistingProduct.employmentStatus || "",
    );
    setEditExistingHasRegularContributions(
      selectedExistingProduct.hasRegularContributions === true
        ? "yes"
        : selectedExistingProduct.hasRegularContributions === false
        ? "no"
        : "",
    );
  }, [selectedExistingProduct]);

  useEffect(() => {
    if (!selectedExistingProduct || !selectedSavingProduct) {
      return;
    }
    if (existingFormMode !== "edit") {
      return;
    }

    setEditExistingFundType(selectedSavingProduct.fundType || "");
    setEditExistingCompanyName(selectedSavingProduct.companyName || "");
    setEditExistingFundName(selectedSavingProduct.fundName || "");
    setEditExistingFundCode(selectedSavingProduct.fundCode || "");
  }, [selectedSavingProduct, selectedExistingProduct, existingFormMode]);

  const findMatchingSavingProductForExisting = (
    product: ExistingProduct | null,
  ): SavingProduct | null => {
    return findMatchingSavingProductForExistingUtil(product, savingProducts);
  };

  const replacementSourceProduct =
    replacementExistingId !== null
      ? existingProducts.find((p) => p.id === replacementExistingId) || null
      : null;

  let replacementLockFundType: string | null = null;
  if (createMode === "new" && replacementSourceProduct) {
    if (replacementSourceProduct.fundType) {
      replacementLockFundType = replacementSourceProduct.fundType;
    } else {
      const autoMatch = findMatchingSavingProductForExisting(
        replacementSourceProduct,
      );
      if (autoMatch) {
        replacementLockFundType = autoMatch.fundType;
      }
    }
  }

  const sortedNewProducts = [...newProducts].sort((a, b) => {
    const aExisting = a.existingProductId ?? null;
    const bExisting = b.existingProductId ?? null;

    if (aExisting != null && bExisting != null) {
      if (aExisting !== bExisting) {
        return aExisting - bExisting;
      }
      return a.id - b.id;
    }

    if (aExisting != null && bExisting == null) {
      return -1;
    }
    if (aExisting == null && bExisting != null) {
      return 1;
    }

    return a.id - b.id;
  });

  const findExistingForNew = (product: NewProduct): ExistingProduct | null => {
    if (product.existingProductId == null) {
      return null;
    }
    return (
      existingProducts.find(
        (existing) => existing.id === product.existingProductId,
      ) || null
    );
  };

  const handleCreateExistingProduct = () => {
    createExistingProductAction({
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
    });
  };

  const handleUpdateExistingProduct = () => {
    updateExistingProductAction({
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
    });
  };

  const handleDeleteExistingProduct = () => {
    deleteExistingProductAction({
      selectedExistingProduct,
      setLoading,
      setExistingProducts,
      setSelectedExistingProduct,
      setError,
    });
  };

  const handleSelectNewProduct = (product: NewProduct) => {
    selectNewProductAction({
      product,
      setSelectedNewProduct,
      setFormInstances,
      setLoading,
      setError,
    });
  };

  const handleCreateFormInstance = () => {
    createFormInstanceAction({
      selectedNewProduct,
      newFormTemplate,
      setLoading,
      setFormInstances,
      setNewFormTemplate,
      setError,
    });
  };

  const handleCreateNewProduct = (existingProductIdOverride?: number | null) => {
    createNewProductAction({
      selectedClient,
      selectedSavingProduct,
      selectedExistingProduct,
      newExistingAccumulatedAmount,
      newExistingManagementFeeBalance,
      newExistingManagementFeeContributions,
      newExistingEmploymentStatus,
      newExistingHasRegularContributions,
      existingProductIdOverride,
      setLoading,
      setNewProducts,
      setExistingProducts,
      setSelectedExistingProduct,
      setReplacementExistingId,
      setError,
    });
  };

  const handleDeleteNewProduct = (productId: number) => {
    deleteNewProductAction({
      productId,
      selectedNewProduct,
      setLoading,
      setNewProducts,
      setSelectedNewProduct,
      setFormInstances,
      setError,
    });
  };

  const handleDeleteFormInstance = (formId: number) => {
    deleteFormInstanceAction({
      formId,
      setLoading,
      setFormInstances,
      setError,
    });
  };

  return {
    savingProducts,
    selectedSavingProduct,
    newFormTemplate,
    selectedFundTypeFilter,
    savingProductSearch,
    replacementExistingId,
    createMode,
    newExistingFundType,
    newExistingCompanyName,
    newExistingFundName,
    newExistingFundCode,
    newExistingPersonalNumber,
    newExistingAccumulatedAmount,
    newExistingManagementFeeBalance,
    newExistingManagementFeeContributions,
    newExistingEmploymentStatus,
    newExistingHasRegularContributions,
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
    replacementLockFundType,
    sortedNewProducts,
    findExistingForNew,
    findMatchingSavingProductForExisting,
    handleCreateExistingProduct,
    handleCreateNewProduct,
    handleUpdateExistingProduct,
    handleDeleteExistingProduct,
    handleSelectNewProduct,
    handleCreateFormInstance,
    handleDeleteNewProduct,
    handleDeleteFormInstance,
    setSelectedSavingProduct,
    setNewFormTemplate,
    setSelectedFundTypeFilter,
    setSavingProductSearch,
    setReplacementExistingId,
    setCreateMode,
    setNewExistingFundType,
    setNewExistingCompanyName,
    setNewExistingFundName,
    setNewExistingFundCode,
    setNewExistingPersonalNumber,
    setNewExistingAccumulatedAmount,
    setNewExistingManagementFeeBalance,
    setNewExistingManagementFeeContributions,
    setNewExistingEmploymentStatus,
    setNewExistingHasRegularContributions,
    setEditExistingFundType,
    setEditExistingCompanyName,
    setEditExistingFundName,
    setEditExistingFundCode,
    setEditExistingPersonalNumber,
    setEditExistingAccumulatedAmount,
    setEditExistingManagementFeeBalance,
    setEditExistingManagementFeeContributions,
    setEditExistingEmploymentStatus,
    setEditExistingHasRegularContributions,
  };
}
