export function Loading({ label = "Loading…" }: { label?: string }) {
  return (
    <div className="loading">
      <span className="loading__spinner" />
      <span>{label}</span>
    </div>
  );
}
