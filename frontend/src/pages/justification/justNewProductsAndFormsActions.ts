import type { Dispatch, SetStateAction } from "react";
import type {
  SavingProduct,
  NewProduct,
  FormInstance,
  ExistingProduct,
} from "../../api/justificationApi";
import {
  fetchFormInstancesForNewProduct,
  createNewProductForClient,
  createFormInstanceForNewProduct,
  deleteNewProduct,
  deleteFormInstance,
} from "../../api/justificationApi";
import type { ClientSummary } from "../../api/crmApi";

export type SelectNewProductArgs = {
  product: NewProduct;
  setSelectedNewProduct: Dispatch<SetStateAction<NewProduct | null>>;
  setFormInstances: Dispatch<SetStateAction<FormInstance[]>>;
  setLoading: Dispatch<SetStateAction<boolean>>;
  setError: Dispatch<SetStateAction<string | null>>;
};

export function selectNewProductAction({
  product,
  setSelectedNewProduct,
  setFormInstances,
  setLoading,
  setError,
}: SelectNewProductArgs) {
  setSelectedNewProduct(product);
  setFormInstances([]);
  setLoading(true);
  fetchFormInstancesForNewProduct(product.id)
    .then((forms) => {
      setFormInstances(forms);
      setError(null);
    })
    .catch(() => {
      setError("שגיאה בטעינת טפסים");
    })
    .finally(() => {
      setLoading(false);
    });
}

export type CreateFormInstanceArgs = {
  selectedNewProduct: NewProduct | null;
  newFormTemplate: string;
  setLoading: Dispatch<SetStateAction<boolean>>;
  setFormInstances: Dispatch<SetStateAction<FormInstance[]>>;
  setNewFormTemplate: Dispatch<SetStateAction<string>>;
  setError: Dispatch<SetStateAction<string | null>>;
};

export function createFormInstanceAction({
  selectedNewProduct,
  newFormTemplate,
  setLoading,
  setFormInstances,
  setNewFormTemplate,
  setError,
}: CreateFormInstanceArgs) {
  if (!selectedNewProduct || !newFormTemplate.trim()) {
    return;
  }

  setLoading(true);
  createFormInstanceForNewProduct(selectedNewProduct.id, {
    templateFilename: newFormTemplate.trim(),
    status: null,
    filledData: null,
    fileOutputPath: null,
  })
    .then((created) => {
      setFormInstances((prev: FormInstance[]) => [created, ...prev]);
      setNewFormTemplate("");
      setError(null);
    })
    .catch(() => {
      setError("שגיאה ביצירת טופס חדש");
    })
    .finally(() => {
      setLoading(false);
    });
}

export type CreateNewProductArgs = {
  selectedClient: ClientSummary | null;
  selectedSavingProduct: SavingProduct | null;
  selectedExistingProduct: ExistingProduct | null;
  newExistingAccumulatedAmount: string;
  newExistingEmploymentStatus: string;
  newExistingHasRegularContributions: string;
  existingProductIdOverride?: number | null;
  setLoading: Dispatch<SetStateAction<boolean>>;
  setNewProducts: Dispatch<SetStateAction<NewProduct[]>>;
  setExistingProducts: Dispatch<SetStateAction<ExistingProduct[]>>;
  setSelectedExistingProduct: Dispatch<
    SetStateAction<ExistingProduct | null>
  >;
  setReplacementExistingId: Dispatch<SetStateAction<number | null>>;
  setError: Dispatch<SetStateAction<string | null>>;
};

