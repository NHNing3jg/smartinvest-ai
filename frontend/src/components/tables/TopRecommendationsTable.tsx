import SignalBadge from "../ui/SignalBadge";
import type { Recommendation } from "../../types/recommendation";

type TopRecommendationsTableProps = {
  recommendations: Recommendation[];
  emptyTitle: string;
  emptyDetail: string;
  formatPercent: (value: number | null) => string;
  formatNumber: (value: number | null, digits?: number) => string;
};

export default function TopRecommendationsTable({
  recommendations,
  emptyTitle,
  emptyDetail,
  formatPercent,
  formatNumber,
}: TopRecommendationsTableProps) {
  if (recommendations.length === 0) {
    return (
      <div className="table-empty-state">
        <strong>{emptyTitle}</strong>
        <span>{emptyDetail}</span>
      </div>
    );
  }

  return (
    <div className="recommendation-table-wrap">
      <table className="recommendation-table top-recommendations-table">
        <thead>
          <tr>
            <th scope="col">Ticker</th>
            <th scope="col">Signal</th>
            <th scope="col">Proba Up</th>
            <th scope="col">Confidence</th>
            <th scope="col">Advisor Score</th>
            <th scope="col">Momentum 5</th>
            <th scope="col">Rolling Vol 10</th>
            <th scope="col">Explanation</th>
          </tr>
        </thead>
        <tbody>
          {recommendations.map((recommendation) => (
            <tr key={`top-${recommendation.signal}-${recommendation.date_id}-${recommendation.ticker}`}>
              <td data-label="Ticker">
                <strong className="ticker-cell">{recommendation.ticker}</strong>
              </td>
              <td data-label="Signal">
                <SignalBadge signal={recommendation.signal} />
              </td>
              <td data-label="Proba Up">{formatPercent(recommendation.proba_up)}</td>
              <td data-label="Confidence">{recommendation.confidence ?? "N/A"}</td>
              <td data-label="Advisor Score">{formatNumber(recommendation.advisor_score)}</td>
              <td data-label="Momentum 5">{formatNumber(recommendation.momentum_5, 4)}</td>
              <td data-label="Rolling Vol 10">{formatNumber(recommendation.rolling_vol_10, 4)}</td>
              <td data-label="Explanation" className="explanation-cell">
                <span className="table-explanation-preview" title={recommendation.explanation ?? undefined}>
                  {recommendation.explanation ?? "N/A"}
                </span>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
