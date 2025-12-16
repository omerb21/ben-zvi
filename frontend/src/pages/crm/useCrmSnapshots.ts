import { useState } from "react";
import type {
  ClientSummary,
  Snapshot,
  HistoryPoint,
  FundHistoryPoint,
} from "../../api/crmApi";
import type { Dispatch, SetStateAction } from "react";
import {
  selectSnapshotAction,
  createSnapshotAction,
  exportClientReportAction,
  exportClientPdfAction,
} from "./crmSnapshotsAndExport";

export type UseCrmSnapshotsArgs = {
  selectedClient: ClientSummary | null;
  setLoading: Dispatch<SetStateAction<boolean>>;
  setError: Dispatch<SetStateAction<string | null>>;
};

export function useCrmSnapshots({
  selectedClient,
  setLoading,
  setError,
}: UseCrmSnapshotsArgs) {
  const [snapshots, setSnapshots] = useState<Snapshot[]>([]);
  const [selectedSnapshot, setSelectedSnapshot] = useState<Snapshot | null>(
    null
  );
  const [clientHistory, setClientHistory] = useState<HistoryPoint[]>([]);
  const [fundHistory, setFundHistory] = useState<FundHistoryPoint[]>([]);

  const [newSnapshotFundCode, setNewSnapshotFundCode] = useState("");
  const [newSnapshotFundName, setNewSnapshotFundName] = useState("");
  const [newSnapshotFundType, setNewSnapshotFundType] = useState("");
  const [newSnapshotAmount, setNewSnapshotAmount] = useState("");
  const [newSnapshotDate, setNewSnapshotDate] = useState("");

  let latestMonth = "";
  snapshots.forEach((snapshot) => {
    const month = (snapshot.snapshotDate || "").slice(0, 7); // "YYYY-MM"
    if (month > latestMonth) {
      latestMonth = month;
    }
  });

  const snapshotsFromLatestMonth = snapshots.filter((snapshot) => {
    const month = (snapshot.snapshotDate || "").slice(0, 7);
    return month === latestMonth;
  });

  const latestSnapshotsByFund: Record<string, Snapshot> = {};
  snapshotsFromLatestMonth.forEach((snapshot) => {
    const key = snapshot.fundCode;
    const existing = latestSnapshotsByFund[key];
    if (!existing || snapshot.snapshotDate > existing.snapshotDate) {
      latestSnapshotsByFund[key] = snapshot;
    }
  });

  const latestSnapshots: Snapshot[] = Object.values(latestSnapshotsByFund);

  const handleSelectSnapshot = (snapshot: Snapshot) => {
    selectSnapshotAction({
      snapshot,
      selectedClient,
      setSelectedSnapshot,
      setFundHistory,
      setLoading,
      setError,
    });
  };

  const handleCreateSnapshot = () => {
    createSnapshotAction({
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
    });
  };

  const handleExportClientReport = () => {
    exportClientReportAction({
      selectedClient,
      latestSnapshots,
    });
  };

  const handleExportClientPdf = () => {
    exportClientPdfAction({
      selectedClient,
      latestSnapshots,
    });
  };

  return {
    snapshots,
    selectedSnapshot,
    clientHistory,
    fundHistory,
    newSnapshotFundCode,
    newSnapshotFundName,
    newSnapshotFundType,
    newSnapshotAmount,
    newSnapshotDate,
    latestSnapshots,
    setSnapshots,
    setSelectedSnapshot,
    setClientHistory,
    setFundHistory,
    setNewSnapshotFundCode,
    setNewSnapshotFundName,
    setNewSnapshotFundType,
    setNewSnapshotAmount,
    setNewSnapshotDate,
    handleSelectSnapshot,
    handleCreateSnapshot,
    handleExportClientReport,
    handleExportClientPdf,
  };
}
