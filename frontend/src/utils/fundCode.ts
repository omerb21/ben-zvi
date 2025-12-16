export function getCoreFundCode(value: string | null | undefined): string {
  const text = (value ?? "").toString().trim();
  if (!text) {
    return "";
  }

  const match = text.match(/\((\d+)\)/);
  if (match) {
    return match[1];
  }

  return text;
}
