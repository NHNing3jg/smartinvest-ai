import type { BacktestSignal } from "../../types/backtest";

type MetricBarProps = {
  signal: BacktestSignal;
  label: string;
  value: number | null;
  maxValue: number;
  formatter: (value: number) => string;
};

export default function MetricBar({ signal, label, value, maxValue, formatter }: MetricBarProps) {
  const normalizedMax = maxValue > 0 ? maxValue : 1;
  const width = value === null ? 0 : Math.min(100, (Math.abs(value) / normalizedMax) * 100);
  const signalClass = signal.toLowerCase();

  return (
    <div className="metric-bar-row">
      <div className="metric-bar-meta">
        <span>{label}</span>
        <strong>{value === null ? "N/A" : formatter(value)}</strong>
      </div>
      <div className="metric-bar-track" aria-hidden="true">
        <span
          className={`metric-bar-fill metric-bar-fill-${signalClass}`}
          style={{ width: `${width}%` }}
        />
      </div>
    </div>
  );
}
