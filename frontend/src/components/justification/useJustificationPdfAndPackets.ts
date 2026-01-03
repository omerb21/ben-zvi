import { useEffect, useState, ChangeEvent } from "react";
import type { NewProduct } from "../../api/justificationApi";
import httpClient from "../../api/httpClient";
import {
  buildAdvicePdfUrl,
  buildB1PdfUrl,
  buildKitPdfUrl,
  buildPacketPdfUrl,
  buildSignedClientPacketPdfUrl,
  createPacketSignRequest,
  uploadPacketPdf,
  trimPacketPdf,
  deleteClientExports,
} from "../../api/justificationApi";
import type { ClientSummary } from "../../api/crmApi";

export type JustificationPdfAndPacketsState = {
  pdfGenerationMessage: string | null;
  pdfGenerationIsError: boolean;
  packetSignLink: string | null;
  packetSignError: string | null;
  isPacketSignLoading: boolean;
  packetTrimInput: string;
  packetTrimStatus: string | null;
  packetTrimIsError: boolean;
  packetUploadFile: File | null;
  packetUploadStatus: string | null;
  packetUploadIsError: boolean;
  clientExportsStatus: string | null;
  clientExportsIsError: boolean;
  isDeletingClientExports: boolean;
  handleOpenAdviceHtml: () => Promise<void>;
  handleDownloadB1Pdf: () => Promise<void>;
  handleGenerateAllKits: () => Promise<void>;
  handleDownloadKitPdf: (product: NewProduct) => void;
  handleGeneratePacketPdf: () => Promise<void>;
  handlePreviewPacketPdf: () => Promise<void>;
  handlePreviewSignedPacketPdf: () => void;
  handleCreatePacketSignLink: () => Promise<void>;
  handleTrimPacketPages: () => Promise<void>;
  handlePacketUploadFileChange: (event: ChangeEvent<HTMLInputElement>) => void;
  handleUploadPacketPdf: () => Promise<void>;
  handleDeleteClientExports: () => Promise<void>;
  setPacketTrimInput: (value: string) => void;
};

