import { useState, type ChangeEvent } from "react";
import {
  crmFileChangeHandler,
  runCrmImportAction,
  clearCrmDataLocalAction,
} from "./crmAdminActions";

export function useCrmAdmin() {
  const [crmImportFiles, setCrmImportFiles] = useState<File[]>([]);
  const [crmImportMonth, setCrmImportMonth] = useState(""
  );
  const [isCrmImporting, setIsCrmImporting] = useState(false);
  const [isCrmClearing, setIsCrmClearing] = useState(false);
  const [crmAdminMessage, setCrmAdminMessage] = useState<string | null>(null);
  const [crmAdminError, setCrmAdminError] = useState<string | null>(null);

  const handleCrmFileChange = (event: ChangeEvent<HTMLInputElement>) => {
    crmFileChangeHandler({
      event,
      setCrmImportFiles,
    });
  };

  const handleRunCrmImport = () => {
    runCrmImportAction({
      crmImportFiles,
      crmImportMonth,
      isCrmImporting,
      isCrmClearing,
      setIsCrmImporting,
      setCrmAdminMessage,
      setCrmAdminError,
    });
  };

  const handleClearCrmDataLocal = () => {
    clearCrmDataLocalAction({
      isCrmImporting,
      isCrmClearing,
      setIsCrmClearing,
      setCrmAdminMessage,
      setCrmAdminError,
    });
  };

  return {
    crmImportFiles,
    crmImportMonth,
    isCrmImporting,
    isCrmClearing,
    crmAdminMessage,
    crmAdminError,
    setCrmImportMonth,
    handleCrmFileChange,
    handleRunCrmImport,
    handleClearCrmDataLocal,
  };
}
