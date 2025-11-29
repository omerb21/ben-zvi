import type {
  ClientSummary,
  Snapshot,
  FundHistoryPoint,
} from "../../api/crmApi";
import { fetchFundHistory, createSnapshotForClient } from "../../api/crmApi";
import httpClient from "../../api/httpClient";
import type { Dispatch, SetStateAction } from "react";

export type SelectSnapshotArgs = {
  snapshot: Snapshot;
  selectedClient: ClientSummary | null;
  setSelectedSnapshot: Dispatch<SetStateAction<Snapshot | null>>;
  setFundHistory: Dispatch<SetStateAction<FundHistoryPoint[]>>;
  setLoading: Dispatch<SetStateAction<boolean>>;
  setError: Dispatch<SetStateAction<string | null>>;
};

export function selectSnapshotAction({
  snapshot,
  selectedClient,
  setSelectedSnapshot,
  setFundHistory,
  setLoading,
  setError,
}: SelectSnapshotArgs) {
  setSelectedSnapshot(snapshot);
  setFundHistory([]);

  const fundNumber = (snapshot as any).fundNumber as string | undefined;
  const fundIdentifier = fundNumber || snapshot.fundCode;
  if (!selectedClient || !fundIdentifier) {
    return;
  }

  setLoading(true);
  fetchFundHistory(selectedClient.id, fundIdentifier)
    .then((items) => {
      setFundHistory(items);
      setError(null);
    })
    .catch(() => {
      setError("שגיאה בטעינת היסטוריית קופה");
    })
    .finally(() => {
      setLoading(false);
    });
}

export type CreateSnapshotArgs = {
  selectedClient: ClientSummary | null;
  newSnapshotFundCode: string;
  newSnapshotAmount: string;
  newSnapshotDate: string;
  newSnapshotFundType: string;
  newSnapshotFundName: string;
  setLoading: Dispatch<SetStateAction<boolean>>;
  setSnapshots: Dispatch<SetStateAction<Snapshot[]>>;
  setNewSnapshotFundCode: Dispatch<SetStateAction<string>>;
  setNewSnapshotFundName: Dispatch<SetStateAction<string>>;
  setNewSnapshotFundType: Dispatch<SetStateAction<string>>;
  setNewSnapshotAmount: Dispatch<SetStateAction<string>>;
  setNewSnapshotDate: Dispatch<SetStateAction<string>>;
  setError: Dispatch<SetStateAction<string | null>>;
};

export function createSnapshotAction({
  selectedClient,
  newSnapshotFundCode,
  newSnapshotAmount,
  newSnapshotDate,
  newSnapshotFundType,
  newSnapshotFundName,
  setLoading,
  setSnapshots,
  setNewSnapshotFundCode,
  setNewSnapshotFundName,
  setNewSnapshotFundType,
  setNewSnapshotAmount,
  setNewSnapshotDate,
  setError,
}: CreateSnapshotArgs) {
  if (!selectedClient) {
    return;
  }

  const fundCode = newSnapshotFundCode.trim();
  const amountText = newSnapshotAmount.trim();
  const snapshotDate = newSnapshotDate.trim();

  if (!fundCode || !amountText || !snapshotDate) {
    return;
  }

  const amount = Number(amountText.replace(/,/g, ""));
  if (!Number.isFinite(amount)) {
    return;
  }

  const payload = {
    fundCode,
    amount,
    snapshotDate,
  };

  if (newSnapshotFundType.trim()) {
    (payload as any).fundType = newSnapshotFundType.trim();
  }
  if (newSnapshotFundName.trim()) {
    (payload as any).fundName = newSnapshotFundName.trim();
  }

  setLoading(true);
  createSnapshotForClient(selectedClient.id, payload)
    .then((created) => {
      setSnapshots((prev) => [created, ...prev]);
      setNewSnapshotFundCode("");
      setNewSnapshotFundName("");
      setNewSnapshotFundType("");
      setNewSnapshotAmount("");
      setNewSnapshotDate("");
      setError(null);
    })
    .catch(() => {
      setError("שגיאה ביצירת צילום מוצר");
    })
    .finally(() => {
      setLoading(false);
    });
}

function escapeCsvValue(value: string): string {
  const text = value ?? "";
  if (/[",\r\n]/.test(text)) {
    return `"${text.replace(/"/g, '""')}"`;
  }
  return text;
}

export type ExportClientReportArgs = {
  selectedClient: ClientSummary | null;
  latestSnapshots: Snapshot[];
};

export function exportClientReportAction({
  selectedClient,
  latestSnapshots,
}: ExportClientReportArgs) {
  if (!selectedClient || latestSnapshots.length === 0) {
    return;
  }

  const headers = [
    "תאריך צילום",
    "קוד קופה",
    "שם קופה",
    "סוג קופה",
    "סכום",
    "מקור",
  ];

  const rows = latestSnapshots.map((snapshot) => {
    const fundName = (snapshot as any).fundName || "";
    const fundType = (snapshot as any).fundType || "";
    const source = (snapshot as any).source || "";
    return [
      snapshot.snapshotDate || "",
      snapshot.fundCode || "",
      fundName,
      fundType,
      (snapshot.amount ?? 0).toString(),
      source,
    ];
  });

  const lines = [
    headers.map(escapeCsvValue).join(","),
    ...rows.map((row) => row.map(escapeCsvValue).join(",")),
  ];

  const csvContent = "\uFEFF" + lines.join("\r\n");
  const blob = new Blob([csvContent], {
    type: "text/csv;charset=utf-8;",
  });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  const safeName = (
    selectedClient.fullName || selectedClient.idNumber || "client"
  ).replace(/[^a-zA-Z0-9\u0590-\u05FF]+/g, "_");
  link.href = url;
  link.download = `client_report_${safeName}.csv`;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
}

export type ExportClientPdfArgs = {
  selectedClient: ClientSummary | null;
  latestSnapshots: Snapshot[];
};

export function exportClientPdfAction({
  selectedClient,
  latestSnapshots,
}: ExportClientPdfArgs) {
  if (!selectedClient || latestSnapshots.length === 0) {
    return;
  }

  const baseUrl = (httpClient.defaults.baseURL || "").replace(/\/+$/, "");
  const reportUrl = `${baseUrl}/api/v1/crm/clients/${selectedClient.id}/report.pdf`;
  window.open(reportUrl, "_blank");
}
