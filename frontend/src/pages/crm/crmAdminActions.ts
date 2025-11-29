import type { ChangeEvent } from "react";
import type { Dispatch, SetStateAction } from "react";
import { importCrmExcel, clearCrmData } from "../../api/adminApi";

export type CrmFileChangeArgs = {
  event: ChangeEvent<HTMLInputElement>;
  setCrmImportFiles: Dispatch<SetStateAction<File[]>>;
};

export function crmFileChangeHandler({
  event,
  setCrmImportFiles,
}: CrmFileChangeArgs) {
  const { files } = event.target;
  if (!files || files.length === 0) {
    setCrmImportFiles([]);
    return;
  }
  const nextFiles: File[] = [];
  for (let i = 0; i < files.length; i += 1) {
    nextFiles.push(files[i]);
  }
  setCrmImportFiles(nextFiles);
}

export type RunCrmImportArgs = {
  crmImportFiles: File[];
  crmImportMonth: string;
  isCrmImporting: boolean;
  isCrmClearing: boolean;
  setIsCrmImporting: Dispatch<SetStateAction<boolean>>;
  setCrmAdminMessage: Dispatch<SetStateAction<string | null>>;
  setCrmAdminError: Dispatch<SetStateAction<string | null>>;
};

export function runCrmImportAction({
  crmImportFiles,
  crmImportMonth,
  isCrmImporting,
  isCrmClearing,
  setIsCrmImporting,
  setCrmAdminMessage,
  setCrmAdminError,
}: RunCrmImportArgs) {
  if (
    crmImportFiles.length === 0 ||
    !crmImportMonth ||
    isCrmImporting ||
    isCrmClearing
  ) {
    return;
  }

  setIsCrmImporting(true);
  setCrmAdminMessage(null);
  setCrmAdminError(null);

  Promise.all(crmImportFiles.map((file) => importCrmExcel(file, crmImportMonth)))
    .then((results) => {
      if (results.length === 0) {
        return;
      }

      const aggregated = results.reduce(
        (acc, current) => ({
          companyCode: current.companyCode,
          createdClients: acc.createdClients + current.createdClients,
          reusedClients: acc.reusedClients + current.reusedClients,
          createdSnapshots: acc.createdSnapshots + current.createdSnapshots,
          rowsProcessed: acc.rowsProcessed + current.rowsProcessed,
          duplicatesSkipped: acc.duplicatesSkipped + current.duplicatesSkipped,
        }),
        {
          companyCode: results[0].companyCode,
          createdClients: 0,
          reusedClients: 0,
          createdSnapshots: 0,
          rowsProcessed: 0,
          duplicatesSkipped: 0,
        }
      );

      setCrmAdminMessage(
        `ייבוא CRM (Excel) מתוך ${results.length} קבצים: נוצרו ${aggregated.createdClients} לקוחות, נעשה שימוש חוזר ב-${aggregated.reusedClients} לקוחות, נוצרו ${aggregated.createdSnapshots} צילומים (שורות: ${aggregated.rowsProcessed}, כפילויות שדולגו: ${aggregated.duplicatesSkipped})`
      );
    })
    .catch((error: any) => {
      const detail = error?.response?.data?.detail || error?.message;
      setCrmAdminError(detail || "שגיאה בייבוא CRM מקובצי Excel");
    })
    .finally(() => {
      setIsCrmImporting(false);
    });
}

export type ClearCrmDataLocalArgs = {
  isCrmImporting: boolean;
  isCrmClearing: boolean;
  setIsCrmClearing: Dispatch<SetStateAction<boolean>>;
  setCrmAdminMessage: Dispatch<SetStateAction<string | null>>;
  setCrmAdminError: Dispatch<SetStateAction<string | null>>;
};

export function clearCrmDataLocalAction({
  isCrmImporting,
  isCrmClearing,
  setIsCrmClearing,
  setCrmAdminMessage,
  setCrmAdminError,
}: ClearCrmDataLocalArgs) {
  if (isCrmImporting || isCrmClearing) {
    return;
  }

  // eslint-disable-next-line no-alert
  const confirmed = window.confirm(
    "האם אתה בטוח שברצונך למחוק את כל נתוני ה-CRM (צילומים ותזכורות)?"
  );
  if (!confirmed) {
    return;
  }

  setIsCrmClearing(true);
  setCrmAdminMessage(null);
  setCrmAdminError(null);

  clearCrmData()
    .then((result) => {
      setCrmAdminMessage(
        `נמחקו נתוני CRM: ${result.deletedSnapshots} צילומים ו-${result.deletedClientNotes} תזכורות`
      );
    })
    .catch(() => {
      setCrmAdminError("שגיאה במחיקת נתוני CRM");
    })
    .finally(() => {
      setIsCrmClearing(false);
    });
}
