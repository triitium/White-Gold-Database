export function formatRuntime(minutes: number | null): string {
  if (minutes == null) {
    return "—";
  }

  const hours = Math.floor(minutes / 60);
  const rest = minutes % 60;

  if (!hours) {
    return `${rest} min`;
  }

  return `${hours}h ${rest.toString().padStart(2, "0")}m`;
}

export function normalizedRating(
  value: number | null,
  scale: number,
): number | null {
  if (value == null) {
    return null;
  }

  return (value / scale) * 100;
}

export function displayScore(value: number | null): string {
  if (value == null) {
    return "—";
  }

  return Number.isInteger(value)
    ? `${value}`
    : value.toFixed(1);
}

export function dateLabel(value: string): string {
  return new Intl.DateTimeFormat(undefined, {
    dateStyle: "medium",
  }).format(new Date(value));
}
