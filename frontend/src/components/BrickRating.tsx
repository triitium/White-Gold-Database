import { ratingToBricks } from "../lib/bricks";

type Props = {
  rating: number | null;
  compact?: boolean;
  showNumeric?: boolean;
};

export function BrickRating({
  rating,
  compact = false,
  showNumeric = true,
}: Props) {
  const brickValue = ratingToBricks(rating);

  if (brickValue == null) {
    return <span className="muted">Not rated</span>;
  }

  return (
    <div
      className={`brick-rating ${compact ? "brick-rating--compact" : ""}`}
      title={`${rating}/100 · ${brickValue}/5 Bricks`}
      aria-label={`${brickValue} out of 5 Bricks, ${rating} out of 100`}
    >
      <div className="brick-row" aria-hidden="true">
        {[0, 1, 2, 3, 4].map((index) => {
          const fill = Math.max(
            0,
            Math.min(1, brickValue - index),
          );

          return (
            <span className="brick-shell" key={index}>
              <span
                className="brick-fill"
                style={{ width: `${fill * 100}%` }}
              />
              <span className="brick-band brick-band--a" />
              <span className="brick-band brick-band--b" />
            </span>
          );
        })}
      </div>

      {!compact && (
        <div className="brick-caption">
          <strong>{brickValue.toFixed(1)} / 5 Bricks</strong>
          {showNumeric && (
            <span>{rating} / 100</span>
          )}
        </div>
      )}

      {compact && showNumeric && (
        <span className="brick-compact-score">{rating}</span>
      )}
    </div>
  );
}
