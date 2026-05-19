import { useState, type ChangeEvent } from "react";
import { importGemelNetXml, clearJustificationData, deleteAllDocuments } from "../../api/adminApi";

export type JustificationGemelState = {
  gemelFile: File | null;
  isGemelImporting: boolean;
  isJustificationClearing: boolean;
  isDeletingDocuments: boolean;
  importStatus: string | null;
  importError: string | null;
  handleGemelFileChange: (event: ChangeEvent<HTMLInputElement>) => void;
  handleRunGemelImport: () => void;
  handleClearJustificationData: () => void;
  handleDeleteAllDocuments: () => void;
};

export function useJustificationGemel(
  onGemelNetImportCompleted?: () => void
): JustificationGemelState {
  const [gemelFile, setGemelFile] = useState<File | null>(null);
  const [isGemelImporting, setIsGemelImporting] = useState(false);
  const [isJustificationClearing, setIsJustificationClearing] = useState(false);
  const [isDeletingDocuments, setIsDeletingDocuments] = useState(false);
  const [importStatus, setImportStatus] = useState<string | null>(null);
  const [importError, setImportError] = useState<string | null>(null);

  const handleGemelFileChange = (event: ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0] ?? null;
    setGemelFile(file);
  };

  const handleRunGemelImport = () => {
    if (!gemelFile || isGemelImporting || isJustificationClearing || isDeletingDocuments) {
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
    if (isGemelImporting || isJustificationClearing || isDeletingDocuments) {
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

  const handleDeleteAllDocuments = () => {
    if (isGemelImporting || isJustificationClearing || isDeletingDocuments) {
      return;
    }

    const confirmed = window.confirm(
      "האם אתה בטוח שברצונך למחוק את כל מסמכי ההנמקה (PDF) של כל הלקוחות? פעולה זו תפנה מקום בשרת אך המסמכים יאבדו לצמיתות."
    );
    if (!confirmed) {
      return;
    }

    setIsDeletingDocuments(true);
    setImportStatus(null);
    setImportError(null);
    deleteAllDocuments()
      .then((result) => {
        const mbFreed = (result.totalBytesFreed / (1024 * 1024)).toFixed(2);
        setImportStatus(
          `נמחקו ${result.deletedDirectories} תיקיות עם ${result.totalFilesDeleted} קבצים (${mbFreed} MB פונו). ` +
          `עובדו ${result.totalClients} לקוחות.`
        );
      })
      .catch((error: any) => {
        const detail = error?.response?.data?.detail || error?.message;
        setImportError(detail || "שגיאה במחיקת מסמכים");
      })
      .finally(() => {
        setIsDeletingDocuments(false);
      });
  };

  return {
    gemelFile,
    isGemelImporting,
    isJustificationClearing,
    isDeletingDocuments,
    importStatus,
    importError,
    handleGemelFileChange,
    handleRunGemelImport,
    handleClearJustificationData,
    handleDeleteAllDocuments,
  };
}
