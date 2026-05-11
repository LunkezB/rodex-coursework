interface SkeletonLineProps {
  width?: string;
  className?: string;
}

export function SkeletonLine({ width = "100%", className }: SkeletonLineProps) {
  return (
    <span
      className={["skeleton", "skeleton-line", className]
        .filter(Boolean)
        .join(" ")}
      style={width !== "100%" ? { width } : undefined}
      aria-hidden="true"
    />
  );
}

interface SkeletonCardProps {
  compact?: boolean;
}

export function SkeletonCard({ compact }: SkeletonCardProps) {
  return (
    <div
      className={`skeleton-card${compact ? " skeleton-compact" : ""}`}
      aria-hidden="true"
    >
      <SkeletonLine width="55%" />
      <SkeletonLine width="82%" />
      {!compact && <SkeletonLine width="38%" />}
    </div>
  );
}

interface SkeletonCardListProps {
  count?: number;
  compact?: boolean;
}

export function SkeletonCardList({ count = 3, compact }: SkeletonCardListProps) {
  return (
    <ul className="skeleton-card-list" aria-hidden="true">
      {Array.from({ length: count }, (_, i) => (
        <li key={i}>
          <SkeletonCard compact={compact} />
        </li>
      ))}
    </ul>
  );
}

export function SkeletonToolbar() {
  return (
    <div className="skeleton-toolbar" aria-hidden="true">
      <span className="skeleton skeleton-pill skeleton-pill-wide" />
      <span className="skeleton skeleton-pill" />
      <span className="skeleton skeleton-pill" />
    </div>
  );
}

export function SkeletonAuthCard() {
  return (
    <div className="skeleton-auth-card" aria-hidden="true">
      <SkeletonLine width="42%" />
      <SkeletonLine width="58%" className="skeleton-line-lg" />
      <span className="skeleton skeleton-pill" />
      <span className="skeleton skeleton-pill" />
      <span className="skeleton skeleton-pill" />
    </div>
  );
}
