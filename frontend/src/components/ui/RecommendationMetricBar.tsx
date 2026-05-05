import type { CSSProperties } from "react";

type RecommendationMetricBarProps = {
  label: string;
  value: number | null;
  maxValue: number;
  formatter: (value: number | null) => string;
  variant?: "probability" | "score" | "buy" | "hold" | "sell";
};

const getFillWidth = (value: number | null, maxValue: number) => {
  if (value === null || !Number.isFinite(value) || maxValue <= 0) {
    return 0;
  }

  return Math.min(Math.max((Math.abs(value) / maxValue) * 100, 0), 100);
};

export default function RecommendationMetricBar({
  label,
  value,
  maxValue,
  formatter,
  variant = "score",
}: RecommendationMetricBarProps) {
  const width = getFillWidth(value, maxValue);
  const style = { "--bar-width": `${width}%` } as CSSProperties;

  return (
    <div className="advisor-metric-bar-row">
      <div className="advisor-metric-bar-meta">
        <span>{label}</span>
        <strong>{formatter(value)}</strong>
      </div>
      <div className="advisor-metric-bar-track">
        <span className={`advisor-metric-bar-fill advisor-metric-bar-fill-${variant}`} style={style} />
      </div>
    </div>
  );
}
