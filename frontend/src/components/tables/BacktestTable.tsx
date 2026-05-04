import SignalBadge from "../ui/SignalBadge";
import type { BacktestSummaryRow } from "../../types/backtest";

type BacktestTableProps = {
  rows: BacktestSummaryRow[];
};

const formatNumber = (value: number | null | undefined, digits = 3) => {
  if (value === null || value === undefined || Number.isNaN(value)) {
    return "N/A";
  }

  return value.toFixed(digits);
};

const formatWinRate = (value: number | null | undefined) => {
  if (value === null || value === undefined || Number.isNaN(value)) {
    return "N/A";
  }

  const percentValue = Math.abs(value) <= 1 ? value * 100 : value;
  return `${percentValue.toFixed(2)}%`;
};

const formatReturnPercent = (value: number | null | undefined) => {
  if (value === null || value === undefined || Number.isNaN(value)) {
    return "N/A";
  }

  const percentValue = value * 100;
  return `${percentValue > 0 ? "+" : ""}${percentValue.toFixed(2)}%`;
};

const formatCount = (value: number | null | undefined) => {
  if (value === null || value === undefined || Number.isNaN(value)) {
    return "N/A";
  }

  return value.toLocaleString();
};

export default function BacktestTable({ rows }: BacktestTableProps) {
  if (rows.length === 0) {
    return (
      <div className="table-empty-state">
        <strong>No backtest summary available</strong>
        <span>The API returned an empty backtest summary.</span>
      </div>
    );
  }

  return (
    <div className="recommendation-table-wrap">
      <table className="recommendation-table backtest-table">
        <thead>
          <tr>
            <th scope="col">Signal</th>
            <th scope="col">Obs</th>
            <th scope="col">Avg Next Return</th>
            <th scope="col">Median Return</th>
            <th scope="col">Win Rate</th>
            <th scope="col">Avg Proba Up</th>
            <th scope="col">Avg Score</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr key={row.signal}>
              <td data-label="Signal">
                <SignalBadge signal={row.signal} />
              </td>
              <td data-label="Obs">{formatCount(row.nb_obs)}</td>
              <td data-label="Avg Next Return">{formatReturnPercent(row.avg_next_return)}</td>
              <td data-label="Median Return">{formatReturnPercent(row.median_next_return)}</td>
              <td data-label="Win Rate">{formatWinRate(row.win_rate)}</td>
              <td data-label="Avg Proba Up">{formatNumber(row.avg_proba_up)}</td>
              <td data-label="Avg Score">{formatNumber(row.avg_advisor_score)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
