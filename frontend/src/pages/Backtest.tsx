import axios from "axios";
import {
  BarChart3,
  CalendarRange,
  CheckCircle2,
  Gauge,
  RefreshCw,
  Sigma,
  TrendingDown,
  TrendingUp,
} from "lucide-react";
import { useCallback, useEffect, useMemo, useState } from "react";

import { apiClient } from "../api/client";
import BacktestTable from "../components/tables/BacktestTable";
import ErrorMessage from "../components/ui/ErrorMessage";
import KpiCard from "../components/ui/KpiCard";
import Loader from "../components/ui/Loader";
import MetricBar from "../components/ui/MetricBar";
import SignalBadge from "../components/ui/SignalBadge";
import type { BacktestMetricRow, BacktestSignal, BacktestSummaryRow } from "../types/backtest";

const SIGNALS: BacktestSignal[] = ["BUY", "HOLD", "SELL"];

const isRecord = (value: unknown): value is Record<string, unknown> =>
  typeof value === "object" && value !== null && !Array.isArray(value);

const normalizeSignal = (value: unknown): BacktestSignal | null => {
  if (typeof value !== "string") {
    return null;
  }

  const normalized = value.toUpperCase();
  return SIGNALS.includes(normalized as BacktestSignal) ? (normalized as BacktestSignal) : null;
};

const parseNumber = (value: unknown): number | null => {
  if (typeof value === "number") {
    return Number.isFinite(value) ? value : null;
  }

  if (typeof value === "string" && value.trim() !== "") {
    const parsed = Number(value);
    return Number.isFinite(parsed) ? parsed : null;
  }

  return null;
};

const normalizeKey = (value: string) => value.toLowerCase().replace(/[^a-z0-9]+/g, "_");

const rowsFromPayload = (payload: unknown, nestedKeys: string[]): Record<string, unknown>[] => {
  if (Array.isArray(payload)) {
    return payload.filter(isRecord);
  }

  if (!isRecord(payload)) {
    return [];
  }

  for (const key of nestedKeys) {
    const nested = payload[key];
    if (Array.isArray(nested)) {
      return nested.filter(isRecord);
    }
  }

  const rows: Record<string, unknown>[] = [];

  for (const [key, value] of Object.entries(payload)) {
    if (isRecord(value)) {
      rows.push({ ...value, signal: value.signal ?? key });
    }
  }

  return rows;
};

const normalizeSummaryRows = (payload: unknown): BacktestSummaryRow[] =>
  rowsFromPayload(payload, ["summary", "data", "rows", "items"]).map((row) => ({
    ...row,
    signal: String(row.signal ?? "N/A"),
    nb_obs: parseNumber(row.nb_obs),
    avg_next_return: parseNumber(row.avg_next_return),
    median_next_return: parseNumber(row.median_next_return),
    win_rate: parseNumber(row.win_rate),
    avg_proba_up: parseNumber(row.avg_proba_up),
    avg_advisor_score: parseNumber(row.avg_advisor_score),
  }));

const normalizeMetricRows = (payload: unknown): BacktestMetricRow[] => {
  const rows = rowsFromPayload(payload, ["metrics", "data", "rows", "items"]);

  if (rows.length > 0) {
    return rows.map((row) => ({
      ...row,
      metric: typeof row.metric === "string" ? row.metric : undefined,
      signal: typeof row.signal === "string" ? row.signal : undefined,
      value: typeof row.value === "number" || typeof row.value === "string" ? row.value : undefined,
      win_rate: parseNumber(row.win_rate),
      avg_next_return: parseNumber(row.avg_next_return),
      nb_obs: parseNumber(row.nb_obs),
    }));
  }

  if (!isRecord(payload)) {
    return [];
  }

  return Object.entries(payload).map(([metric, value]) => ({ metric, value: parseNumber(value) ?? String(value) }));
};

const getErrorMessage = (error: unknown) => {
  if (axios.isAxiosError(error)) {
    if (!error.response) {
      return "Could not reach the FastAPI backend. Start it with python -m uvicorn app.main:app --reload, then refresh this page.";
    }

    const detail = error.response.data?.detail;
    if (typeof detail === "string") {
      return detail;
    }

    if (detail?.message) {
      return detail.message;
    }

    return `Backtest request failed with status ${error.response.status}.`;
  }

  return "Unable to load backtest data.";
};

const findSummaryRow = (rows: BacktestSummaryRow[], signal: BacktestSignal) =>
  rows.find((row) => normalizeSignal(row.signal) === signal);

