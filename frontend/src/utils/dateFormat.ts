export function isoToDmy(value: string | null | undefined): string {
  if (!value) {
    return "";
  }

  const text = String(value).trim();
  if (!text) {
    return "";
  }

  // 1) תאריכים בפורמט ISO: YYYY-MM-DD או YYYY-MM-DD HH:MM:SS
  const isoMatch = text.match(/^(\d{4})-(\d{2})-(\d{2})/);
  if (isoMatch) {
    const [, year, month, day] = isoMatch;
    const base = `${day}/${month}/${year}`;

    // אם יש רכיב שעה (HH:MM) נשאיר אותו בצד ימין
    if (text.length > 10) {
      const timePart = text.slice(11, 16);
      if (/^\d{2}:\d{2}$/.test(timePart)) {
        return `${base} ${timePart}`;
      }
    }

    return base;
  }

  // 2) תמיכה בנתונים ישנים שנשמרו כ-MM/DD/YYYY –
  //    ממיר אותם ל-DD/MM/YYYY כאשר זה חד-משמעי (חודש <= 12, יום > 12).
  const legacyMatch = text.match(/^(\d{1,2})[\/.\-](\d{1,2})[\/.\-](\d{2,4})$/);
  if (legacyMatch) {
    const [, firstRaw, secondRaw, yearRaw] = legacyMatch;
    const first = Number.parseInt(firstRaw, 10);
    const second = Number.parseInt(secondRaw, 10);
    const yearNum = Number.parseInt(yearRaw, 10);

    if (
      Number.isFinite(first) &&
      Number.isFinite(second) &&
      Number.isFinite(yearNum) &&
      first >= 1 &&
      first <= 12 &&
      second >= 1 &&
      second <= 31 &&
      second > 12
    ) {
      // נניח שמדובר ב-MM/DD/YYYY ונחליף ל-DD/MM/YYYY
      const yearStr = yearNum.toString().padStart(4, "0");
      const monthStr = first.toString().padStart(2, "0");
      const dayStr = second.toString().padStart(2, "0");
      return `${dayStr}/${monthStr}/${yearStr}`;
    }

    // אם המבנה לא תואם לדפוס חד-משמעי של MM/DD/YYYY (למשל כבר DD/MM/YYYY
    // או מקרה אמביוולנטי), נשאיר את הטקסט כפי שהוא.
    return text;
  }

  // עבור כל שאר המקרים, לא ניגע בטקסט כדי לא לשבור נתונים לא צפויים.
  return text;
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