export function useJustificationPdfAndPackets(
  selectedClient: ClientSummary | null,
  newProducts: NewProduct[]
): JustificationPdfAndPacketsState {
  const [pdfGenerationMessage, setPdfGenerationMessage] = useState<string | null>(null);
  const [pdfGenerationIsError, setPdfGenerationIsError] = useState(false);
  const [packetSignLink, setPacketSignLink] = useState<string | null>(null);
  const [packetSignError, setPacketSignError] = useState<string | null>(null);
  const [isPacketSignLoading, setIsPacketSignLoading] = useState(false);
  const [packetTrimInput, setPacketTrimInput] = useState("");
  const [packetTrimStatus, setPacketTrimStatus] = useState<string | null>(null);
  const [packetTrimIsError, setPacketTrimIsError] = useState(false);
  const [packetUploadFile, setPacketUploadFile] = useState<File | null>(null);
  const [packetUploadStatus, setPacketUploadStatus] = useState<string | null>(null);
  const [packetUploadIsError, setPacketUploadIsError] = useState(false);
  const [clientExportsStatus, setClientExportsStatus] = useState<string | null>(null);
  const [clientExportsIsError, setClientExportsIsError] = useState(false);
  const [isDeletingClientExports, setIsDeletingClientExports] = useState(false);

  const fetchPdfBlob = async (url: string) => {
    return httpClient.get<Blob>(url, {
      responseType: "blob",
      validateStatus: () => true,
    });
  };

  const extractErrorDetail = async (blob: Blob): Promise<string | null> => {
    try {
      const text = await blob.text();
      if (!text) {
        return null;
      }
      try {
        const parsed = JSON.parse(text);
        const detail = (parsed as any)?.detail;
        if (typeof detail === "string" && detail.trim()) {
          return detail;
        }
      } catch {
        // not json
      }
      return text;
    } catch {
      return null;
    }
  };

  const buildPdfErrorMessage = (status: number, detail?: string | null) => {
    if (status === 503 && detail === "wkhtmltopdf not found") {
      return "לא ניתן להפיק PDF: wkhtmltopdf לא מותקן/לא נמצא במחשב (Service Unavailable)";
    }
    return "שגיאה בהפקת PDF";
  };

  const triggerPdfDownloadFromBlob = async (blob: Blob) => {
    const objectUrl = URL.createObjectURL(blob);
    try {
      const link = document.createElement("a");
      link.href = objectUrl;
      link.target = "_blank";
      link.rel = "noopener noreferrer";
      link.download = "";
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    } finally {
      URL.revokeObjectURL(objectUrl);
    }
  };

  const openPdfTabFromBlob = async (blob: Blob) => {
    const objectUrl = URL.createObjectURL(blob);
    try {
      window.open(objectUrl, "_blank");
    } finally {
      // ניתן לשחרר את ה-URL לאחר פתיחת הלשונית
      setTimeout(() => {
        URL.revokeObjectURL(objectUrl);
      }, 10000);
    }
  };

  useEffect(() => {
    setPacketSignLink(null);
    setPacketSignError(null);
    setPacketTrimInput("");
    setPacketTrimStatus(null);
    setPacketTrimIsError(false);
    setPacketUploadFile(null);
    setPacketUploadStatus(null);
    setPacketUploadIsError(false);
    setClientExportsStatus(null);
    setClientExportsIsError(false);
    setIsDeletingClientExports(false);
  }, [selectedClient]);

  const handleOpenAdviceHtml = async () => {
    if (!selectedClient) {
      return;
    }
    const pdfUrl = `${buildAdvicePdfUrl(selectedClient.id)}?generate=1`;

    try {
      const response = await fetchPdfBlob(pdfUrl);
      if (response.status < 200 || response.status >= 300) {
        const detail = await extractErrorDetail(response.data);
        setPdfGenerationIsError(true);
        setPdfGenerationMessage(buildPdfErrorMessage(response.status, detail));
        return;
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
      const response = await fetchPdfBlob(url);
      if (response.status < 200 || response.status >= 300) {
        const detail = await extractErrorDetail(response.data);
        setPdfGenerationIsError(true);
        setPdfGenerationMessage(buildPdfErrorMessage(response.status, detail));
        return;
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
    const response = await fetchPdfBlob(url);
    if (response.status < 200 || response.status >= 300) {
      throw new Error("kit-generate-failed");
    }
  };

  const handleDownloadKitPdf = (product: NewProduct) => {
    if (!selectedClient) {
      return;
    }

    const clientId = selectedClient.id;
    const viewUrl = buildKitPdfUrl(clientId, product.id);

    void (async () => {
      // קודם מנסים לפתוח קיט קיים, בלי יצירה כבדה
      try {
        const existingResponse = await fetchPdfBlob(viewUrl);
        if (existingResponse.status >= 200 && existingResponse.status < 300) {
          await openPdfTabFromBlob(existingResponse.data);
          return;
        }
      } catch {
        // אם יש שגיאה ברשת, נעבור לנסיון יצירה למטה
      }

      // אם אין קיט קיים, מנסים להפיק קיט חדש ואז לפתוח אותו
      try {
        await handleGenerateKitPdf(product);
        const generatedResponse = await fetchPdfBlob(viewUrl);
        if (generatedResponse.status >= 200 && generatedResponse.status < 300) {
          await openPdfTabFromBlob(generatedResponse.data);
        }
      } catch {
        // בשלב זה אין טיפול הודעות ייעודי לקיט בודד; השגיאה פשוט לא תפתח קובץ
      }
    })();
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
      const response = await fetchPdfBlob(url);
      if (response.status < 200 || response.status >= 300) {
        const detail = await extractErrorDetail(response.data);
        setPdfGenerationIsError(true);
        setPdfGenerationMessage(buildPdfErrorMessage(response.status, detail));
        return;
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
    const url = buildPacketPdfUrl(selectedClient.id);

    // קודם כל מנסים לפתוח חבילה קיימת בלי להפעיל יצירה כבדה מחדש
    try {
      const response = await fetchPdfBlob(url);
      if (response.status >= 200 && response.status < 300) {
        await triggerPdfDownloadFromBlob(response.data);
        return;
      }
    } catch {
      // אם יש שגיאת רשת, נעבור לנסיון יצירה למטה
    }

    // אם אין חבילה קיימת, מפעילים יצירה ולאחריה ניסיון תצוגה
    await handleGeneratePacketPdf();
    try {
      const response = await fetchPdfBlob(url);
      if (response.status >= 200 && response.status < 300) {
        await triggerPdfDownloadFromBlob(response.data);
      }
    } catch {
      // אם גם כאן יש תקלה, לא נעשה עוד ניסיון
    }
  };

  const handlePreviewSignedPacketPdf = () => {
    if (!selectedClient) {
      return;
    }
    const url = buildSignedClientPacketPdfUrl(selectedClient.id);
    void (async () => {
      try {
        const response = await fetchPdfBlob(url);
        if (response.status >= 200 && response.status < 300) {
          await openPdfTabFromBlob(response.data);
        }
      } catch {
        // אם יש שגיאה ברשת, לא נפתח קובץ
      }
    })();
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

  const handlePacketUploadFileChange = (event: ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0] ?? null;
    setPacketUploadFile(file);
  };

  const handleUploadPacketPdf = async () => {
    if (!selectedClient || !packetUploadFile) {
      return;
    }

    try {
      await uploadPacketPdf(selectedClient.id, packetUploadFile);
      setPacketUploadIsError(false);
      setPacketUploadStatus("חבילת הטפסים הערוכה נשמרה בתיקיית הלקוח");
    } catch (error: any) {
      const detail = error?.response?.data?.detail || error?.message;
      setPacketUploadIsError(true);
      setPacketUploadStatus(detail || "שגיאה בהעלאת חבילת הטפסים");
    }
  };

  const handleDeleteClientExports = async () => {
    if (!selectedClient) {
      return;
    }

    // eslint-disable-next-line no-alert
    const confirmed = window.confirm(
      "האם אתה בטוח שברצונך למחוק את כל קבצי ה-PDF של הלקוח?"
    );
    if (!confirmed) {
      return;
    }

    setIsDeletingClientExports(true);
    setClientExportsStatus(null);
    setClientExportsIsError(false);

    try {
      await deleteClientExports(selectedClient.id);
      setClientExportsIsError(false);
      setClientExportsStatus("כל קבצי ה-PDF של הלקוח נמחקו בהצלחה");
    } catch (error: any) {
      const detail = error?.response?.data?.detail || error?.message;
      setClientExportsIsError(true);
      setClientExportsStatus(detail || "שגיאה במחיקת תיקיית הקבצים של הלקוח");
    } finally {
      setIsDeletingClientExports(false);
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

  return {
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
  };
}
