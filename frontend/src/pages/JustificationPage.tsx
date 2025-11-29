import { useEffect, useState, ChangeEvent } from "react";
import {
  SavingProduct,
  NewProduct,
  ExistingProduct,
  FormInstance,
  fetchSavingProducts,
  fetchNewProductsForClient,
  fetchExistingProductsForClient,
  fetchFormInstancesForNewProduct,
  createNewProductForClient,
  createFormInstanceForNewProduct,
  deleteNewProduct,
  deleteFormInstance,
  createExistingProductForClient,
  updateExistingProduct,
  deleteExistingProduct,
  buildAdvicePdfUrl,
  buildB1PdfUrl,
  buildKitPdfUrl,
  buildPacketPdfUrl,
  createPacketSignRequest,
  buildSignedClientPacketPdfUrl,
  uploadPacketPdf,
  trimPacketPdf,
} from "../api/justificationApi";
import { importGemelNetXml, clearJustificationData } from "../api/adminApi";
import { Client, ClientSummary, fetchClientSummaries, fetchClient } from "../api/crmApi";
import "../styles/justification.css";
import JustificationTabs from "../components/JustificationTabs";
import JustificationMarketDashboard from "../components/JustificationMarketDashboard";
import JustificationFormsPanel from "../components/JustificationFormsPanel";
import JustificationClientHeader from "../components/JustificationClientHeader";
import JustificationExistingProductsSection from "../components/JustificationExistingProductsSectionRoot";
import JustificationNewProductsSection from "../components/JustificationNewProductsSection";
import { useJustificationPdfAndPackets } from "../components/justification/useJustificationPdfAndPackets";
import { useAdobePdfViewer } from "../components/justification/useAdobePdfViewer";
import { useJustificationGemel } from "../components/justification/useJustificationGemel";
import { findMatchingSavingProductForExisting as findMatchingSavingProductForExistingUtil } from "../components/justification/justificationMatching";

type Props = {
  savingProductsReloadKey?: number;
  initialClientId?: number | null;
  onGemelNetImportCompleted?: () => void;
};