const findMetricValue = (
  metrics: BacktestMetricRow[],
  signal: BacktestSignal,
  field: "win_rate" | "avg_next_return" | "nb_obs",
) => {
  const fieldKey = normalizeKey(field);
  const directMetric = metrics.find((metric) => normalizeSignal(metric.signal) === signal);
  const directValue = parseNumber(directMetric?.[field]);

  if (directValue !== null) {
    return directValue;
  }

  if (directMetric?.metric && normalizeKey(directMetric.metric).includes(fieldKey)) {
    const metricValue = parseNumber(directMetric.value);

    if (metricValue !== null) {
      return metricValue;
    }
  }

  const namedMetric = metrics.find((metric) => {
    if (!metric.metric) {
      return false;
    }

    const metricKey = normalizeKey(metric.metric);
    return metricKey.includes(signal.toLowerCase()) && metricKey.includes(fieldKey);
  });

  return parseNumber(namedMetric?.value);
};

const getSignalValue = (
  signal: BacktestSignal,
  field: "win_rate" | "avg_next_return" | "nb_obs",
  summaryRows: BacktestSummaryRow[],
  metrics: BacktestMetricRow[],
) => findMetricValue(metrics, signal, field) ?? parseNumber(findSummaryRow(summaryRows, signal)?.[field]);

const getTotalObservations = (summaryRows: BacktestSummaryRow[], metrics: BacktestMetricRow[]) => {
  const totalMetric = metrics.find((metric) => {
    if (!metric.metric) {
      return false;
    }

    const key = normalizeKey(metric.metric);
    return ["total_observations", "total_obs", "observations"].includes(key);
  });
  const metricValue = parseNumber(totalMetric?.value);

  if (metricValue !== null) {
    return metricValue;
  }

  const summaryValues = summaryRows.map((row) => parseNumber(row.nb_obs)).filter((value): value is number => value !== null);
  return summaryValues.length > 0 ? summaryValues.reduce((total, value) => total + value, 0) : null;
};

const formatCount = (value: number | null) => (value === null ? "N/A" : Math.round(value).toLocaleString());

const formatDecimal = (value: number | null, digits = 3) => {
  if (value === null || Number.isNaN(value)) {
    return "N/A";
  }

  return value.toFixed(digits);
};

const formatWinRate = (value: number | null) => {
  if (value === null || Number.isNaN(value)) {
    return "N/A";
  }

  const percentValue = Math.abs(value) <= 1 ? value * 100 : value;
  return `${percentValue.toFixed(2)}%`;
};

const formatSignedReturnPercent = (value: number | null) => {
  if (value === null || Number.isNaN(value)) {
    return "N/A";
  }

  const percentValue = value * 100;
  return `${percentValue > 0 ? "+" : ""}${percentValue.toFixed(2)}%`;
};

