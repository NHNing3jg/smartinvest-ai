type AllocationBarProps = {
  label: string;
  value: number | null;
  maxValue: number;
  variant: "weight" | "risk";
  formatter: (value: number) => string;
};

export default function AllocationBar({ label, value, maxValue, variant, formatter }: AllocationBarProps) {
  const normalizedMax = maxValue > 0 ? maxValue : 1;
  const width = value === null ? 0 : Math.min(100, (Math.max(value, 0) / normalizedMax) * 100);

  return (
    <div className="allocation-bar-row">
      <div className="allocation-bar-meta">
        <span>{label}</span>
        <strong>{value === null ? "N/A" : formatter(value)}</strong>
      </div>
      <div className="allocation-bar-track" aria-hidden="true">
        <span className={`allocation-bar-fill allocation-bar-fill-${variant}`} style={{ width: `${width}%` }} />
      </div>
    </div>
  );
}
