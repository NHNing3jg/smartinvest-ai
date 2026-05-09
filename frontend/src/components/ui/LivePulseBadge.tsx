type LivePulseBadgeProps = {
  label: string;
};

export default function LivePulseBadge({ label }: LivePulseBadgeProps) {
  return (
    <div className="topbar-context live-pulse-badge" aria-label={label}>
      <span className="market-status-dot live-pulse-dot" aria-hidden="true" />
      <span>{label}</span>
    </div>
  );
}