export default function Backtest() {
  const [summaryRows, setSummaryRows] = useState<BacktestSummaryRow[]>([]);
  const [metrics, setMetrics] = useState<BacktestMetricRow[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const fetchBacktest = useCallback(async () => {
    setIsLoading(true);
    setErrorMessage(null);

    try {
      const [summaryResponse, metricsResponse] = await Promise.all([
        apiClient.get<unknown>("/api/backtest/summary"),
        apiClient.get<unknown>("/api/backtest/metrics"),
      ]);

      setSummaryRows(normalizeSummaryRows(summaryResponse.data));
      setMetrics(normalizeMetricRows(metricsResponse.data));
    } catch (error) {
      setErrorMessage(getErrorMessage(error));
      setSummaryRows([]);
      setMetrics([]);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    void fetchBacktest();
  }, [fetchBacktest]);

  const signalMetrics = useMemo(
    () =>
      SIGNALS.map((signal) => ({
        signal,
        winRate: getSignalValue(signal, "win_rate", summaryRows, metrics),
        avgNextReturn: getSignalValue(signal, "avg_next_return", summaryRows, metrics),
        observations: getSignalValue(signal, "nb_obs", summaryRows, metrics),
      })),
    [metrics, summaryRows],
  );

  const totalObservations = useMemo(() => getTotalObservations(summaryRows, metrics), [metrics, summaryRows]);

  const bestSignal = signalMetrics
    .filter((metric) => metric.winRate !== null)
    .sort((left, right) => (right.winRate ?? 0) - (left.winRate ?? 0))[0];

  const winRateMax = signalMetrics.some((metric) => Math.abs(metric.winRate ?? 0) > 1) ? 100 : 1;
  const maxAbsReturn = Math.max(...signalMetrics.map((metric) => Math.abs(metric.avgNextReturn ?? 0)), 0.001);

  return (
    <section className="page-stack">
      <div className="page-hero hero-backtest">
        <div className="hero-copy">
          <span className="eyebrow">Backtest</span>
          <h1>Strategy Performance</h1>
          <p>Validate historical advisor signals with FastAPI-backed win rates, returns, and observation counts.</p>
        </div>
        <div className="hero-visual" aria-hidden="true">
          <div className="chart-steps">
            <span />
            <span />
            <span />
            <span />
          </div>
        </div>
      </div>

      <div className="toolbar-row">
        <button className="primary-button" type="button" onClick={() => void fetchBacktest()} disabled={isLoading}>
          <RefreshCw size={18} />
          Refresh Backtest
        </button>
      </div>

      {isLoading && (
        <div className="content-panel split-panel">
          <BarChart3 className="panel-icon" size={32} />
          <Loader label="Loading backtest data" />
        </div>
      )}

      {errorMessage && !isLoading && <ErrorMessage title="Backtest unavailable" message={errorMessage} />}

      {!isLoading && !errorMessage && (
        <>
          <div className="kpi-grid backtest-kpi-grid">
            <KpiCard title="BUY Win Rate" value={formatWinRate(signalMetrics[0].winRate)} detail="Historical BUY outcomes" icon={TrendingUp} />
            <KpiCard title="HOLD Win Rate" value={formatWinRate(signalMetrics[1].winRate)} detail="Historical HOLD outcomes" icon={Gauge} />
            <KpiCard title="SELL Win Rate" value={formatWinRate(signalMetrics[2].winRate)} detail="Historical SELL outcomes" icon={TrendingDown} />
            <KpiCard title="BUY Avg Next Return" value={formatSignedReturnPercent(signalMetrics[0].avgNextReturn)} detail="Mean next-day BUY return" icon={TrendingUp} />
            <KpiCard title="HOLD Avg Next Return" value={formatSignedReturnPercent(signalMetrics[1].avgNextReturn)} detail="Mean next-day HOLD return" icon={Gauge} />
            <KpiCard title="SELL Avg Next Return" value={formatSignedReturnPercent(signalMetrics[2].avgNextReturn)} detail="Mean next-day SELL return" icon={TrendingDown} />
            <KpiCard title="Total Observations" value={formatCount(totalObservations)} detail="Rows available from API data" icon={Sigma} />
          </div>

          <div className="backtest-chart-grid">
            <div className="content-panel metric-panel">
              <div className="panel-heading-row">
                <div>
                  <span className="eyebrow">Signal Validation</span>
                  <h2>Win Rate by Signal</h2>
                </div>
              </div>
              <div className="metric-bar-stack">
                {signalMetrics.map((metric) => (
                  <MetricBar
                    key={metric.signal}
                    signal={metric.signal}
                    label={metric.signal}
                    value={metric.winRate}
                    maxValue={winRateMax}
                    formatter={(value) => formatWinRate(value)}
                  />
                ))}
              </div>
            </div>

            <div className="content-panel metric-panel">
              <div className="panel-heading-row">
                <div>
                  <span className="eyebrow">Return Lens</span>
                  <h2>Average Next-Day Return by Signal</h2>
                </div>
              </div>
              <div className="metric-bar-stack">
                {signalMetrics.map((metric) => (
                  <MetricBar
                    key={metric.signal}
                    signal={metric.signal}
                    label={metric.signal}
                    value={metric.avgNextReturn}
                    maxValue={maxAbsReturn}
                    formatter={formatSignedReturnPercent}
                  />
                ))}
              </div>
            </div>
          </div>

          <div className="content-panel split-panel interpretation-panel">
            <CheckCircle2 className="panel-icon" size={32} />
            <div>
              <span className="eyebrow">Interpretation</span>
              <h2>What this backtest says</h2>
              <p>
                Backtesting validates historical recommendations by comparing each advisor signal with the next observed
                market outcome in the API data.
              </p>
              {bestSignal ? (
                <p>
                  The strongest historical signal by win rate is <SignalBadge signal={bestSignal.signal} /> with a win
                  rate of {formatWinRate(bestSignal.winRate)}.
                </p>
              ) : (
                <p>The API did not return enough win-rate data to identify a strongest historical signal.</p>
              )}
              <p>Historical performance does not guarantee future performance.</p>
            </div>
          </div>

          <div className="content-panel recommendation-panel">
            <div className="panel-heading-row">
              <div>
                <span className="eyebrow">FastAPI Data</span>
                <h2>Backtest Summary</h2>
              </div>
            </div>
            <BacktestTable rows={summaryRows} />
          </div>

          <div className="compact-panel">
            <CalendarRange size={20} />
            <span>Backtest data is loaded from /api/backtest/summary and /api/backtest/metrics.</span>
          </div>
        </>
      )}
    </section>
  );
}
