type Props = {
  label: string;
  value: number | null;
  suffix?: string;
};

export function ScoreBadge({ label, value, suffix = "" }: Props) {
  return (
    <div className="score-badge">
      <span className="score-badge__label">{label}</span>
      <strong className="score-badge__value">
        {value == null
          ? "—"
          : `${Number.isInteger(value) ? value : value.toFixed(1)}${suffix}`}
      </strong>
    </div>
  );
}
