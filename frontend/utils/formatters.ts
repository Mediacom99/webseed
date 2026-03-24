export function formatTime(timestamp: string): string {
  try {
    const d = new Date(timestamp);
    return d.toLocaleTimeString("it-IT", {
      hour: "2-digit",
      minute: "2-digit",
      second: "2-digit",
    });
  } catch {
    return timestamp;
  }
}

export function formatDate(dateStr: string): string {
  try {
    return new Date(dateStr).toLocaleString("it-IT");
  } catch {
    return dateStr;
  }
}

export function humanizeKey(key: string): string {
  return key
    .replace(/^config\./, "")
    .replace(/_/g, " ")
    .replace(/\b\w/g, (c) => c.toUpperCase());
}

export function formatType(type: string): string {
  return type.replace(/_/g, " ");
}
