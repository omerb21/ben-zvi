export function isoToDmy(value: string | null | undefined): string {
  if (!value) {
    return "";
  }
  const text = String(value).trim();
  if (text.length < 10) {
    return text;
  }
  const year = text.slice(0, 4);
  const month = text.slice(5, 7);
  const day = text.slice(8, 10);
  if (!/^\d{4}$/.test(year) || !/^\d{2}$/.test(month) || !/^\d{2}$/.test(day)) {
    return text;
  }
  const base = `${day}/${month}/${year}`;

  // If there is a time component like YYYY-MM-DD HH:MM:SS, keep only HH:MM
  if (text.length > 10) {
    const timePart = text.slice(11, 16);
    if (/^\d{2}:\d{2}$/.test(timePart)) {
      return `${base} ${timePart}`;
    }
  }

  return base;
}

export function dmyToIso(value: string | null | undefined): string | null {
  if (!value) {
    return null;
  }
  const text = String(value).trim();
  if (!text) {
    return null;
  }

  // Already ISO YYYY-MM-DD (or with time) – normalize to first 10 chars
  if (/^\d{4}-\d{2}-\d{2}/.test(text)) {
    return text.slice(0, 10);
  }

  const parts = text.split(/[\/.\-]/).filter(Boolean);
  if (parts.length < 3) {
    return null;
  }
  const [dayRaw, monthRaw, yearRaw] = parts;
  const day = parseInt(dayRaw, 10);
  const month = parseInt(monthRaw, 10);
  const year = parseInt(yearRaw, 10);

  if (!Number.isFinite(day) || !Number.isFinite(month) || !Number.isFinite(year)) {
    return null;
  }
  if (day < 1 || day > 31 || month < 1 || month > 12) {
    return null;
  }

  const yearStr = year.toString().padStart(4, "0");
  const monthStr = month.toString().padStart(2, "0");
  const dayStr = day.toString().padStart(2, "0");

  return `${yearStr}-${monthStr}-${dayStr}`;
}
