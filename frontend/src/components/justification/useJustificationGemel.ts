import { useState, type ChangeEvent } from "react";
import { importGemelNetXml, clearJustificationData } from "../../api/adminApi";

export type JustificationGemelState = {
  gemelFile: File | null;
  isGemelImporting: boolean;
  isJustificationClearing: boolean;
  importStatus: string | null;
  importError: string | null;
  handleGemelFileChange: (event: ChangeEvent<HTMLInputElement>) => void;
  handleRunGemelImport: () => void;
  handleClearJustificationData: () => void;
};

export function useJustificationGemel(
  onGemelNetImportCompleted?: () => void
): JustificationGemelState {
  const [gemelFile, setGemelFile] = useState<File | null>(null);
  const [isGemelImporting, setIsGemelImporting] = useState(false);
  const [isJustificationClearing, setIsJustificationClearing] = useState(false);
  const [importStatus, setImportStatus] = useState<string | null>(null);
  const [importError, setImportError] = useState<string | null>(null);

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

  return {
    gemelFile,
    isGemelImporting,
    isJustificationClearing,
    importStatus,
    importError,
    handleGemelFileChange,
    handleRunGemelImport,
    handleClearJustificationData,
  };
}
