export function ratingToBricks(rating: number | null): number | null {
  if (rating == null) {
    return null;
  }

  const clamped = Math.max(0, Math.min(100, rating));
  return Math.round((clamped / 20) * 2) / 2;
}
