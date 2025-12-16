import { useEffect, useState } from "react";
import type {
  Client,
  ClientSummary,
  Snapshot,
} from "../../api/crmApi";
import {
  fetchClientSummaries,
  fetchClient,
  fetchClientSnapshots,
} from "../../api/crmApi";
import type {
  ExistingProduct,
  NewProduct,
  FormInstance,
} from "../../api/justificationApi";
import {
  fetchExistingProductsForClient,
  fetchNewProductsForClient,
  syncClientProductsFromCrm,
} from "../../api/justificationApi";
import type { Dispatch, SetStateAction } from "react";

export type UseJustificationClientsArgs = {
  initialClientId?: number | null;
  setLoading: Dispatch<SetStateAction<boolean>>;
  setError: Dispatch<SetStateAction<string | null>>;
};

export function useJustificationClients({
  initialClientId = null,
  setLoading,
  setError,
}: UseJustificationClientsArgs) {
  const [clients, setClients] = useState<ClientSummary[]>([]);
  const [selectedClient, setSelectedClient] =
    useState<ClientSummary | null>(null);
  const [clientFilter, setClientFilter] = useState("");
  const [existingProducts, setExistingProducts] = useState<ExistingProduct[]>(
    []
  );
  const [crmSnapshots, setCrmSnapshots] = useState<Snapshot[]>([]);
  const [newProducts, setNewProducts] = useState<NewProduct[]>([]);
  const [formInstances, setFormInstances] = useState<FormInstance[]>([]);
  const [selectedExistingProduct, setSelectedExistingProduct] =
    useState<ExistingProduct | null>(null);
  const [selectedNewProduct, setSelectedNewProduct] =
    useState<NewProduct | null>(null);
  const [selectedClientDetails, setSelectedClientDetails] =
    useState<Client | null>(null);
  const [existingFormMode, setExistingFormMode] =
    useState<"none" | "create" | "edit">("none");

  useEffect(() => {
    setLoading(true);
    fetchClientSummaries()
      .then((clientSummaries) => {
        setClients(clientSummaries);
        if (clientSummaries.length > 0) {
          const initial =
            initialClientId != null
              ? clientSummaries.find((client) => client.id === initialClientId) ||
                clientSummaries[0]
              : clientSummaries[0];
          setSelectedClient(initial);
        }
        setError(null);
      })
      .catch(() => {
        setError("שגיאה בטעינת רשימת לקוחות להנמקה");
      })
      .finally(() => {
        setLoading(false);
      });
  }, [initialClientId, setError, setLoading]);

  useEffect(() => {
    if (!selectedClient) {
      setExistingProducts([]);
      setCrmSnapshots([]);
      setNewProducts([]);
      setSelectedExistingProduct(null);
      setSelectedNewProduct(null);
      setFormInstances([]);
      setSelectedClientDetails(null);
      setExistingFormMode("none");
      return;
    }

    setLoading(true);
    Promise.all([
      fetchExistingProductsForClient(selectedClient.id),
      fetchNewProductsForClient(selectedClient.id),
      fetchClient(selectedClient.id),
      fetchClientSnapshots(selectedClient.id),
    ])
      .then(([existingProductsData, newProductsData, clientDetails, snapshotsData]) => {
        setExistingProducts(existingProductsData);
        setNewProducts(newProductsData);
        setSelectedClientDetails(clientDetails);
        setCrmSnapshots(snapshotsData);
        setError(null);
      })
      .catch(() => {
        setError("שגיאה בטעינת נתוני מוצרים ללקוח");
      })
      .finally(() => {
        setLoading(false);
      });
  }, [selectedClient, setError, setLoading]);

  const handleSyncFromCrm = () => {
    if (!selectedClient) {
      return;
    }
    setLoading(true);
    syncClientProductsFromCrm(selectedClient.id)
      .then(() => {
        return fetchExistingProductsForClient(selectedClient.id);
      })
      .then((products) => {
        setExistingProducts(products);
      })
      .catch((err) => {
        // eslint-disable-next-line no-console
        console.error(err);
        setError("שגיאה בסנכרון מוצרים מ-CRM");
      })
      .finally(() => {
        setLoading(false);
      });
  };

  return {
    clients,
    selectedClient,
    clientFilter,
    existingProducts,
    crmSnapshots,
    newProducts,
    formInstances,
    selectedExistingProduct,
    selectedNewProduct,
    selectedClientDetails,
    existingFormMode,
    setSelectedClient,
    setClientFilter,
    setExistingProducts,
    setCrmSnapshots,
    setNewProducts,
    setFormInstances,
    setSelectedExistingProduct,
    setSelectedNewProduct,
    setSelectedClientDetails,
    setExistingFormMode,
    handleSyncFromCrm,
  };
}