export function createNewProductAction({
  selectedClient,
  selectedSavingProduct,
  selectedExistingProduct,
  newExistingAccumulatedAmount,
  newExistingEmploymentStatus,
  newExistingHasRegularContributions,
  existingProductIdOverride,
  setLoading,
  setNewProducts,
  setExistingProducts,
  setSelectedExistingProduct,
  setReplacementExistingId,
  setError,
}: CreateNewProductArgs) {
  if (!selectedClient || !selectedSavingProduct) {
    return;
  }

  const existingProductIdInternal =
    existingProductIdOverride !== undefined
      ? existingProductIdOverride
      : selectedExistingProduct
      ? selectedExistingProduct.id
      : null;

  const accumulatedRaw = newExistingAccumulatedAmount.trim();
  const accumulatedValue = accumulatedRaw
    ? Number(accumulatedRaw.replace(/,/g, ""))
    : null;

  const employmentStatus = newExistingEmploymentStatus.trim() || null;
  let hasRegularContributions: boolean | null = null;
  if (newExistingHasRegularContributions === "yes") {
    hasRegularContributions = true;
  } else if (newExistingHasRegularContributions === "no") {
    hasRegularContributions = false;
  }

  const existingProductIdBefore = existingProductIdInternal;

  setLoading(true);
  createNewProductForClient(selectedClient.id, {
    existingProductId: existingProductIdInternal,
    fundType: selectedSavingProduct.fundType,
    companyName: selectedSavingProduct.companyName,
    fundName: selectedSavingProduct.fundName,
    fundCode: selectedSavingProduct.fundCode,
    yield1yr: selectedSavingProduct.yield1yr ?? null,
    yield3yr: selectedSavingProduct.yield3yr ?? null,
    personalNumber: null,
    managementFeeBalance: null,
    managementFeeContributions: null,
    accumulatedAmount: accumulatedValue,
    employmentStatus,
    hasRegularContributions,
  })
    .then((product) => {
      setNewProducts((prev: NewProduct[]) => [...prev, product]);

      const newExistingIdFromProduct =
        product.existingProductId !== undefined && product.existingProductId !== null
          ? product.existingProductId
          : null;

      if (
        existingProductIdBefore != null &&
        existingProductIdBefore < 0 &&
        newExistingIdFromProduct != null &&
        newExistingIdFromProduct > 0
      ) {
        setExistingProducts((prev: ExistingProduct[]) =>
          prev.map((existing) =>
            existing.id === existingProductIdBefore
              ? { ...existing, id: newExistingIdFromProduct, isVirtual: false }
              : existing
          )
        );

        setSelectedExistingProduct((prev) =>
          prev && prev.id === existingProductIdBefore
            ? { ...prev, id: newExistingIdFromProduct, isVirtual: false }
            : prev
        );
      }

      setReplacementExistingId(null);
      setError(null);
    })
    .catch(() => {
      setError("שגיאה ביצירת מוצר חדש ללקוח");
    })
    .finally(() => {
      setLoading(false);
    });
}

export type DeleteNewProductArgs = {
  productId: number;
  selectedNewProduct: NewProduct | null;
  setLoading: Dispatch<SetStateAction<boolean>>;
  setNewProducts: Dispatch<SetStateAction<NewProduct[]>>;
  setSelectedNewProduct: Dispatch<SetStateAction<NewProduct | null>>;
  setFormInstances: Dispatch<SetStateAction<FormInstance[]>>;
  setError: Dispatch<SetStateAction<string | null>>;
};

export function deleteNewProductAction({
  productId,
  selectedNewProduct,
  setLoading,
  setNewProducts,
  setSelectedNewProduct,
  setFormInstances,
  setError,
}: DeleteNewProductArgs) {
  setLoading(true);
  deleteNewProduct(productId)
    .then(() => {
      setNewProducts((prev: NewProduct[]) =>
        prev.filter((product) => product.id !== productId)
      );
      if (selectedNewProduct && selectedNewProduct.id === productId) {
        setSelectedNewProduct(null);
        setFormInstances([]);
      }
      setError(null);
    })
    .catch(() => {
      setError("שגיאה במחיקת מוצר חדש");
    })
    .finally(() => {
      setLoading(false);
    });
}

export type DeleteFormInstanceArgs = {
  formId: number;
  setLoading: Dispatch<SetStateAction<boolean>>;
  setFormInstances: Dispatch<SetStateAction<FormInstance[]>>;
  setError: Dispatch<SetStateAction<string | null>>;
};

export function deleteFormInstanceAction({
  formId,
  setLoading,
  setFormInstances,
  setError,
}: DeleteFormInstanceArgs) {
  setLoading(true);
  deleteFormInstance(formId)
    .then(() => {
      setFormInstances((prev: FormInstance[]) =>
        prev.filter((form) => form.id !== formId)
      );
      setError(null);
    })
    .catch(() => {
      setError("שגיאה במחיקת טופס");
    })
    .finally(() => {
      setLoading(false);
    });
}
