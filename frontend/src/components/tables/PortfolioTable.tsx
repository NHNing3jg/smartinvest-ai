import type { PortfolioAllocationRow } from "../../types/portfolio";
import SignalBadge from "../ui/SignalBadge";

type PortfolioTableProps = {
  rows: PortfolioAllocationRow[];
};

const formatNumber = (value: number | null | undefined, digits = 3) => {
  if (value === null || value === undefined || Number.isNaN(value)) {
    return "N/A";
  }

  return value.toFixed(digits);
};

const formatSignedPercent = (value: number | null | undefined) => {
  if (value === null || value === undefined || Number.isNaN(value)) {
    return "N/A";
  }

  const percentValue = value * 100;
  return `${percentValue > 0 ? "+" : ""}${percentValue.toFixed(2)}%`;
};

const formatPercent = (value: number | null | undefined) => {
  if (value === null || value === undefined || Number.isNaN(value)) {
    return "N/A";
  }

  const percentValue = Math.abs(value) <= 1 ? value * 100 : value;
  return `${percentValue.toFixed(2)}%`;
};

const formatWeight = (value: number | null | undefined) => {
  if (value === null || value === undefined || Number.isNaN(value)) {
    return "N/A";
  }

  const percentValue = Math.abs(value) <= 1 ? value * 100 : value;
  return `${percentValue.toFixed(2)}%`;
};

export default function PortfolioTable({ rows }: PortfolioTableProps) {
  if (rows.length === 0) {
    return (
      <div className="table-empty-state">
        <strong>No portfolio allocation available</strong>
        <span>The API returned an empty portfolio allocation.</span>
      </div>
    );
  }

  return (
    <div className="recommendation-table-wrap">
      <table className="recommendation-table portfolio-table">
        <thead>
          <tr>
            <th scope="col">Ticker</th>
            <th scope="col">Signal</th>
            <th scope="col">Confidence</th>
            <th scope="col">Proba Up</th>
            <th scope="col">Advisor Score</th>
            <th scope="col">Expected Return</th>
            <th scope="col">Risk Score</th>
            <th scope="col">Weight</th>
            <th scope="col">Explanation</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr key={row.ticker}>
              <td data-label="Ticker">
                <strong className="ticker-cell">{row.ticker}</strong>
              </td>
              <td data-label="Signal">
                <SignalBadge signal={row.signal} />
              </td>
              <td data-label="Confidence">{row.confidence ?? "N/A"}</td>
              <td data-label="Proba Up">{formatPercent(row.proba_up)}</td>
              <td data-label="Advisor Score">{formatNumber(row.advisor_score)}</td>
              <td data-label="Expected Return">{formatSignedPercent(row.expected_return)}</td>
              <td data-label="Risk Score">{formatNumber(row.risk_score)}</td>
              <td data-label="Weight">{formatWeight(row.weight)}</td>
              <td data-label="Explanation" className="explanation-cell">
                <span className="table-explanation-preview" title={row.explanation ?? undefined}>
                  {row.explanation ?? "N/A"}
                </span>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
