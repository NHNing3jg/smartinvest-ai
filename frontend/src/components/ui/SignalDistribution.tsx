import type { RecommendationSignal } from "../../types/recommendation";

type SignalDistributionProps = {
  counts: Record<RecommendationSignal, number>;
  total: number;
};

const SIGNALS: RecommendationSignal[] = ["BUY", "HOLD", "SELL"];

const formatShare = (count: number, total: number) => {
  if (total <= 0) {
    return "0.00%";
  }

  return `${((count / total) * 100).toFixed(2)}%`;
};

export default function SignalDistribution({ counts, total }: SignalDistributionProps) {
  return (
    <div className="signal-distribution-grid">
      {SIGNALS.map((signal) => {
        const count = counts[signal];
        const share = total > 0 ? (count / total) * 100 : 0;

        return (
          <article key={signal} className={`signal-distribution-card signal-distribution-${signal.toLowerCase()}`}>
            <div className="signal-distribution-meta">
              <span>{signal}</span>
              <strong>{count.toLocaleString()}</strong>
            </div>
            <div className="signal-distribution-track">
              <span style={{ width: `${share}%` }} />
            </div>
            <em>{formatShare(count, total)} of filtered set</em>
          </article>
        );
      })}
    </div>
  );
}
