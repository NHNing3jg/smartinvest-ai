import SignalBadge from "../ui/SignalBadge";
import type { Recommendation } from "../../types/recommendation";

type RecommendationTableProps = {
  recommendations: Recommendation[];
};

const formatNumber = (value: number | null | undefined, digits = 3) => {
  if (value === null || value === undefined || Number.isNaN(value)) {
    return "N/A";
  }

  return value.toFixed(digits);
};

export default function RecommendationTable({ recommendations }: RecommendationTableProps) {
  if (recommendations.length === 0) {
    return (
      <div className="table-empty-state">
        <strong>No recommendations available</strong>
        <span>The API returned an empty recommendation set.</span>
      </div>
    );
  }

  return (
    <div className="recommendation-table-wrap">
      <table className="recommendation-table">
        <thead>
          <tr>
            <th scope="col">Ticker</th>
            <th scope="col">Signal</th>
            <th scope="col">Confidence</th>
            <th scope="col">Proba Up</th>
            <th scope="col">Advisor Score</th>
            <th scope="col">Direction</th>
            <th scope="col">Explanation</th>
          </tr>
        </thead>
        <tbody>
          {recommendations.map((recommendation) => (
            <tr key={`${recommendation.date_id}-${recommendation.ticker}`}>
              <td data-label="Ticker">
                <strong className="ticker-cell">{recommendation.ticker}</strong>
              </td>
              <td data-label="Signal">
                <SignalBadge signal={recommendation.signal} />
              </td>
              <td data-label="Confidence">{recommendation.confidence ?? "N/A"}</td>
              <td data-label="Proba Up">{formatNumber(recommendation.proba_up)}</td>
              <td data-label="Advisor Score">{formatNumber(recommendation.advisor_score)}</td>
              <td data-label="Direction">{recommendation.predicted_direction ?? "N/A"}</td>
              <td data-label="Explanation" className="explanation-cell">
                {recommendation.explanation ?? "N/A"}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
