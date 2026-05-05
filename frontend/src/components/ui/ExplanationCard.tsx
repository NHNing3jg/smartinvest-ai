import SignalBadge from "./SignalBadge";
import type { Recommendation } from "../../types/recommendation";

type ExplanationCardProps = {
  recommendation: Recommendation;
  formatPercent: (value: number | null) => string;
  formatNumber: (value: number | null, digits?: number) => string;
};

export default function ExplanationCard({ recommendation, formatPercent, formatNumber }: ExplanationCardProps) {
  return (
    <article className="advisor-explanation-card">
      <div className="advisor-explanation-card-header">
        <div>
          <span className="advisor-explanation-ticker">{recommendation.ticker}</span>
          <SignalBadge signal={recommendation.signal} />
        </div>
        <strong>{formatPercent(recommendation.proba_up)}</strong>
      </div>

      <div className="advisor-explanation-metrics">
        <span>Confidence: {recommendation.confidence ?? "N/A"}</span>
        <span>Score: {formatNumber(recommendation.advisor_score)}</span>
      </div>

      <p>{recommendation.explanation ?? "N/A"}</p>
    </article>
  );
}
