import { useEffect, useState, useRef, Fragment, ChangeEvent } from "react";
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
  buildAdviceHtmlUrl,
  buildAdvicePdfUrl,
  buildB1PdfUrl,
  buildKitPdfUrl,
  buildPacketPdfUrl,
  createPacketSignRequest,
  buildSignedClientPacketPdfUrl,
  trimPacketPdf,
} from "../api/justificationApi";
import { importGemelNetXml, clearJustificationData } from "../api/adminApi";
import { Client, ClientSummary, fetchClientSummaries, fetchClient } from "../api/crmApi";
import "../styles/justification.css";

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
  const [pdfPreviewUrl, setPdfPreviewUrl] = useState<string | null>(null);
  const [useAdobeViewer, setUseAdobeViewer] = useState(false);
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
  const [gemelFile, setGemelFile] = useState<File | null>(null);
  const [isGemelImporting, setIsGemelImporting] = useState(false);
  const [isJustificationClearing, setIsJustificationClearing] = useState(false);
  const [importStatus, setImportStatus] = useState<string | null>(null);
  const [importError, setImportError] = useState<string | null>(null);
  const [pdfGenerationMessage, setPdfGenerationMessage] = useState<string | null>(null);
  const [pdfGenerationIsError, setPdfGenerationIsError] = useState(false);
  const [packetSignLink, setPacketSignLink] = useState<string | null>(null);
  const [packetSignError, setPacketSignError] = useState<string | null>(null);
  const [isPacketSignLoading, setIsPacketSignLoading] = useState(false);
  const [packetTrimInput, setPacketTrimInput] = useState("");
  const [packetTrimStatus, setPacketTrimStatus] = useState<string | null>(null);
  const [packetTrimIsError, setPacketTrimIsError] = useState(false);
  const adobeViewRef = useRef<any | null>(null);

  useEffect(() => {
    if (typeof window === "undefined") {
      return;
    }
    const w: any = window;
    const onReady = () => {
      if (w.ADOBE_PDF_EMBED_API_KEY) {
        setUseAdobeViewer(true);
      }
    };

    if (w.AdobeDC) {
      onReady();
      return;
    }

    document.addEventListener("adobe_dc_view_sdk.ready", onReady);
    return () => {
      document.removeEventListener("adobe_dc_view_sdk.ready", onReady);
    };
  }, []);

  useEffect(() => {
    if (!useAdobeViewer || !pdfPreviewUrl) {
      return;
    }
    if (typeof window === "undefined") {
      return;
    }
    const w: any = window;
    if (!w.AdobeDC || !w.ADOBE_PDF_EMBED_API_KEY) {
      return;
    }
    if (pdfPreviewUrl.includes("/advice.html")) {
      return;
    }
    const viewerElement = document.getElementById("adobe-pdf-viewer");
    if (!viewerElement) {
      return;
    }

    const view = new w.AdobeDC.View({
      clientId: w.ADOBE_PDF_EMBED_API_KEY,
      divId: "adobe-pdf-viewer",
    });
    adobeViewRef.current = view;

    view.previewFile(
      {
        content: {
          location: {
            url: pdfPreviewUrl,
          },
        },
        metaData: {
          fileName: "טופס.pdf",
        },
      },
      {
        embedMode: "SIZED_CONTAINER",
        showDownloadPDF: true,
        showPrintPDF: true,
      }
    );
  }, [useAdobeViewer, pdfPreviewUrl]);

  const handleOpenAdviceHtml = async () => {
    if (!selectedClient) {
      return;
    }
    const pdfUrl = `${buildAdvicePdfUrl(selectedClient.id)}?generate=1`;

    try {
      const response = await fetch(pdfUrl);
      if (!response.ok) {
        throw new Error("advice-generate-failed");
      }
      setPdfGenerationIsError(false);
      setPdfGenerationMessage("מסמך ההנמקה הופק ונשמר בתיקיית הלקוח");
    } catch {
      setPdfGenerationIsError(true);
      setPdfGenerationMessage("שגיאה בהפקת מסמך ההנמקה");
    }
  };

  const handleDownloadB1Pdf = async () => {
    if (!selectedClient) {
      return;
    }
    const url = `${buildB1PdfUrl(selectedClient.id)}?generate=1`;
    try {
      const response = await fetch(url);
      if (!response.ok) {
        throw new Error("b1-generate-failed");
      }
      setPdfGenerationIsError(false);
      setPdfGenerationMessage("טופס B1 הופק ונשמר בתיקיית הלקוח");
    } catch {
      setPdfGenerationIsError(true);
      setPdfGenerationMessage("שגיאה בהפקת טופס B1");
    }
  };

  const handleGenerateKitPdf = async (product: NewProduct): Promise<void> => {
    if (!selectedClient) {
      return;
    }
    const url = `${buildKitPdfUrl(selectedClient.id, product.id)}?generate=1`;
    const response = await fetch(url);
    if (!response.ok) {
      throw new Error("kit-generate-failed");
    }
  };

  const handleDownloadKitPdf = (product: NewProduct) => {
    if (!selectedClient) {
      return;
    }
    const url = buildKitPdfUrl(selectedClient.id, product.id);
    window.open(url, "_blank");
  };

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

  const handleGemelFileChange = (event: ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0] ?? null;
    setGemelFile(file);
  };

  const handleRunGemelImport = () => {
    if (!gemelFile || isGemelImporting || isJustificationClearing) {
      return;
    }
    setIsGemelImporting(true);
    setImportStatus(null);
    setImportError(null);
    importGemelNetXml(gemelFile)
      .then((result) => {
        setImportStatus(
          `ייבוא גמל-נט (XML): נוספו ${result.createdSavingProducts} מוצרי חיסכון חדשים, עודכנו ${result.updatedSavingProducts}, מתוך ${result.rowsProcessed} רשומות (כפילויות שדולגו: ${result.duplicatesSkipped})`
        );
        setGemelFile(null);
        if (onGemelNetImportCompleted) {
          onGemelNetImportCompleted();
        }
      })
      .catch((error: any) => {
        const detail = error?.response?.data?.detail || error?.message;
        setImportError(detail || "שגיאה בייבוא קופות מגמל-נט");
      })
      .finally(() => {
        setIsGemelImporting(false);
      });
  };

  const handleClearJustificationData = () => {
    if (isGemelImporting || isJustificationClearing) {
      return;
    }
    // eslint-disable-next-line no-alert
    const confirmed = window.confirm(
      "האם אתה בטוח שברצונך למחוק את כל נתוני ההנמקה (מוצרי חיסכון, מוצרים קיימים/חדשים וטפסים)?"
    );
    if (!confirmed) {
      return;
    }

    setIsJustificationClearing(true);
    setImportStatus(null);
    setImportError(null);
    clearJustificationData()
      .then((result) => {
        setImportStatus(
          `נמחקו נתוני הנמקה: ${result.deletedSavingProducts} מוצרי חיסכון, ${result.deletedExistingProducts} מוצרים קיימים, ${result.deletedNewProducts} מוצרים חדשים ו-${result.deletedFormInstances} טפסים`
        );
      })
      .catch(() => {
        setImportError("שגיאה במחיקת נתוני הנמקה");
      })
      .finally(() => {
        setIsJustificationClearing(false);
      });
  };

  const handleGenerateAllKits = async () => {
    if (!selectedClient || newProducts.length === 0) {
      return;
    }

    const seenExisting = new Set<number>();
    const targets: NewProduct[] = [];

    [...newProducts].sort((a, b) => a.id - b.id).forEach((product) => {
      const existingId = product.existingProductId;
      if (existingId != null) {
        if (!seenExisting.has(existingId)) {
          seenExisting.add(existingId);
          targets.push(product);
        }
      } else {
        targets.push(product);
      }
    });

    if (targets.length === 0) {
      return;
    }

    try {
      await Promise.all(targets.map((product) => handleGenerateKitPdf(product)));
      setPdfGenerationIsError(false);
      setPdfGenerationMessage("קיטי ההצטרפות הופקו ונשמרו בתיקיית הלקוח");
    } catch {
      setPdfGenerationIsError(true);
      setPdfGenerationMessage("שגיאה בהפקת קיטי ההצטרפות");
    }
  };

  const handleGeneratePacketPdf = async () => {
    if (!selectedClient) {
      return;
    }
    const url = `${buildPacketPdfUrl(selectedClient.id)}?generate=1`;
    try {
      const response = await fetch(url);
      if (!response.ok) {
        throw new Error("packet-generate-failed");
      }
      setPdfGenerationIsError(false);
      setPdfGenerationMessage("חבילת הטפסים הופקה ונשמרה בתיקיית הלקוח");
    } catch {
      setPdfGenerationIsError(true);
      setPdfGenerationMessage("שגיאה בהפקת חבילת הטפסים");
    }
  };

  const handlePreviewPacketPdf = async () => {
    if (!selectedClient) {
      return;
    }
    const generateUrl = `${buildPacketPdfUrl(selectedClient.id)}?generate=1`;
    try {
      await fetch(generateUrl);
    } catch {
      // במקרה של שגיאה בהפקה, עדיין ננסה לפתוח את מה שקיים (אם קיים)
    }
    const url = buildPacketPdfUrl(selectedClient.id);
    window.open(url, "_blank");
  };

  const handlePreviewSignedPacketPdf = () => {
    if (!selectedClient) {
      return;
    }
    const url = buildSignedClientPacketPdfUrl(selectedClient.id);
    window.open(url, "_blank");
  };

  const handleTrimPacketPages = async () => {
    if (!selectedClient) {
      return;
    }
    const raw = packetTrimInput.trim();
    if (!raw) {
      return;
    }

    const parts = raw
      .split(/[ ,;]+/)
      .map((part) => part.trim())
      .filter((part) => part.length > 0);

    const pages: number[] = [];
    parts.forEach((part) => {
      const n = Number(part);
      if (Number.isFinite(n) && n >= 1) {
        pages.push(Math.floor(n));
      }
    });

    if (pages.length === 0) {
      setPacketTrimIsError(true);
      setPacketTrimStatus("לא הוזנו מספרי עמודים תקינים למחיקה");
      return;
    }

    try {
      await trimPacketPdf(selectedClient.id, pages);
      setPacketTrimIsError(false);
      setPacketTrimStatus(
        "החבילה נערכה: העמודים שביקשת נמחקו מהגרסה לעריכה. החתימה תיעשה על החבילה הערוכה."
      );
    } catch (error: any) {
      const detail = error?.response?.data?.detail || error?.message;
      setPacketTrimIsError(true);
      setPacketTrimStatus(detail || "שגיאה בעריכת חבילת הטפסים");
    }
  };

  const handleCreatePacketSignLink = async () => {
    if (!selectedClient) {
      return;
    }

    setIsPacketSignLoading(true);
    setPacketSignLink(null);
    setPacketSignError(null);

    try {
      const result = await createPacketSignRequest(selectedClient.id);
      const link = result.fullUrl || result.url;
      setPacketSignLink(link);
    } catch (error: any) {
      const detail = error?.response?.data?.detail || error?.message;
      setPacketSignError(detail || "שגיאה ביצירת קישור לחתימת הלקוח");
    } finally {
      setIsPacketSignLoading(false);
    }
  };

  const getNewProductReplacementLabel = (product: NewProduct): string => {
    if (product.existingProductId == null) {
      return "מוצר חדש ללא קופה קיימת";
    }
    const existing = existingProducts.find(
      (p) => p.id === product.existingProductId
    );
    if (!existing) {
      return "מוצר חדש (קופה חלופית - קופה קיימת לא נטענה)";
    }
    const personal = existing.personalNumber || "";
    if (personal) {
      return `מחליף קופה קיימת: ${existing.companyName || ""} - ${
        existing.fundName || ""
      } (מס' אישי ${personal})`;
    }
    return `מחליף קופה קיימת: ${existing.companyName || ""} - ${
      existing.fundName || ""
    }`;
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
    setPacketSignLink(null);
    setPacketSignError(null);
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
    if (!product) {
      return null;
    }
    const normalizeText = (value: string | null | undefined): string => {
      return (value ?? "").toLowerCase().replace(/\s+/g, " ").trim();
    };

    const normalizeName = (value: string | null | undefined): string => {
      const base = normalizeText(value);
      return base.replace(/["'`.,]/g, "").replace(/\s+/g, " ").trim();
    };

    const normalizeCode = (value: string | null | undefined): string => {
      return (value ?? "").toLowerCase().replace(/[\s-]/g, "");
    };

    const normalizeFundType = (value: string | null | undefined): string => {
      const base = normalizeText(value);
      if (!base) {
        return "";
      }

      // Map obvious synonyms to a canonical type for matching and locking
      if (base.includes("השתלמות")) {
        return "השתלמות";
      }

      return base;
    };

    const normalizeCompanyKey = (value: string | null | undefined): string => {
      const base = normalizeText(value);
      if (!base) {
        return "";
      }

      const parts = base.split(" ").filter(Boolean);
      if (parts.length === 0) {
        return "";
      }

      const significant = parts.find((p) => p.length >= 3) || parts[0];
      return significant;
    };

    const existingCompany = normalizeName(product.companyName);
    const existingCompanyKey = normalizeCompanyKey(product.companyName);
    const existingFundName = normalizeName(product.fundName);
    const existingFundCode = normalizeCode(product.fundCode);
    const existingFundType = normalizeFundType(product.fundType);

    let bestScore = 0;
    let bestProduct: SavingProduct | null = null;

    const splitToWords = (value: string): string[] => {
      return value
        .split(" ")
        .map((part) => part.trim())
        .filter((part) => part.length >= 2);
    };

    savingProducts.forEach((marketProduct) => {
      const marketCompany = normalizeName(marketProduct.companyName);
      const marketCompanyKey = normalizeCompanyKey(marketProduct.companyName);
      const marketFundName = normalizeName(marketProduct.fundName);
      const marketFundCode = normalizeCode(marketProduct.fundCode);
      const marketFundType = normalizeFundType(marketProduct.fundType);

      let score = 0;
      let codeScore = 0;

      if (existingFundCode && marketFundCode) {
        if (existingFundCode === marketFundCode) {
          codeScore += 80;
        } else if (
          existingFundCode.length >= 4 &&
          marketFundCode.length >= 4 &&
          (existingFundCode.includes(marketFundCode) ||
            marketFundCode.includes(existingFundCode))
        ) {
          codeScore += 50;
        }
      }

      score += codeScore;

      if (existingCompany && marketCompany) {
        if (existingCompany === marketCompany) {
          score += 30;
        } else if (
          existingCompany.length >= 4 &&
          marketCompany.length >= 4 &&
          (existingCompany.includes(marketCompany) ||
            marketCompany.includes(existingCompany))
        ) {
          score += 15;
        }
      }

      if (existingCompanyKey && marketCompanyKey && existingCompanyKey === marketCompanyKey) {
        score += 20;
      }

      if (existingFundName && marketFundName) {
        if (existingFundName === marketFundName) {
          score += 25;
        } else if (
          existingFundName.length >= 6 &&
          marketFundName.length >= 6 &&
          (existingFundName.includes(marketFundName) ||
            marketFundName.includes(existingFundName))
        ) {
          score += 10;
        }

        const existingWords = splitToWords(existingFundName);
        const marketWords = splitToWords(marketFundName);
        if (existingWords.length > 0 && marketWords.length > 0) {
          const existingSet = new Set(existingWords);
          let overlapCount = 0;
          marketWords.forEach((w) => {
            if (existingSet.has(w)) {
              overlapCount += 1;
            }
          });

          if (overlapCount >= 3) {
            score += 20;
          } else if (overlapCount === 2) {
            score += 12;
          } else if (overlapCount === 1) {
            score += 5;
          }
        }
      }

      if (existingFundType && marketFundType && existingFundType === marketFundType) {
        score += 10;
      }

      const candidateHasCodeMatch = codeScore > 0;
      const candidateMinScore = candidateHasCodeMatch ? 60 : 30;

      if (score >= candidateMinScore && score > bestScore) {
        bestScore = score;
        bestProduct = marketProduct;
      }
    });

    if (bestProduct) {
      return bestProduct;
    }

    return null;
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
        <div className="just-tabs">
          <button
            type="button"
            className="just-tab-button just-tab-button-active"
            onClick={() => setViewMode("market")}
          >
            דשבורד
          </button>
          <button
            type="button"
            className="just-tab-button"
            onClick={() => setViewMode("client")}
          >
            הנמקה ללקוח
          </button>
          <button
            type="button"
            className="just-tab-button"
            onClick={() => setViewMode("forms")}
          >
            עריכת טפסים
          </button>
        </div>
        <div className="justification-page">
          <section className="just-panel">
            <h2 className="panel-title">דשבורד הנמקה</h2>
            {importStatus && (
              <div className="admin-import-status">{importStatus}</div>
            )}
            {importError && (
              <div className="admin-import-status admin-import-status-error">
                {importError}
              </div>
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
                  onChange={handleGemelFileChange}
                />
                <button
                  type="button"
                  className="admin-import-button"
                  onClick={handleRunGemelImport}
                  disabled={!gemelFile || isGemelImporting || isJustificationClearing}
                >
                  ייבוא גמל-נט (XML)
                </button>
                <button
                  type="button"
                  className="admin-import-button"
                  onClick={handleClearJustificationData}
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
                </tr>
              </thead>
              <tbody>
                {savingProducts.map((product) => (
                  <tr
                    key={product.id}
                    className={
                      selectedSavingProduct &&
                      selectedSavingProduct.id === product.id
                        ? "saving-row saving-row-selected"
                        : "saving-row"
                    }
                    onClick={() => setSelectedSavingProduct(product)}
                  >
                    <td>{product.companyName}</td>
                    <td>{product.fundName}</td>
                    <td>{product.fundType}</td>
                    <td>{product.fundCode}</td>
                    <td>{product.yield1yr ?? "-"}</td>
                    <td>{product.yield3yr ?? "-"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </section>
        </div>
      </div>
    );
  }

  if (viewMode === "forms") {
    return (
      <div className="justification-page-wrapper">
        <div className="just-tabs">
          <button
            type="button"
            className="just-tab-button"
            onClick={() => setViewMode("market")}
          >
            דשבורד
          </button>
          <button
            type="button"
            className="just-tab-button"
            onClick={() => setViewMode("client")}
          >
            הנמקה ללקוח
          </button>
          <button
            type="button"
            className="just-tab-button just-tab-button-active"
            onClick={() => setViewMode("forms")}
          >
            עריכת טפסים
          </button>
        </div>
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
              <section className="client-pdf-section">
                <h3 className="panel-subtitle">חבילת טפסי PDF ללקוח</h3>
                <div className="client-pdf-layout">
                  <ul className="client-pdf-list">
                    <li className="client-pdf-item">
                      <div className="client-pdf-item-main">
                        <span className="client-pdf-title">חבילת טפסים מאוחדת</span>
                        <span className="client-pdf-meta">
                          החבילה כוללת: מסמך הנמקה, טופס B1 וכל קיטי ההצטרפות שנוצרו ללקוח
                        </span>
                      </div>
                      <div className="client-pdf-actions">
                        <button
                          type="button"
                          className="client-pdf-button"
                          onClick={handleGeneratePacketPdf}
                        >
                          הפקת חבילת טפסים
                        </button>
                        <button
                          type="button"
                          className="client-pdf-button"
                          onClick={handlePreviewPacketPdf}
                        >
                          תצוגה בעמוד
                        </button>
                        <button
                          type="button"
                          className="client-pdf-button"
                          onClick={handleCreatePacketSignLink}
                          disabled={isPacketSignLoading}
                        >
                          שלח ללקוח לחתימה
                        </button>
                        <button
                          type="button"
                          className="client-pdf-button"
                          onClick={handlePreviewSignedPacketPdf}
                        >
                          צפייה בחבילה החתומה
                        </button>
                        <div className="client-pdf-trim">
                          <span>מחק עמודים (לפי מספר):</span>
                          <input
                            type="text"
                            className="client-pdf-input"
                            value={packetTrimInput}
                            onChange={(event) => setPacketTrimInput(event.target.value)}
                            placeholder="לדוגמה: 2 5 7"
                          />
                          <button
                            type="button"
                            className="client-pdf-button"
                            onClick={handleTrimPacketPages}
                          >
                            מחק עמודים מהחבילה
                          </button>
                        </div>
                      </div>
                    </li>
                  </ul>
                </div>
                {pdfGenerationMessage && (
                  <div
                    className={
                      pdfGenerationIsError ? "status-text status-error" : "status-text"
                    }
                  >
                    {pdfGenerationMessage}
                  </div>
                )}
                {packetSignLink && (
                  <div className="status-text">
                    ניתן לשלוח ללקוח את הקישור הבא לחתימה:
                    <br />
                    <a href={packetSignLink} target="_blank" rel="noreferrer">
                      {packetSignLink}
                    </a>
                  </div>
                )}
                {packetTrimStatus && (
                  <div
                    className={
                      packetTrimIsError ? "status-text status-error" : "status-text"
                    }
                  >
                    {packetTrimStatus}
                  </div>
                )}
                {packetSignError && (
                  <div className="status-text status-error">{packetSignError}</div>
                )}
              </section>
            )}
          </section>
        </div>
      </div>
    );
  }

  return (
    <div className="justification-page-wrapper">
      <div className="just-tabs">
        <button
          type="button"
          className="just-tab-button"
          onClick={() => setViewMode("market")}
        >
          דשבורד
        </button>
        <button
          type="button"
          className="just-tab-button just-tab-button-active"
          onClick={() => setViewMode("client")}
        >
          הנמקה ללקוח
        </button>
        <button
          type="button"
          className="just-tab-button"
          onClick={() => setViewMode("forms")}
        >
          עריכת טפסים
        </button>
      </div>
      <div className="justification-page">
        <section className="just-panel just-middle">
          <h2 className="panel-title">
            תהליך הנמקה ללקוח
            {selectedClient ? ` - ${selectedClient.fullName}` : ""}
          </h2>
          <div className="just-client-search">
            <input
              type="text"
              className="just-client-search-input"
              placeholder="חיפוש לקוח לפי שם או תעודת זהות"
              value={clientFilter}
              onChange={(event) => setClientFilter(event.target.value)}
            />
          </div>
          <div className="just-client-selector">
            <span className="just-client-label">בחר לקוח:</span>
            <select
              className="just-client-select"
              value={selectedClient ? selectedClient.id : ""}
              onChange={(event) => {
                const value = event.target.value;
                if (!value) {
                  setSelectedClient(null);
                  return;
                }
                const id = Number(value);
                const client = clients.find((c) => c.id === id) || null;
                setSelectedClient(client);
              }}
            >
              {clients
                .filter((client) => {
                  const term = clientFilter.trim();
                  if (!term) {
                    return true;
                  }
                  return (
                    client.fullName.includes(term) ||
                    client.idNumber.includes(term)
                  );
                })
                .map((client) => (
                <option key={client.id} value={client.id}>
                  {client.fullName} ({client.idNumber})
                </option>
              ))}
              {clients.length === 0 && (
                <option value="">אין לקוחות זמינים</option>
              )}
            </select>
          </div>
          
          {selectedClientDetails && (
            <div className="just-client-details">
              <div className="just-client-details-row">
                <span className="just-client-details-label">שם מלא:</span>
                <span className="just-client-details-value">
                  {selectedClientDetails.fullName}
                </span>
              </div>
              <div className="just-client-details-row">
                <span className="just-client-details-label">ת.ז:</span>
                <span className="just-client-details-value">
                  {selectedClientDetails.idNumber}
                </span>
              </div>
              <div className="just-client-details-row">
                <span className="just-client-details-label">תאריך לידה:</span>
                <span className="just-client-details-value">
                  {selectedClientDetails.birthDate || "-"}
                </span>
              </div>
              <div className="just-client-details-row">
                <span className="just-client-details-label">מין:</span>
                <span className="just-client-details-value">
                  {selectedClientDetails.gender || "-"}
                </span>
              </div>
              <div className="just-client-details-row">
                <span className="just-client-details-label">סטטוס:</span>
                <span className="just-client-details-value">
                  {selectedClientDetails.maritalStatus || "-"}
                </span>
              </div>
              <div className="just-client-details-row">
                <span className="just-client-details-label">ארץ לידה:</span>
                <span className="just-client-details-value">
                  {selectedClientDetails.birthCountry || "-"}
                </span>
              </div>
              <div className="just-client-details-row">
                <span className="just-client-details-label">טלפון:</span>
                <span className="just-client-details-value">
                  {selectedClientDetails.phone || "-"}
                </span>
              </div>
              <div className="just-client-details-row">
                <span className="just-client-details-label">אימייל:</span>
                <span className="just-client-details-value">
                  {selectedClientDetails.email || "-"}
                </span>
              </div>
              <div className="just-client-details-row">
                <span className="just-client-details-label">כתובת:</span>
                <span className="just-client-details-value">
                  {[
                    selectedClientDetails.addressCity,
                    [
                      selectedClientDetails.addressStreet,
                      selectedClientDetails.addressHouseNumber,
                    ]
                      .filter(Boolean)
                      .join(" "),
                    selectedClientDetails.addressApartment
                      ? `דירה ${selectedClientDetails.addressApartment}`
                      : null,
                    selectedClientDetails.addressPostalCode,
                  ]
                    .filter(Boolean)
                    .join(", ") || "-"}
                </span>
              </div>
              <div className="just-client-details-row">
                <span className="just-client-details-label">מעסיק:</span>
                <span className="just-client-details-value">
                  {selectedClientDetails.employerName || "-"}
                </span>
              </div>
              <div className="just-client-details-row">
                <span className="just-client-details-label">ח"פ מעסיק:</span>
                <span className="just-client-details-value">
                  {selectedClientDetails.employerHp || "-"}
                </span>
              </div>
              <div className="just-client-details-row">
                <span className="just-client-details-label">טלפון מעסיק:</span>
                <span className="just-client-details-value">
                  {selectedClientDetails.employerPhone || "-"}
                </span>
              </div>
              <div className="just-client-details-row">
                <span className="just-client-details-label">כתובת מעסיק:</span>
                <span className="just-client-details-value">
                  {selectedClientDetails.employerAddress || "-"}
                </span>
              </div>
          </div>
        )}
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
          <div className={pdfGenerationIsError ? "status-text status-error" : "status-text"}>
            {pdfGenerationMessage}
          </div>
        )}
        <div className="existing-products-section">
          <div className="existing-products-header">
            <h3 className="panel-subtitle">מוצרים קיימים ללקוח</h3>
            <div className="existing-products-actions">
              <button
                type="button"
                className="existing-row-action-button"
                onClick={() => {
                  setExistingFormMode("create");
                  setReplacementExistingId(null);
                  setSelectedExistingProduct(null);
                  setCreateMode("existing");
                }}
              >
                צור קופה קיימת
              </button>
              <button
                type="button"
                className="existing-row-action-button"
                disabled={!selectedClient}
                onClick={() => {
                  setExistingFormMode("create");
                  setReplacementExistingId(null);
                  setCreateMode("new");
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
                const matchingSavingProduct = findMatchingSavingProductForExisting(
                  product
                );
                const hasCompleteCoreData =
                  !!product.personalNumber &&
                  !!matchingSavingProduct;

                return (
                  <tr
                    key={product.id}
                    className={
                      selectedExistingProduct && selectedExistingProduct.id === product.id
                        ? "existing-row existing-row-selected"
                        : "existing-row"
                    }
                    onClick={() => {
                      setSelectedExistingProduct(product);
                      setExistingFormMode("edit");
                      setReplacementExistingId(null);
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
                          setSelectedExistingProduct(product);
                          setExistingFormMode("edit");
                          setReplacementExistingId(null);
                          setCreateMode("existing");
                          const match = findMatchingSavingProductForExisting(product);
                          if (match) {
                            setSelectedFundTypeFilter(match.fundType);
                            setSelectedSavingProduct(match);
                          } else {
                            setSelectedSavingProduct(null);
                          }
                          setSavingProductSearch("");
                        }}
                      >
                        עריכה
                      </button>
                      <button
                        type="button"
                        className="existing-row-action-button"
                        onClick={(event) => {
                          event.stopPropagation();
                          setSelectedExistingProduct(product);
                          handleDeleteExistingProduct();
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
                          setSelectedExistingProduct(product);
                          setReplacementExistingId(product.id);
                          const match = findMatchingSavingProductForExisting(product);
                          if (match) {
                            setSelectedFundTypeFilter(match.fundType);
                            setSelectedSavingProduct(match);
                          } else {
                            if (product.fundType) {
                              setSelectedFundTypeFilter(product.fundType);
                            }
                            setSelectedSavingProduct(null);
                          }
                          const accValue =
                            product.accumulatedAmount != null
                              ? String(product.accumulatedAmount)
                              : "";
                          setNewExistingAccumulatedAmount(accValue);
                          setNewExistingEmploymentStatus(product.employmentStatus || "");
                          setNewExistingHasRegularContributions(
                            product.hasRegularContributions === true
                              ? "yes"
                              : product.hasRegularContributions === false
                              ? "no"
                              : ""
                          );
                          setSavingProductSearch("");
                          setExistingFormMode("create");
                          setCreateMode("new");
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
          {existingFormMode !== "none" && (
          <div className="existing-edit-panel">
            {existingFormMode === "create" && (
              <div className="existing-edit-group">
                <div className="existing-edit-title">
                  {createMode === "existing"
                    ? "הוספת קופה קיימת ידנית"
                    : replacementExistingId
                    ? "יצירת קופה חלופית"
                    : "צור קופה חדשה"}
                </div>
                {savingProducts.length > 0 && (
                  <div className="just-saving-filter">
                    <div className="just-saving-filter-header">
                      <span className="just-saving-filter-title">בחירת סוג מוצר וקופה מהשוק</span>
                      <span className="just-saving-filter-hint">
                        בחר סוג קופה, ולאחר מכן קופה מהרשימה. הנתונים של החברה, שם הקופה, סוג
                        וקוד ייקבעו אוטומטית.
                      </span>
                    </div>
                    <div className="just-saving-type-radios">
                      {Array.from(new Set(savingProducts.map((product) => product.fundType))).map(
                        (type) => (
                          <label key={type} className="just-saving-type-option">
                            <input
                              type="radio"
                              name="saving-fund-type"
                              value={type}
                              checked={selectedFundTypeFilter === type}
                              onChange={(event) => setSelectedFundTypeFilter(event.target.value)}
                              disabled={
                                !!replacementLockFundType && replacementLockFundType !== type
                              }
                            />
                            <span>{type}</span>
                          </label>
                        )
                      )}
                    </div>
                    {selectedFundTypeFilter && (
                      <div className="just-saving-filter-table-wrapper">
                        <input
                          className="existing-edit-input"
                          placeholder="חיפוש קופה לפי שם / חברה / קוד"
                          value={savingProductSearch}
                          onChange={(event) => setSavingProductSearch(event.target.value)}
                        />
                        <select
                          className="just-saving-select"
                          value={
                            selectedSavingProduct &&
                            selectedSavingProduct.fundType === selectedFundTypeFilter
                              ? String(selectedSavingProduct.id)
                              : ""
                          }
                          onChange={(event) => {
                            const value = event.target.value;
                            if (!value) {
                              setSelectedSavingProduct(null);
                              return;
                            }
                            const id = Number(value);
                            const product =
                              savingProducts.find(
                                (p) =>
                                  p.id === id && p.fundType === selectedFundTypeFilter
                              ) || null;
                            setSelectedSavingProduct(product);
                          }}
                        >
                          <option value="">בחר קופה מהרשימה</option>
                          {savingProducts
                            .filter((product) => product.fundType === selectedFundTypeFilter)
                            .filter((product) => {
                              const term = savingProductSearch.trim().toLowerCase();
                              if (!term) {
                                return true;
                              }
                              const company = (product.companyName || "").toLowerCase();
                              const name = (product.fundName || "").toLowerCase();
                              const code = (product.fundCode || "").toLowerCase();
                              return (
                                company.includes(term) ||
                                name.includes(term) ||
                                code.includes(term)
                              );
                            })
                            .map((product) => (
                              <option key={product.id} value={String(product.id)}>
                                {product.companyName} - {product.fundName} ({product.fundCode})
                              </option>
                            ))}
                        </select>
                      </div>
                    )}
                  </div>
                )}
                <div className="status-text">
                  בחר קודם קופה מטבלת הקופות מעל. שדות החברה/שם/סוג/קוד ייקבעו אוטומטית.
                </div>
                <div className="existing-edit-row">
                  <label className="existing-edit-label">חברה</label>
                  <div className="existing-edit-value">
                    {selectedSavingProduct ? selectedSavingProduct.companyName : "לא נבחרה קופה"}
                  </div>
                </div>
                <div className="existing-edit-row">
                  <label className="existing-edit-label">שם קופה</label>
                  <div className="existing-edit-value">
                    {selectedSavingProduct ? selectedSavingProduct.fundName : ""}
                  </div>
                </div>
                <div className="existing-edit-row">
                  <label className="existing-edit-label">סוג קופה</label>
                  <div className="existing-edit-value">
                    {selectedSavingProduct ? selectedSavingProduct.fundType : ""}
                  </div>
                </div>
                <div className="existing-edit-row">
                  <label className="existing-edit-label">קוד קופה</label>
                  <div className="existing-edit-value">
                    {selectedSavingProduct ? selectedSavingProduct.fundCode : ""}
                  </div>
                </div>
                <div className="existing-edit-row">
                  <label className="existing-edit-label">מס' אישי</label>
                  <input
                    className="existing-edit-input"
                    value={newExistingPersonalNumber}
                    onChange={(event) => setNewExistingPersonalNumber(event.target.value)}
                  />
                </div>
                <div className="existing-edit-row">
                  <label className="existing-edit-label">יתרה</label>
                  <input
                    className="existing-edit-input"
                    value={newExistingAccumulatedAmount}
                    onChange={(event) => setNewExistingAccumulatedAmount(event.target.value)}
                  />
                </div>
                <div className="existing-edit-row">
                  <label className="existing-edit-label">דמי ניהול מצבירה</label>
                  <input
                    className="existing-edit-input"
                    value={newExistingManagementFeeBalance}
                    onChange={(event) => setNewExistingManagementFeeBalance(event.target.value)}
                  />
                </div>
                <div className="existing-edit-row">
                  <label className="existing-edit-label">דמי ניהול מהפקדה</label>
                  <input
                    className="existing-edit-input"
                    value={newExistingManagementFeeContributions}
                    onChange={(event) =>
                      setNewExistingManagementFeeContributions(event.target.value)
                    }
                  />
                </div>
                <div className="existing-edit-row">
                  <label className="existing-edit-label">מעמד</label>
                  <div className="existing-edit-radio-group">
                    <label className="existing-edit-radio-option">
                      <input
                        type="radio"
                        name="new-existing-employment"
                        value="שכיר"
                        checked={newExistingEmploymentStatus === "שכיר"}
                        onChange={(event) => setNewExistingEmploymentStatus(event.target.value)}
                      />
                      <span>שכיר</span>
                    </label>
                    <label className="existing-edit-radio-option">
                      <input
                        type="radio"
                        name="new-existing-employment"
                        value="עצמאי"
                        checked={newExistingEmploymentStatus === "עצמאי"}
                        onChange={(event) => setNewExistingEmploymentStatus(event.target.value)}
                      />
                      <span>עצמאי</span>
                    </label>
                  </div>
                </div>
                <div className="existing-edit-row">
                  <label className="existing-edit-label">האם יש הפקדות שוטפות</label>
                  <div className="existing-edit-radio-group">
                    <label className="existing-edit-radio-option">
                      <input
                        type="radio"
                        name="new-existing-regular"
                        value="yes"
                        checked={newExistingHasRegularContributions === "yes"}
                        onChange={(event) => setNewExistingHasRegularContributions(event.target.value)}
                      />
                      <span>כן</span>
                    </label>
                    <label className="existing-edit-radio-option">
                      <input
                        type="radio"
                        name="new-existing-regular"
                        value="no"
                        checked={newExistingHasRegularContributions === "no"}
                        onChange={(event) => setNewExistingHasRegularContributions(event.target.value)}
                      />
                      <span>לא</span>
                    </label>
                  </div>
                </div>
                <div className="existing-edit-actions">
                  <button
                    type="button"
                    className="existing-edit-save-button"
                    disabled={
                      !selectedClient ||
                      !selectedSavingProduct ||
                      (createMode === "existing" && !newExistingPersonalNumber.trim())
                    }
                    onClick={() => {
                      if (createMode === "existing") {
                        handleCreateExistingProduct();
                      } else {
                        const existingId = replacementExistingId ?? null;
                        handleCreateNewProduct(existingId);
                      }
                    }}
                  >
                    {createMode === "existing"
                      ? "הוסף קופה קיימת"
                      : replacementExistingId
                      ? "צור קופה חלופית"
                      : "צור קופה חדשה"}
                  </button>
                </div>
              </div>
            )}
            {existingFormMode === "edit" && (
              <div className="existing-edit-group">
                <div className="existing-edit-title">עריכה / מחיקה של קופה קיימת</div>
                {!selectedExistingProduct && (
                  <div className="status-text">בחר קופה קיימת מתוך הטבלה לעריכה</div>
                )}
                {selectedExistingProduct && selectedExistingProduct.isVirtual && (
                  <div className="status-text">
                    קופה זו נוצרה אוטומטית מנתוני ה‑CRM. ניתן לערוך את הנתונים כדי
                    להתאים לקופה בשוק.
                  </div>
                )}
                {selectedExistingProduct && (
                  <>
                    {savingProducts.length > 0 && (
                      <div className="just-saving-filter">
                        <div className="just-saving-filter-header">
                          <span className="just-saving-filter-title">
                            בחירת סוג מוצר וקופה מהשוק
                          </span>
                          <span className="just-saving-filter-hint">
                            בחר סוג קופה, ולאחר מכן קופה מהרשימה. הנתונים של החברה, שם הקופה,
                            סוג וקוד ייקבעו אוטומטית.
                          </span>
                        </div>
                        <div className="just-saving-type-radios">
                          {Array.from(
                            new Set(savingProducts.map((product) => product.fundType))
                          ).map((type) => (
                            <label key={type} className="just-saving-type-option">
                              <input
                                type="radio"
                                name="saving-fund-type-edit"
                                value={type}
                                checked={selectedFundTypeFilter === type}
                                onChange={(event) => setSelectedFundTypeFilter(event.target.value)}
                              />
                              <span>{type}</span>
                            </label>
                          ))}
                        </div>
                        {selectedFundTypeFilter && (
                          <div className="just-saving-filter-table-wrapper">
                            <input
                              className="existing-edit-input"
                              placeholder="חיפוש קופה לפי שם / חברה / קוד"
                              value={savingProductSearch}
                              onChange={(event) => setSavingProductSearch(event.target.value)}
                            />
                            <select
                              className="just-saving-select"
                              value={
                                selectedSavingProduct &&
                                selectedSavingProduct.fundType === selectedFundTypeFilter
                                  ? String(selectedSavingProduct.id)
                                  : ""
                              }
                              onChange={(event) => {
                                const value = event.target.value;
                                if (!value) {
                                  setSelectedSavingProduct(null);
                                  return;
                                }
                                const id = Number(value);
                                const product =
                                  savingProducts.find(
                                    (p) =>
                                      p.id === id && p.fundType === selectedFundTypeFilter
                                  ) || null;
                                setSelectedSavingProduct(product);
                              }}
                            >
                              <option value="">בחר קופה מהרשימה</option>
                              {savingProducts
                                .filter((product) => product.fundType === selectedFundTypeFilter)
                                .filter((product) => {
                                  const term = savingProductSearch.trim().toLowerCase();
                                  if (!term) {
                                    return true;
                                  }
                                  const company = (product.companyName || "").toLowerCase();
                                  const name = (product.fundName || "").toLowerCase();
                                  const code = (product.fundCode || "").toLowerCase();
                                  return (
                                    company.includes(term) ||
                                    name.includes(term) ||
                                    code.includes(term)
                                  );
                                })
                                .map((product) => (
                                  <option key={product.id} value={String(product.id)}>
                                    {product.companyName} - {product.fundName} ({product.fundCode})
                                  </option>
                                ))}
                            </select>
                          </div>
                        )}
                      </div>
                    )}
                    <div className="existing-edit-row">
                      <label className="existing-edit-label">חברה</label>
                      <div className="existing-edit-value">
                        {selectedSavingProduct
                          ? selectedSavingProduct.companyName
                          : selectedExistingProduct.companyName}
                      </div>
                    </div>
                    <div className="existing-edit-row">
                      <label className="existing-edit-label">שם קופה</label>
                      <div className="existing-edit-value">
                        {selectedSavingProduct
                          ? selectedSavingProduct.fundName
                          : selectedExistingProduct.fundName}
                      </div>
                    </div>
                    <div className="existing-edit-row">
                      <label className="existing-edit-label">סוג קופה</label>
                      <div className="existing-edit-value">
                        {selectedSavingProduct
                          ? selectedSavingProduct.fundType
                          : selectedExistingProduct.fundType}
                      </div>
                    </div>
                    <div className="existing-edit-row">
                      <label className="existing-edit-label">קוד קופה</label>
                      <div className="existing-edit-value">
                        {selectedSavingProduct
                          ? selectedSavingProduct.fundCode
                          : selectedExistingProduct.fundCode}
                      </div>
                    </div>
                    <div className="existing-edit-row">
                      <label className="existing-edit-label">מס' אישי</label>
                      <input
                        className="existing-edit-input"
                        value={editExistingPersonalNumber}
                        onChange={(event) => setEditExistingPersonalNumber(event.target.value)}
                      />
                    </div>
                    <div className="existing-edit-row">
                      <label className="existing-edit-label">יתרה</label>
                      <input
                        className="existing-edit-input"
                        value={editExistingAccumulatedAmount}
                        onChange={(event) => setEditExistingAccumulatedAmount(event.target.value)}
                      />
                    </div>
                    <div className="existing-edit-row">
                      <label className="existing-edit-label">דמי ניהול מצבירה</label>
                      <input
                        className="existing-edit-input"
                        value={editExistingManagementFeeBalance}
                        onChange={(event) => setEditExistingManagementFeeBalance(event.target.value)}
                      />
                    </div>
                    <div className="existing-edit-row">
                      <label className="existing-edit-label">דמי ניהול מהפקדה</label>
                      <input
                        className="existing-edit-input"
                        value={editExistingManagementFeeContributions}
                        onChange={(event) =>
                          setEditExistingManagementFeeContributions(event.target.value)
                        }
                      />
                    </div>
                    <div className="existing-edit-row">
                      <label className="existing-edit-label">מעמד</label>
                      <div className="existing-edit-radio-group">
                        <label className="existing-edit-radio-option">
                          <input
                            type="radio"
                            name="edit-existing-employment"
                            value="שכיר"
                            checked={editExistingEmploymentStatus === "שכיר"}
                            onChange={(event) =>
                              setEditExistingEmploymentStatus(event.target.value)
                            }
                          />
                          <span>שכיר</span>
                        </label>
                        <label className="existing-edit-radio-option">
                          <input
                            type="radio"
                            name="edit-existing-employment"
                            value="עצמאי"
                            checked={editExistingEmploymentStatus === "עצמאי"}
                            onChange={(event) =>
                              setEditExistingEmploymentStatus(event.target.value)
                            }
                          />
                          <span>עצמאי</span>
                        </label>
                      </div>
                    </div>
                    <div className="existing-edit-row">
                      <label className="existing-edit-label">האם יש הפקדות שוטפות</label>
                      <div className="existing-edit-radio-group">
                        <label className="existing-edit-radio-option">
                          <input
                            type="radio"
                            name="edit-existing-regular"
                            value="yes"
                            checked={editExistingHasRegularContributions === "yes"}
                            onChange={(event) =>
                              setEditExistingHasRegularContributions(event.target.value)
                            }
                          />
                          <span>כן</span>
                        </label>
                        <label className="existing-edit-radio-option">
                          <input
                            type="radio"
                            name="edit-existing-regular"
                            value="no"
                            checked={editExistingHasRegularContributions === "no"}
                            onChange={(event) =>
                              setEditExistingHasRegularContributions(event.target.value)
                            }
                          />
                          <span>לא</span>
                        </label>
                      </div>
                    </div>
                    <div className="existing-edit-actions">
                      <button
                        type="button"
                        className="existing-edit-save-button"
                        onClick={handleUpdateExistingProduct}
                      >
                        שמור שינויים
                      </button>
                      <button
                        type="button"
                        className="existing-edit-delete-button"
                        onClick={handleDeleteExistingProduct}
                      >
                        מחיקת קופה
                      </button>
                    </div>
                  </>
                )}
              </div>
            )}
          </div>
          )}
        </div>
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
                    onClick={() => handleSelectNewProduct(product)}
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
                          handleDownloadKitPdf(product);
                        }}
                      >
                        הורדת קיט
                      </button>
                      <button
                        type="button"
                        className="new-product-delete-button"
                        onClick={(event) => {
                          event.stopPropagation();
                          handleDeleteNewProduct(product.id);
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
      </section>
      </div>
    </div>
  );
}

export default JustificationPage;