function JustificationPage({
  savingProductsReloadKey = 0,
  initialClientId = null,
  onGemelNetImportCompleted,
}: Props) {
  const [savingProducts, setSavingProducts] = useState<SavingProduct[]>([]);
  const [selectedSavingProduct, setSelectedSavingProduct] =
    useState<SavingProduct | null>(null);
  const [clients, setClients] = useState<ClientSummary[]>([]);
  const [selectedClient, setSelectedClient] = useState<ClientSummary | null>(null);
  const [clientFilter, setClientFilter] = useState("");
  const [existingProducts, setExistingProducts] = useState<ExistingProduct[]>([]);
  const [selectedExistingProduct, setSelectedExistingProduct] =
    useState<ExistingProduct | null>(null);
  const [newProducts, setNewProducts] = useState<NewProduct[]>([]);
  const [formInstances, setFormInstances] = useState<FormInstance[]>([]);
  const [selectedNewProduct, setSelectedNewProduct] = useState<NewProduct | null>(null);
  const [newFormTemplate, setNewFormTemplate] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [viewMode, setViewMode] = useState<"client" | "market" | "forms">("client");
  const [selectedClientDetails, setSelectedClientDetails] = useState<Client | null>(null);
  const [selectedFundTypeFilter, setSelectedFundTypeFilter] = useState("");
  const [savingProductSearch, setSavingProductSearch] = useState("");
  const [existingFormMode, setExistingFormMode] = useState<"none" | "create" | "edit">("none");
  const [replacementExistingId, setReplacementExistingId] = useState<number | null>(null);
  const [createMode, setCreateMode] = useState<"existing" | "new">("existing");
  const [newExistingFundType, setNewExistingFundType] = useState("");
  const [newExistingCompanyName, setNewExistingCompanyName] = useState("");
  const [newExistingFundName, setNewExistingFundName] = useState("");
  const [newExistingFundCode, setNewExistingFundCode] = useState("");
  const [newExistingPersonalNumber, setNewExistingPersonalNumber] = useState("");
  const [newExistingAccumulatedAmount, setNewExistingAccumulatedAmount] = useState("");
  const [newExistingManagementFeeBalance, setNewExistingManagementFeeBalance] =
    useState("");
  const [newExistingManagementFeeContributions, setNewExistingManagementFeeContributions] =
    useState("");
  const [newExistingEmploymentStatus, setNewExistingEmploymentStatus] = useState("");
  const [newExistingHasRegularContributions, setNewExistingHasRegularContributions] =
    useState("");
  const [editExistingFundType, setEditExistingFundType] = useState("");
  const [editExistingCompanyName, setEditExistingCompanyName] = useState("");
  const [editExistingFundName, setEditExistingFundName] = useState("");
  const [editExistingFundCode, setEditExistingFundCode] = useState("");
  const [editExistingPersonalNumber, setEditExistingPersonalNumber] = useState("");
  const [editExistingAccumulatedAmount, setEditExistingAccumulatedAmount] = useState("");
  const [editExistingManagementFeeBalance, setEditExistingManagementFeeBalance] =
    useState("");
  const [editExistingManagementFeeContributions, setEditExistingManagementFeeContributions] =
    useState("");
  const [editExistingEmploymentStatus, setEditExistingEmploymentStatus] = useState("");
  const [editExistingHasRegularContributions, setEditExistingHasRegularContributions] =
    useState("");
  const {
    gemelFile,
    isGemelImporting,
    isJustificationClearing,
    importStatus,
    importError,
    handleGemelFileChange,
    handleRunGemelImport,
    handleClearJustificationData,
  } = useJustificationGemel(onGemelNetImportCompleted);
  const {
    pdfGenerationMessage,
    pdfGenerationIsError,
    packetSignLink,
    packetSignError,
    isPacketSignLoading,
    packetTrimInput,
    packetTrimStatus,
    packetTrimIsError,
    packetUploadFile,
    packetUploadStatus,
    packetUploadIsError,
    clientExportsStatus,
    clientExportsIsError,
    isDeletingClientExports,
    handleOpenAdviceHtml,
    handleDownloadB1Pdf,
    handleGenerateAllKits,
    handleDownloadKitPdf,
    handleGeneratePacketPdf,
    handlePreviewPacketPdf,
    handlePreviewSignedPacketPdf,
    handleCreatePacketSignLink,
    handleTrimPacketPages,
    handlePacketUploadFileChange,
    handleUploadPacketPdf,
    handleDeleteClientExports,
    setPacketTrimInput,
  } = useJustificationPdfAndPackets(selectedClient, newProducts);
  useAdobePdfViewer();

  const handlePreviewAdvicePdf = () => {
    if (!selectedClient) {
      return;
    }
    const url = buildAdvicePdfUrl(selectedClient.id);
    window.open(url, "_blank");
  };

  const handlePreviewB1Pdf = () => {
    if (!selectedClient) {
      return;
    }
    const url = buildB1PdfUrl(selectedClient.id);
    window.open(url, "_blank");
  };

  const handlePreviewKitPdf = (product: NewProduct) => {
    if (!selectedClient) {
      return;
    }
    const url = buildKitPdfUrl(selectedClient.id, product.id);
    window.open(url, "_blank");
  };

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
  }, [savingProductsReloadKey]);
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
  }, []);

  useEffect(() => {
    if (!selectedClient) {
      setExistingProducts([]);
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
    ])
      .then(([existingProductsData, newProductsData, clientDetails]) => {
        setExistingProducts(existingProductsData);
        setNewProducts(newProductsData);
        setSelectedClientDetails(clientDetails);
        setError(null);
      })
      .catch(() => {
        setError("שגיאה בטעינת נתוני מוצרים ללקוח");
      })
      .finally(() => {
        setLoading(false);
      });
  }, [selectedClient]);

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
    setEditExistingPersonalNumber(selectedExistingProduct.personalNumber || "");
    setEditExistingAccumulatedAmount(
      selectedExistingProduct.accumulatedAmount != null
        ? String(selectedExistingProduct.accumulatedAmount)
        : ""
    );
    setEditExistingManagementFeeBalance("");
    setEditExistingManagementFeeContributions(
      selectedExistingProduct.managementFeeContributions != null
        ? String(selectedExistingProduct.managementFeeContributions)
        : ""
    );
    setEditExistingEmploymentStatus(selectedExistingProduct.employmentStatus || "");
    setEditExistingHasRegularContributions(
      selectedExistingProduct.hasRegularContributions === true
        ? "yes"
        : selectedExistingProduct.hasRegularContributions === false
        ? "no"
        : ""
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
    product: ExistingProduct | null
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
      const autoMatch = findMatchingSavingProductForExisting(replacementSourceProduct);
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
        (existing) => existing.id === product.existingProductId
      ) || null
    );
  };

  const handleSelectNewProduct = (product: NewProduct) => {
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
  };

  const handleCreateExistingProduct = () => {
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
  };

  const handleUpdateExistingProduct = () => {
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
            prev.map((product) => (product.id === selectedExistingProduct.id ? created : product))
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
      companyName: editExistingCompanyName.trim() || selectedExistingProduct.companyName,
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
  };

  const handleDeleteExistingProduct = () => {
    if (!selectedExistingProduct) {
      return;
    }

    // קופה וירטואלית (מ-CRM): הסרה מקומית בלבד במודול ההנמקה
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
  };

  const handleCreateFormInstance = () => {
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
  };

  const handleCreateNewProduct = (existingProductIdOverride?: number | null) => {
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
  };

  const handleDeleteNewProduct = (productId: number) => {
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
  };

  const handleDeleteFormInstance = (formId: number) => {
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
  };

  if (viewMode === "market") {
    return (
      <div className="justification-page-wrapper">
        <JustificationTabs currentView={viewMode} onChangeView={setViewMode} />
        <div className="justification-page">
          <JustificationMarketDashboard
            savingProducts={savingProducts}
            selectedSavingProduct={selectedSavingProduct}
            onSelectSavingProduct={setSelectedSavingProduct}
            importStatus={importStatus}
            importError={importError}
            loading={loading}
            error={error}
            gemelFile={gemelFile}
            isGemelImporting={isGemelImporting}
            isJustificationClearing={isJustificationClearing}
            onGemelFileChange={handleGemelFileChange}
            onRunGemelImport={handleRunGemelImport}
            onClearJustificationData={handleClearJustificationData}
          />
        </div>
      </div>
    );
  }

  if (viewMode === "forms") {
    return (
      <div className="justification-page-wrapper">
        <JustificationTabs currentView={viewMode} onChangeView={setViewMode} />
        <div className="justification-page">
          <section className="just-panel just-middle">
            <h2 className="panel-title">
              עריכת טפסי PDF ללקוח
              {selectedClient ? ` - ${selectedClient.fullName}` : ""}
            </h2>
            {!selectedClient && (
              <div className="status-text">
                בחר לקוח בלשונית "הנמקה ללקוח" כדי להציג ולערוך טפסים
              </div>
            )}
            {selectedClient && (
              <JustificationFormsPanel
                selectedClient={selectedClient}
                isPacketSignLoading={isPacketSignLoading}
                isDeletingClientExports={isDeletingClientExports}
                packetTrimInput={packetTrimInput}
                packetUploadFile={packetUploadFile}
                pdfGenerationMessage={pdfGenerationMessage}
                pdfGenerationIsError={pdfGenerationIsError}
                packetSignLink={packetSignLink}
                packetSignError={packetSignError}
                packetTrimStatus={packetTrimStatus}
                packetTrimIsError={packetTrimIsError}
                packetUploadStatus={packetUploadStatus}
                packetUploadIsError={packetUploadIsError}
                clientExportsStatus={clientExportsStatus}
                clientExportsIsError={clientExportsIsError}
                onGeneratePacketPdf={handleGeneratePacketPdf}
                onPreviewPacketPdf={handlePreviewPacketPdf}
                onCreatePacketSignLink={handleCreatePacketSignLink}
                onPreviewSignedPacketPdf={handlePreviewSignedPacketPdf}
                onPacketTrimInputChange={setPacketTrimInput}
                onTrimPacketPages={handleTrimPacketPages}
                onPacketUploadFileChange={handlePacketUploadFileChange}
                onUploadPacketPdf={handleUploadPacketPdf}
                onDeleteClientExports={handleDeleteClientExports}
              />
            )}
          </section>
        </div>
      </div>
    );
  }

  return (
    <div className="justification-page-wrapper">
      <JustificationTabs currentView={viewMode} onChangeView={setViewMode} />
      <div className="justification-page">
        <section className="just-panel just-middle">
          <h2 className="panel-title">
            תהליך הנמקה ללקוח
            {selectedClient ? ` - ${selectedClient.fullName}` : ""}
          </h2>
          <JustificationClientHeader
            clients={clients}
            selectedClientId={selectedClient ? selectedClient.id : null}
            clientFilter={clientFilter}
            selectedClientDetails={selectedClientDetails}
            onClientFilterChange={setClientFilter}
            onClientChange={(clientId) => {
              if (clientId == null) {
                setSelectedClient(null);
                return;
              }
              const client = clients.find((c) => c.id === clientId) || null;
              setSelectedClient(client);
            }}
          />
          {selectedClient && (
            <div className="just-report-actions">
              <button
                type="button"
                className="just-report-button"
                onClick={handleOpenAdviceHtml}
              >
               הפקת מסמך הנמקה
              </button>
              <button
                type="button"
                className="just-report-button"
                onClick={handleDownloadB1Pdf}
              >
               הפקת טופס ב1
              </button>
              <button
                type="button"
                className="just-report-button"
                onClick={handleGenerateAllKits}
              >
                הפקת קיט הצטרפות
              </button>
            </div>
          )}
          {pdfGenerationMessage && (
            <div
              className={
                pdfGenerationIsError ? "status-text status-error" : "status-text"
              }
            >
              {pdfGenerationMessage}
            </div>
          )}
          <JustificationExistingProductsSection
            existingProducts={existingProducts}
            selectedExistingProduct={selectedExistingProduct}
            loading={loading}
            selectedClient={selectedClient}
            existingFormMode={existingFormMode}
            createMode={createMode}
            replacementExistingId={replacementExistingId}
            savingProducts={savingProducts}
            selectedFundTypeFilter={selectedFundTypeFilter}
            savingProductSearch={savingProductSearch}
            selectedSavingProduct={selectedSavingProduct}
            newExistingPersonalNumber={newExistingPersonalNumber}
            newExistingAccumulatedAmount={newExistingAccumulatedAmount}
            newExistingManagementFeeBalance={newExistingManagementFeeBalance}
            newExistingManagementFeeContributions={newExistingManagementFeeContributions}
            newExistingEmploymentStatus={newExistingEmploymentStatus}
            newExistingHasRegularContributions={newExistingHasRegularContributions}
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
            replacementLockFundType={replacementLockFundType}
            onSetExistingFormMode={setExistingFormMode}
            onSetReplacementExistingId={setReplacementExistingId}
            onSetSelectedExistingProduct={setSelectedExistingProduct}
            onSetCreateMode={setCreateMode}
            onSetSelectedFundTypeFilter={setSelectedFundTypeFilter}
            onSetSelectedSavingProduct={setSelectedSavingProduct}
            onSetSavingProductSearch={setSavingProductSearch}
            onSetNewExistingPersonalNumber={setNewExistingPersonalNumber}
            onSetNewExistingAccumulatedAmount={setNewExistingAccumulatedAmount}
            onSetNewExistingManagementFeeBalance={
              setNewExistingManagementFeeBalance
            }
            onSetNewExistingManagementFeeContributions={
              setNewExistingManagementFeeContributions
            }
            onSetNewExistingEmploymentStatus={setNewExistingEmploymentStatus}
            onSetNewExistingHasRegularContributions={
              setNewExistingHasRegularContributions
            }
            onSetEditExistingPersonalNumber={setEditExistingPersonalNumber}
            onSetEditExistingAccumulatedAmount={setEditExistingAccumulatedAmount}
            onSetEditExistingManagementFeeBalance={setEditExistingManagementFeeBalance}
            onSetEditExistingManagementFeeContributions={
              setEditExistingManagementFeeContributions
            }
            onSetEditExistingEmploymentStatus={setEditExistingEmploymentStatus}
            onSetEditExistingHasRegularContributions={
              setEditExistingHasRegularContributions
            }
            onCreateExistingProduct={handleCreateExistingProduct}
            onCreateNewProduct={handleCreateNewProduct}
            onUpdateExistingProduct={handleUpdateExistingProduct}
            onDeleteExistingProduct={handleDeleteExistingProduct}
            findMatchingSavingProductForExisting={findMatchingSavingProductForExisting}
          />
          <JustificationNewProductsSection
            sortedNewProducts={sortedNewProducts}
            newProducts={newProducts}
            selectedNewProduct={selectedNewProduct}
            loading={loading}
            selectedClient={selectedClient}
            findExistingForNew={findExistingForNew}
            onSelectNewProduct={handleSelectNewProduct}
            onDownloadKitPdf={handleDownloadKitPdf}
            onDeleteNewProduct={handleDeleteNewProduct}
          />
      </section>
      </div>
    </div>
  );
}

export default JustificationPage;
