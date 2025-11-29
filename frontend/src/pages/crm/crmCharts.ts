import type { HistoryPoint, MonthlyChangePoint } from "../../api/crmApi";

export function buildHistoryChartData(history: HistoryPoint[]): {
  path: string;
  points: { x: number; y: number }[];
} {
  if (!history || history.length < 2) {
    return { path: "", points: [] };
  }

  const maxAmount = Math.max(...history.map((point) => point.amount || 0));
  if (!Number.isFinite(maxAmount) || maxAmount <= 0) {
    return { path: "", points: [] };
  }

  const count = history.length;
  const points = history.map((point, index) => {
    const ratio = (point.amount || 0) / maxAmount;
    const x = count === 1 ? 50 : (index / (count - 1)) * 100;
    const y = 95 - ratio * 80;
    return { x, y };
  });

  const path = points
    .map((p, index) => `${index === 0 ? "M" : "L"} ${p.x},${p.y}`)
    .join(" ");

  return { path, points };
}

export function buildMonthlyChangeChartData(points: MonthlyChangePoint[]): {
  path: string;
  points: { x: number; y: number }[];
} {
  if (!points || points.length < 2) {
    return { path: "", points: [] };
  }

  const maxTotal = Math.max(...points.map((p) => p.total || 0));
  if (!Number.isFinite(maxTotal) || maxTotal <= 0) {
    return { path: "", points: [] };
  }

  const count = points.length;
  const scaled = points.map((point, index) => {
    const ratio = (point.total || 0) / maxTotal;
    const x = count === 1 ? 50 : (index / (count - 1)) * 100;
    const y = 95 - ratio * 80;
    return { x, y };
  });

  const path = scaled
    .map((p, index) => `${index === 0 ? "M" : "L"} ${p.x},${p.y}`)
    .join(" ");

  return { path, points: scaled };
}
