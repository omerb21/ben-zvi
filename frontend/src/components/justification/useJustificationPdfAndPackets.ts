import { useEffect, useState, ChangeEvent } from "react";
import type { NewProduct } from "../../api/justificationApi";
import {
  buildAdvicePdfUrl,
  buildB1PdfUrl,
  buildKitPdfUrl,
  buildPacketPdfUrl,
  buildSignedClientPacketPdfUrl,
  createPacketSignRequest,
  uploadPacketPdf,
  trimPacketPdf,
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
      const { deleteClientExports } = await import("../../api/justificationApi");
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
