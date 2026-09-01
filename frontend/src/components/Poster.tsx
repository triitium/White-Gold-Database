type Props = {
  src: string | null;
  alt: string;
  className?: string;
};

function resolvePosterSrc(src: string): string {
  // TMDB poster_path values are stored as e.g. "/abc123.jpg".
  // Convert them to an actual TMDB image URL here so every Poster
  // consumer gets consistent behaviour.
  if (src.startsWith("/") && !src.startsWith("//")) {
    return `https://image.tmdb.org/t/p/w500${src}`;
  }

  return src;
}

export function Poster({ src, alt, className = "" }: Props) {
  if (!src) {
    return (
      <div
        className={`poster poster--placeholder ${className}`}
        aria-label={`No poster available for ${alt}`}
      >
        <span>{alt.slice(0, 1).toUpperCase()}</span>
      </div>
    );
  }

  return (
    <img
      className={`poster ${className}`}
      src={resolvePosterSrc(src)}
      alt={`${alt} poster`}
      loading="lazy"
    />
  );
}
