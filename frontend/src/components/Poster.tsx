type Props = {
  src: string | null;
  alt: string;
  className?: string;
};

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
      src={src}
      alt={`${alt} poster`}
      loading="lazy"
    />
  );
}
