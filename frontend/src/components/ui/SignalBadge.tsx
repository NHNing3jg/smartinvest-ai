import type { RecommendationSignal } from "../../types/recommendation";

type SignalBadgeProps = {
  signal: RecommendationSignal | string | null;
};

export default function SignalBadge({ signal }: SignalBadgeProps) {
  const normalizedSignal = signal?.toUpperCase() ?? "N/A";
  const badgeVariant = ["BUY", "HOLD", "SELL"].includes(normalizedSignal)
    ? normalizedSignal.toLowerCase()
    : "unknown";
  const className = `signal-badge signal-badge-${badgeVariant}`;

  return <span className={className}>{normalizedSignal}</span>;
}
