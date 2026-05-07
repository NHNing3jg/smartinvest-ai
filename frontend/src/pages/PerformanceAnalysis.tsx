import axios from "axios";
import { useCallback, useEffect, useMemo, useState } from "react";
import {
  Activity,
  BarChart3,
  CalendarDays,
  DatabaseZap,
  Gauge,
  LineChart as LineChartIcon,
  RefreshCw,
  Search,
  ShieldAlert,
  Sigma,
  Trophy,
  TrendingDown,
  TrendingUp,
  Waves,
} from "lucide-react";
import {
  Area,
  AreaChart,
  Bar,
  BarChart as RechartsBarChart,
  CartesianGrid,
  Cell,
  Legend,
  Line,
  LineChart as RechartsLineChart,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import { apiClient } from "../api/client";
import ErrorMessage from "../components/ui/ErrorMessage";
import KpiCard from "../components/ui/KpiCard";
import Loader from "../components/ui/Loader";
import type {
  PerformanceCompareRow,
  PerformanceCumulativeRow,
  PerformanceDailyRow,
  PerformanceRankingResponse,
  PerformanceRankingRow,
  PerformanceSummary,
} from "../types/performance";

type ComparisonChartPoint = {
  date: string;
  [ticker: string]: number | string | null;
};

type DailyReturnChartPoint = {
  date: string;
  daily_return_pct: number;
};

type DrawdownPoint = {
  date: string;
  drawdown_pct: number;
};

type RollingVolatilityPoint = {
  date: string;
  rolling_volatility_pct: number;
};

const DEFAULT_TABLE_LIMIT = 15;
const EXPANDED_TABLE_LIMIT = 50;
const PERFORMANCE_POINT_LIMIT = 320;
const DAILY_POINT_LIMIT = 240;
const MAX_COMPARISON_TICKERS = 4;
const CHART_COLORS = ["#277dff", "#12d6c5", "#ff5da2", "#a88bff", "#ffd86b"];

const isRecord = (value: unknown): value is Record<string, unknown> =>
  typeof value === "object" && value !== null && !Array.isArray(value);

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

const parseText = (value: unknown): string | null => {
  if (typeof value !== "string") {
    return null;
  }

  const trimmed = value.trim();
  return trimmed === "" ? null : trimmed;
};

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

  return [];
};

const normalizeTickers = (payload: unknown) => {
  if (Array.isArray(payload)) {
    return payload.map((ticker) => parseText(ticker)).filter((ticker): ticker is string => ticker !== null);
  }

  if (!isRecord(payload) || !Array.isArray(payload.tickers)) {
    return [];
  }

  return payload.tickers.map((ticker) => parseText(ticker)).filter((ticker): ticker is string => ticker !== null);
};

const normalizeDailyRows = (payload: unknown): PerformanceDailyRow[] =>
  rowsFromPayload(payload, ["data", "rows", "items"]).map((row) => ({
    date_id: parseText(row.date_id) ?? "N/A",
    ticker: parseText(row.ticker) ?? "N/A",
    close: parseNumber(row.close),
    close_prev: parseNumber(row.close_prev),
    daily_return: parseNumber(row.daily_return),
    daily_return_pct: parseNumber(row.daily_return_pct),
  }));

const normalizeCumulativeRows = (payload: unknown): PerformanceCumulativeRow[] =>
  rowsFromPayload(payload, ["data", "rows", "items"]).map((row) => ({
    date_id: parseText(row.date_id) ?? "N/A",
    ticker: parseText(row.ticker) ?? "N/A",
    daily_return: parseNumber(row.daily_return),
    cumulative_return_pct: parseNumber(row.cumulative_return_pct),
  }));

const normalizeCompareRows = (payload: unknown): PerformanceCompareRow[] =>
  rowsFromPayload(payload, ["data", "rows", "items"]).map((row) => ({
    date_id: parseText(row.date_id) ?? "N/A",
    ticker: parseText(row.ticker) ?? "N/A",
    cumulative_return_pct: parseNumber(row.cumulative_return_pct),
  }));

const normalizeSummary = (payload: unknown): PerformanceSummary | null => {
  if (!isRecord(payload)) {
    return null;
  }

  return {
    ticker: parseText(payload.ticker) ?? "N/A",
    start_date: parseText(payload.start_date),
    end_date: parseText(payload.end_date),
    observations: parseNumber(payload.observations),
    start_close: parseNumber(payload.start_close),
    last_close: parseNumber(payload.last_close),
    cumulative_return_pct: parseNumber(payload.cumulative_return_pct),
    annualized_return_pct: parseNumber(payload.annualized_return_pct),
    annualized_volatility_pct: parseNumber(payload.annualized_volatility_pct),
    sharpe_ratio: parseNumber(payload.sharpe_ratio),
    max_drawdown_pct: parseNumber(payload.max_drawdown_pct),
    win_rate_pct: parseNumber(payload.win_rate_pct),
    best_daily_return_pct: parseNumber(payload.best_daily_return_pct),
    worst_daily_return_pct: parseNumber(payload.worst_daily_return_pct),
    average_daily_return_pct: parseNumber(payload.average_daily_return_pct),
  };
};

const normalizeRankingRow = (row: Record<string, unknown>): PerformanceRankingRow => ({
  ticker: parseText(row.ticker) ?? "N/A",
  start_date: parseText(row.start_date),
  end_date: parseText(row.end_date),
  cumulative_return_pct: parseNumber(row.cumulative_return_pct),
});

const normalizeRanking = (payload: unknown): PerformanceRankingResponse => {
  if (!isRecord(payload)) {
    return { top: [], worst: [] };
  }

  const top = Array.isArray(payload.top) ? payload.top.filter(isRecord).map(normalizeRankingRow) : [];
  const worst = Array.isArray(payload.worst) ? payload.worst.filter(isRecord).map(normalizeRankingRow) : [];

  return { top, worst };
};

const buildQueryParams = (ticker: string, startDate: string, endDate: string) => ({
  ticker,
  ...(startDate.trim() ? { start_date: startDate.trim() } : {}),
  ...(endDate.trim() ? { end_date: endDate.trim() } : {}),
});

const buildCompareQueryParams = (tickers: string[], startDate: string, endDate: string) => ({
  tickers: tickers.join(","),
  ...(startDate.trim() ? { start_date: startDate.trim() } : {}),
  ...(endDate.trim() ? { end_date: endDate.trim() } : {}),
});

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

    return `Performance request failed with status ${error.response.status}.`;
  }

  return "Unable to load performance data.";
};

const formatPercent = (value: number | null, options?: { signed?: boolean }) => {
  if (value === null || !Number.isFinite(value)) {
    return "N/A";
  }

  const sign = options?.signed !== false && value > 0 ? "+" : "";
  return `${sign}${value.toFixed(2)}%`;
};

const formatNumber = (value: number | null, fractionDigits = 2) => {
  if (value === null || !Number.isFinite(value)) {
    return "N/A";
  }

  return value.toLocaleString(undefined, {
    minimumFractionDigits: fractionDigits,
    maximumFractionDigits: fractionDigits,
  });
};

const formatPrice = (value: number | null) => formatNumber(value, 2);

const formatCount = (value: number | null) => {
  if (value === null || !Number.isFinite(value)) {
    return "N/A";
  }

  return Math.round(value).toLocaleString();
};

const formatDateLabel = (value: string | null | undefined) => {
  if (!value || value === "N/A") {
    return "N/A";
  }

  const parsedDate = new Date(value);
  if (Number.isNaN(parsedDate.getTime())) {
    return value;
  }

  return parsedDate.toLocaleDateString(undefined, {
    month: "short",
    day: "numeric",
    year: "2-digit",
  });
};

const isPositive = (value: number | null | undefined) => typeof value === "number" && Number.isFinite(value) && value >= 0;

const sortDailyRowsDesc = (rows: PerformanceDailyRow[]) =>
  [...rows].sort((left, right) => right.date_id.localeCompare(left.date_id));

const sortDailyRowsAsc = (rows: PerformanceDailyRow[]) =>
  [...rows].sort((left, right) => left.date_id.localeCompare(right.date_id));

const sortCumulativeRowsAsc = (rows: PerformanceCumulativeRow[]) =>
  [...rows].sort((left, right) => left.date_id.localeCompare(right.date_id));

const downsampleRows = <T,>(rows: T[], maxPoints: number) => {
  if (rows.length <= maxPoints) {
    return rows;
  }

  if (maxPoints <= 1) {
    return rows.slice(0, 1);
  }

  const step = (rows.length - 1) / (maxPoints - 1);
  const sampledRows: T[] = [];

  for (let index = 0; index < maxPoints; index += 1) {
    const row = rows[Math.round(index * step)];

    if (row !== undefined) {
      sampledRows.push(row);
    }
  }

  return sampledRows;
};

const buildSingleTickerChartData = (rows: PerformanceCumulativeRow[], ticker: string): ComparisonChartPoint[] =>
  sortCumulativeRowsAsc(rows)
    .map((row) => ({
      date: row.date_id,
      [ticker]: row.cumulative_return_pct,
    }))
    .filter((row) => typeof row[ticker] === "number" && Number.isFinite(row[ticker] as number));

const buildComparisonChartData = (rows: PerformanceCompareRow[]): ComparisonChartPoint[] => {
  const dataByDate = new Map<string, ComparisonChartPoint>();

  [...rows]
    .sort((left, right) => left.date_id.localeCompare(right.date_id))
    .forEach((row) => {
      if (row.cumulative_return_pct === null || !Number.isFinite(row.cumulative_return_pct)) {
        return;
      }

      const point = dataByDate.get(row.date_id) ?? { date: row.date_id };
      point[row.ticker] = row.cumulative_return_pct;
      dataByDate.set(row.date_id, point);
    });

  return Array.from(dataByDate.values());
};

const computeDrawdownSeries = (rows: PerformanceCumulativeRow[]): DrawdownPoint[] => {
  let runningPeak = 1;

  return sortCumulativeRowsAsc(rows)
    .map((row) => {
      if (row.cumulative_return_pct === null || !Number.isFinite(row.cumulative_return_pct)) {
        return null;
      }

      const wealth = 1 + row.cumulative_return_pct / 100;
      runningPeak = Math.max(runningPeak, wealth);
      const drawdownPct = (wealth / runningPeak - 1) * 100;

      return {
        date: row.date_id,
        drawdown_pct: Math.min(0, drawdownPct),
      };
    })
    .filter((row): row is DrawdownPoint => row !== null);
};

const computeRollingVolatility = (rows: PerformanceDailyRow[], windowSize = 30): RollingVolatilityPoint[] => {
  const sortedRows = sortDailyRowsAsc(rows).filter(
    (row) => row.daily_return !== null && Number.isFinite(row.daily_return),
  );

  return sortedRows
    .map((row, index) => {
      if (index + 1 < windowSize) {
        return null;
      }

      const windowValues = sortedRows
        .slice(index + 1 - windowSize, index + 1)
        .map((windowRow) => windowRow.daily_return)
        .filter((value): value is number => value !== null && Number.isFinite(value));

      if (windowValues.length < windowSize) {
        return null;
      }

      const mean = windowValues.reduce((total, value) => total + value, 0) / windowValues.length;
      const variance =
        windowValues.reduce((total, value) => total + (value - mean) ** 2, 0) / (windowValues.length - 1);

      return {
        date: row.date_id,
        rolling_volatility_pct: Math.sqrt(variance) * Math.sqrt(252) * 100,
      };
    })
    .filter((row): row is RollingVolatilityPoint => row !== null);
};

const buildDailyReturnChartData = (rows: PerformanceDailyRow[]): DailyReturnChartPoint[] =>
  sortDailyRowsAsc(rows)
    .map((row) => ({
      date: row.date_id,
      daily_return_pct: row.daily_return_pct,
    }))
    .filter(
      (row): row is DailyReturnChartPoint =>
        row.daily_return_pct !== null && Number.isFinite(row.daily_return_pct),
    );

const getLatestRows = (rows: PerformanceDailyRow[], limit: number) => sortDailyRowsDesc(rows).slice(0, limit);

const getPerformanceClass = (value: number | null | undefined) =>
  isPositive(value) ? "performance-value-positive" : "performance-value-negative";

export default function PerformanceAnalysis() {
  const [tickers, setTickers] = useState<string[]>([]);
  const [selectedTicker, setSelectedTicker] = useState("");
  const [comparisonTickers, setComparisonTickers] = useState<string[]>([]);
  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");
  const [summary, setSummary] = useState<PerformanceSummary | null>(null);
  const [dailyRows, setDailyRows] = useState<PerformanceDailyRow[]>([]);
  const [cumulativeRows, setCumulativeRows] = useState<PerformanceCumulativeRow[]>([]);
  const [ranking, setRanking] = useState<PerformanceRankingResponse>({ top: [], worst: [] });
  const [compareRows, setCompareRows] = useState<PerformanceCompareRow[]>([]);
  const [isTickerLoading, setIsTickerLoading] = useState(true);
  const [isPerformanceLoading, setIsPerformanceLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [isTableExpanded, setIsTableExpanded] = useState(false);

  const selectedTickerGroup = useMemo(
    () => [selectedTicker, ...comparisonTickers].filter((ticker): ticker is string => Boolean(ticker)),
    [comparisonTickers, selectedTicker],
  );

  const fetchTickers = useCallback(async () => {
    setIsTickerLoading(true);
    setErrorMessage(null);

    try {
      const response = await apiClient.get<unknown>("/api/performance/tickers");
      const tickerList = normalizeTickers(response.data);
      const defaultTicker = tickerList.includes("AAPL") ? "AAPL" : tickerList[0] ?? "";

      setTickers(tickerList);
      setSelectedTicker((currentTicker) => (tickerList.includes(currentTicker) ? currentTicker : defaultTicker));
      setComparisonTickers((currentTickers) =>
        currentTickers.filter((ticker) => ticker !== defaultTicker && tickerList.includes(ticker)),
      );
    } catch (error) {
      setErrorMessage(getErrorMessage(error));
      setTickers([]);
      setSelectedTicker("");
      setComparisonTickers([]);
      setSummary(null);
      setDailyRows([]);
      setCumulativeRows([]);
      setRanking({ top: [], worst: [] });
      setCompareRows([]);
    } finally {
      setIsTickerLoading(false);
    }
  }, []);

  const fetchPerformanceData = useCallback(async () => {
    if (!selectedTicker) {
      return;
    }

    setIsPerformanceLoading(true);
    setErrorMessage(null);

    const params = buildQueryParams(selectedTicker, startDate, endDate);
    const compareTickers = [selectedTicker, ...comparisonTickers];

    try {
      const [summaryResponse, dailyResponse, cumulativeResponse, rankingResponse, compareResponse] = await Promise.all([
        apiClient.get<unknown>("/api/performance/summary", { params }),
        apiClient.get<unknown>("/api/performance/daily", { params }),
        apiClient.get<unknown>("/api/performance/cumulative", { params }),
        apiClient.get<unknown>("/api/performance/ranking"),
        comparisonTickers.length > 0
          ? apiClient.get<unknown>("/api/performance/compare", {
              params: buildCompareQueryParams(compareTickers, startDate, endDate),
            })
          : Promise.resolve({ data: [] as unknown }),
      ]);

      setSummary(normalizeSummary(summaryResponse.data));
      setDailyRows(normalizeDailyRows(dailyResponse.data));
      setCumulativeRows(normalizeCumulativeRows(cumulativeResponse.data));
      setRanking(normalizeRanking(rankingResponse.data));
      setCompareRows(comparisonTickers.length > 0 ? normalizeCompareRows(compareResponse.data) : []);
      setIsTableExpanded(false);
    } catch (error) {
      setErrorMessage(getErrorMessage(error));
      setSummary(null);
      setDailyRows([]);
      setCumulativeRows([]);
      setRanking({ top: [], worst: [] });
      setCompareRows([]);
    } finally {
      setIsPerformanceLoading(false);
    }
  }, [comparisonTickers, endDate, selectedTicker, startDate]);

  useEffect(() => {
    void fetchTickers();
  }, [fetchTickers]);

  useEffect(() => {
    void fetchPerformanceData();
  }, [fetchPerformanceData]);

  const isLoading = isTickerLoading || isPerformanceLoading;
  const tableLimit = isTableExpanded ? EXPANDED_TABLE_LIMIT : DEFAULT_TABLE_LIMIT;
  const tableRows = useMemo(() => getLatestRows(dailyRows, tableLimit), [dailyRows, tableLimit]);
  const canToggleTable = dailyRows.length > DEFAULT_TABLE_LIMIT;
  const comparisonOptions = useMemo(() => tickers.filter((ticker) => ticker !== selectedTicker), [selectedTicker, tickers]);

  const comparisonChartData = useMemo(() => {
    const rawData =
      comparisonTickers.length > 0
        ? buildComparisonChartData(compareRows)
        : buildSingleTickerChartData(cumulativeRows, selectedTicker);

    return downsampleRows(rawData, PERFORMANCE_POINT_LIMIT);
  }, [compareRows, comparisonTickers.length, cumulativeRows, selectedTicker]);

  const dailyReturnChartData = useMemo(
    () => downsampleRows(buildDailyReturnChartData(dailyRows), DAILY_POINT_LIMIT),
    [dailyRows],
  );
  const drawdownSeries = useMemo(
    () => downsampleRows(computeDrawdownSeries(cumulativeRows), PERFORMANCE_POINT_LIMIT),
    [cumulativeRows],
  );
  const rollingVolatilitySeries = useMemo(
    () => downsampleRows(computeRollingVolatility(dailyRows), PERFORMANCE_POINT_LIMIT),
    [dailyRows],
  );

  const sortedTopRanking = useMemo(
    () =>
      [...ranking.top]
        .sort((left, right) => (right.cumulative_return_pct ?? -Infinity) - (left.cumulative_return_pct ?? -Infinity))
        .slice(0, 5),
    [ranking.top],
  );
  const sortedWorstRanking = useMemo(
    () =>
      [...ranking.worst]
        .sort((left, right) => (left.cumulative_return_pct ?? Infinity) - (right.cumulative_return_pct ?? Infinity))
        .slice(0, 5),
    [ranking.worst],
  );
  const rankingMaxAbs = useMemo(() => {
    const values = [...sortedTopRanking, ...sortedWorstRanking]
      .map((row) => row.cumulative_return_pct)
      .filter((value): value is number => value !== null && Number.isFinite(value))
      .map((value) => Math.abs(value));

    return Math.max(...values, 1);
  }, [sortedTopRanking, sortedWorstRanking]);

  const toggleComparisonTicker = (ticker: string) => {
    setComparisonTickers((currentTickers) => {
      if (currentTickers.includes(ticker)) {
        return currentTickers.filter((currentTicker) => currentTicker !== ticker);
      }

      if (currentTickers.length >= MAX_COMPARISON_TICKERS) {
        return currentTickers;
      }

      return [...currentTickers, ticker];
    });
  };

  return (
    <section className="page-stack">
      <div className="page-hero hero-performance">
        <div className="hero-copy">
          <span className="eyebrow">Performance Analysis</span>
          <h1>Historical Asset Performance</h1>
          <p>Evaluate returns, volatility, drawdown, and ranking patterns through the FastAPI performance layer.</p>
        </div>
        <div className="hero-visual" aria-hidden="true">
          <div className="performance-hero-lines">
            <span />
            <span />
            <span />
            <span />
          </div>
          <div className="hero-card hero-card-secondary">
            <span>Selected Asset</span>
            <strong>{selectedTicker || "Loading"}</strong>
          </div>
        </div>
      </div>

      <div className="content-panel performance-filter-panel">
        <div className="panel-heading-row">
          <div>
            <span className="eyebrow">Filters</span>
            <h2>Performance Data Controls</h2>
          </div>
          <Search size={22} />
        </div>

        <div className="performance-filter-grid">
          <label className="advisor-filter-field">
            <span>Main Asset</span>
            <select
              value={selectedTicker}
              onChange={(event) => {
                setSelectedTicker(event.target.value);
                setComparisonTickers((currentTickers) =>
                  currentTickers.filter((ticker) => ticker !== event.target.value),
                );
              }}
              disabled={isTickerLoading || tickers.length === 0}
            >
              {tickers.length === 0 ? (
                <option value="">No tickers</option>
              ) : (
                tickers.map((ticker) => (
                  <option key={ticker} value={ticker}>
                    {ticker}
                  </option>
                ))
              )}
            </select>
          </label>

          <label className="advisor-filter-field">
            <span>Start Date</span>
            <input type="date" value={startDate} onChange={(event) => setStartDate(event.target.value)} />
          </label>

          <label className="advisor-filter-field">
            <span>End Date</span>
            <input type="date" value={endDate} onChange={(event) => setEndDate(event.target.value)} />
          </label>

          <div className="performance-filter-actions">
            <button
              className="primary-button"
              type="button"
              onClick={() => void fetchPerformanceData()}
              disabled={isLoading || !selectedTicker}
            >
              <RefreshCw size={18} />
              Refresh Performance
            </button>
            <button
              className="secondary-button"
              type="button"
              onClick={() => {
                setStartDate("");
                setEndDate("");
              }}
              disabled={isLoading || (!startDate && !endDate)}
            >
              Clear Dates
            </button>
          </div>
        </div>

        <div className="performance-comparison-panel" aria-label="Comparison basket">
          <div>
            <span className="eyebrow">Comparison Basket</span>
            <p>Select up to {MAX_COMPARISON_TICKERS} additional tickers for the cumulative performance chart.</p>
          </div>
          <div className="performance-ticker-pills">
            {comparisonOptions.slice(0, 18).map((ticker) => {
              const isSelected = comparisonTickers.includes(ticker);
              const isDisabled = !isSelected && comparisonTickers.length >= MAX_COMPARISON_TICKERS;

              return (
                <button
                  key={ticker}
                  className={isSelected ? "ticker-pill selected" : "ticker-pill"}
                  type="button"
                  onClick={() => toggleComparisonTicker(ticker)}
                  disabled={isDisabled}
                  aria-pressed={isSelected}
                >
                  {ticker}
                </button>
              );
            })}
          </div>
        </div>
      </div>

      {isLoading && (
        <div className="content-panel split-panel">
          <LineChartIcon className="panel-icon" size={32} />
          <Loader label="Loading performance data" />
        </div>
      )}

      {errorMessage && !isLoading && <ErrorMessage title="Performance data unavailable" message={errorMessage} />}

      {!isLoading && !errorMessage && (
        <>
          <div className="kpi-grid performance-kpi-grid">
            <KpiCard
              title="Cumulative Return"
              value={formatPercent(summary?.cumulative_return_pct ?? null)}
              detail={`${formatDateLabel(summary?.start_date)} to ${formatDateLabel(summary?.end_date)}`}
              icon={TrendingUp}
            />
            <KpiCard
              title="Annualized Return"
              value={formatPercent(summary?.annualized_return_pct ?? null)}
              detail="Annualized performance over the selected period"
              icon={LineChartIcon}
            />
            <KpiCard
              title="Volatility"
              value={formatPercent(summary?.annualized_volatility_pct ?? null, { signed: false })}
              detail="Annualized volatility returned by FastAPI"
              icon={Waves}
            />
            <KpiCard
              title="Sharpe Ratio"
              value={formatNumber(summary?.sharpe_ratio ?? null, 2)}
              detail="Risk-adjusted return ratio"
              icon={Sigma}
            />
            <KpiCard
              title="Max Drawdown"
              value={formatPercent(summary?.max_drawdown_pct ?? null)}
              detail="Largest peak-to-trough decline"
              icon={TrendingDown}
            />
            <KpiCard
              title="Win Rate"
              value={formatPercent(summary?.win_rate_pct ?? null, { signed: false })}
              detail="Share of positive daily return rows"
              icon={Gauge}
            />
            <KpiCard
              title="Best Daily Return"
              value={formatPercent(summary?.best_daily_return_pct ?? null)}
              detail={`Average daily return ${formatPercent(summary?.average_daily_return_pct ?? null)}`}
              icon={Trophy}
            />
            <KpiCard
              title="Worst Daily Return"
              value={formatPercent(summary?.worst_daily_return_pct ?? null)}
              detail="Lowest daily return in selected period"
              icon={ShieldAlert}
            />
            <KpiCard
              title="Observations"
              value={formatCount(summary?.observations ?? null)}
              detail={`${formatPrice(summary?.start_close ?? null)} start close, ${formatPrice(summary?.last_close ?? null)} last close`}
              icon={CalendarDays}
            />
          </div>

          <div className="performance-chart-grid">
            <div className="content-panel performance-line-panel">
              <div className="panel-heading-row">
                <div>
                  <span className="eyebrow">Cumulative Performance</span>
                  <h2>Cumulative Return by Ticker</h2>
                  <p className="performance-chart-helper">
                    {comparisonTickers.length > 0
                      ? "Using the compare endpoint for the selected basket."
                      : "Using the cumulative endpoint for the selected asset."}
                  </p>
                </div>
              </div>

              {comparisonChartData.length > 0 ? (
                <div className="performance-recharts-card">
                  <div className="performance-recharts-box performance-recharts-box-large">
                    <ResponsiveContainer width="100%" height="100%">
                      <RechartsLineChart
                        data={comparisonChartData}
                        margin={{ top: 18, right: 24, left: 8, bottom: 12 }}
                      >
                        <CartesianGrid stroke="rgba(83, 98, 123, 0.18)" strokeDasharray="3 4" vertical={false} />
                        <XAxis
                          dataKey="date"
                          minTickGap={30}
                          tickFormatter={formatDateLabel}
                          tick={{ fill: "#66738c", fontSize: 12, fontWeight: 700 }}
                          axisLine={{ stroke: "rgba(83, 98, 123, 0.22)" }}
                          tickLine={false}
                        />
                        <YAxis
                          width={74}
                          tickFormatter={(value) => formatPercent(Number(value))}
                          tick={{ fill: "#66738c", fontSize: 12, fontWeight: 700 }}
                          axisLine={false}
                          tickLine={false}
                        />
                        <Tooltip
                          cursor={{ stroke: "rgba(39, 125, 255, 0.24)", strokeWidth: 1 }}
                          contentStyle={{
                            border: "1px solid rgba(255, 255, 255, 0.82)",
                            borderRadius: 8,
                            background: "rgba(255, 255, 255, 0.94)",
                            boxShadow: "0 18px 36px rgba(47, 64, 101, 0.14)",
                          }}
                          formatter={(value, name) => [formatPercent(Number(value)), String(name)]}
                          labelFormatter={(label) => `Date: ${formatDateLabel(String(label))}`}
                        />
                        <Legend wrapperStyle={{ color: "#53627b", fontWeight: 800, paddingTop: 8 }} />
                        <ReferenceLine y={0} stroke="#53627b" strokeDasharray="4 5" />
                        {selectedTickerGroup.map((ticker, index) => (
                          <Line
                            key={ticker}
                            type="monotone"
                            dataKey={ticker}
                            name={ticker}
                            stroke={CHART_COLORS[index % CHART_COLORS.length]}
                            strokeWidth={ticker === selectedTicker ? 3.1 : 2.15}
                            dot={false}
                            connectNulls
                            activeDot={{ r: ticker === selectedTicker ? 5 : 4, strokeWidth: 2, stroke: "#ffffff" }}
                          />
                        ))}
                      </RechartsLineChart>
                    </ResponsiveContainer>
                  </div>
                  <div className="performance-chart-caption">
                    <span>{formatDateLabel(comparisonChartData[0]?.date as string | undefined)}</span>
                    <strong>{selectedTickerGroup.join(" vs ")}</strong>
                    <span>{formatDateLabel(comparisonChartData[comparisonChartData.length - 1]?.date as string | undefined)}</span>
                  </div>
                </div>
              ) : (
                <div className="table-empty-state">
                  <strong>No cumulative performance available</strong>
                  <span>The API returned no numeric cumulative return rows for this selection.</span>
                </div>
              )}
            </div>

            <div className="content-panel performance-daily-panel">
              <div className="panel-heading-row">
                <div>
                  <span className="eyebrow">Daily Returns</span>
                  <h2>Daily Return Distribution Over Time</h2>
                </div>
              </div>
              {dailyReturnChartData.length > 0 ? (
                <div className="performance-recharts-card performance-recharts-card-compact">
                  <div className="performance-recharts-box">
                    <ResponsiveContainer width="100%" height="100%">
                      <RechartsBarChart data={dailyReturnChartData} margin={{ top: 16, right: 18, left: 4, bottom: 8 }}>
                        <CartesianGrid stroke="rgba(83, 98, 123, 0.16)" strokeDasharray="3 4" vertical={false} />
                        <XAxis
                          dataKey="date"
                          minTickGap={28}
                          tickFormatter={formatDateLabel}
                          tick={{ fill: "#66738c", fontSize: 12, fontWeight: 700 }}
                          axisLine={{ stroke: "rgba(83, 98, 123, 0.22)" }}
                          tickLine={false}
                        />
                        <YAxis
                          width={68}
                          tickFormatter={(value) => formatPercent(Number(value))}
                          tick={{ fill: "#66738c", fontSize: 12, fontWeight: 700 }}
                          axisLine={false}
                          tickLine={false}
                        />
                        <Tooltip
                          cursor={{ fill: "rgba(18, 214, 197, 0.08)" }}
                          contentStyle={{
                            border: "1px solid rgba(255, 255, 255, 0.82)",
                            borderRadius: 8,
                            background: "rgba(255, 255, 255, 0.94)",
                            boxShadow: "0 18px 36px rgba(47, 64, 101, 0.14)",
                          }}
                          formatter={(value) => [formatPercent(Number(value)), "Daily return"]}
                          labelFormatter={(label) => `Date: ${formatDateLabel(String(label))}`}
                        />
                        <ReferenceLine y={0} stroke="#53627b" strokeDasharray="4 5" />
                        <Bar dataKey="daily_return_pct" name="Daily return" radius={[4, 4, 0, 0]} maxBarSize={12}>
                          {dailyReturnChartData.map((row) => (
                            <Cell
                              key={row.date}
                              fill={row.daily_return_pct >= 0 ? "rgba(18, 214, 197, 0.86)" : "rgba(255, 123, 123, 0.88)"}
                            />
                          ))}
                        </Bar>
                      </RechartsBarChart>
                    </ResponsiveContainer>
                  </div>
                </div>
              ) : (
                <div className="table-empty-state">
                  <strong>No daily returns available</strong>
                  <span>The API returned no daily return percentages for this selection.</span>
                </div>
              )}
            </div>

            <div className="content-panel performance-risk-panel">
              <div className="panel-heading-row">
                <div>
                  <span className="eyebrow">Drawdown</span>
                  <h2>Derived Drawdown Series</h2>
                </div>
              </div>
              {drawdownSeries.length > 0 ? (
                <div className="performance-recharts-card performance-recharts-card-compact">
                  <div className="performance-recharts-box">
                    <ResponsiveContainer width="100%" height="100%">
                      <AreaChart data={drawdownSeries} margin={{ top: 16, right: 18, left: 4, bottom: 8 }}>
                        <CartesianGrid stroke="rgba(83, 98, 123, 0.16)" strokeDasharray="3 4" vertical={false} />
                        <XAxis
                          dataKey="date"
                          minTickGap={28}
                          tickFormatter={formatDateLabel}
                          tick={{ fill: "#66738c", fontSize: 12, fontWeight: 700 }}
                          axisLine={{ stroke: "rgba(83, 98, 123, 0.22)" }}
                          tickLine={false}
                        />
                        <YAxis
                          width={68}
                          tickFormatter={(value) => formatPercent(Number(value))}
                          tick={{ fill: "#66738c", fontSize: 12, fontWeight: 700 }}
                          axisLine={false}
                          tickLine={false}
                        />
                        <Tooltip
                          cursor={{ stroke: "rgba(255, 93, 162, 0.2)", strokeWidth: 1 }}
                          contentStyle={{
                            border: "1px solid rgba(255, 255, 255, 0.82)",
                            borderRadius: 8,
                            background: "rgba(255, 255, 255, 0.94)",
                            boxShadow: "0 18px 36px rgba(47, 64, 101, 0.14)",
                          }}
                          formatter={(value) => [formatPercent(Number(value)), "Drawdown"]}
                          labelFormatter={(label) => `Date: ${formatDateLabel(String(label))}`}
                        />
                        <ReferenceLine y={0} stroke="#53627b" strokeDasharray="4 5" />
                        <Area
                          type="monotone"
                          dataKey="drawdown_pct"
                          name="Drawdown"
                          stroke="#ff5da2"
                          fill="rgba(255, 93, 162, 0.18)"
                          strokeWidth={2.35}
                          dot={false}
                        />
                      </AreaChart>
                    </ResponsiveContainer>
                  </div>
                </div>
              ) : (
                <div className="table-empty-state">
                  <strong>No drawdown series available</strong>
                  <span>Cumulative return rows are needed to derive drawdown.</span>
                </div>
              )}
            </div>

            <div className="content-panel performance-volatility-panel performance-wide-card">
              <div className="panel-heading-row">
                <div>
                  <span className="eyebrow">Rolling Risk</span>
                  <h2>30-Day Rolling Volatility</h2>
                </div>
              </div>
              {rollingVolatilitySeries.length > 0 ? (
                <div className="performance-recharts-card performance-recharts-card-compact">
                  <div className="performance-recharts-box performance-recharts-box-wide">
                    <ResponsiveContainer width="100%" height="100%">
                      <AreaChart data={rollingVolatilitySeries} margin={{ top: 16, right: 18, left: 4, bottom: 8 }}>
                        <CartesianGrid stroke="rgba(83, 98, 123, 0.16)" strokeDasharray="3 4" vertical={false} />
                        <XAxis
                          dataKey="date"
                          minTickGap={28}
                          tickFormatter={formatDateLabel}
                          tick={{ fill: "#66738c", fontSize: 12, fontWeight: 700 }}
                          axisLine={{ stroke: "rgba(83, 98, 123, 0.22)" }}
                          tickLine={false}
                        />
                        <YAxis
                          width={68}
                          tickFormatter={(value) => formatPercent(Number(value), { signed: false })}
                          tick={{ fill: "#66738c", fontSize: 12, fontWeight: 700 }}
                          axisLine={false}
                          tickLine={false}
                        />
                        <Tooltip
                          cursor={{ stroke: "rgba(168, 139, 255, 0.22)", strokeWidth: 1 }}
                          contentStyle={{
                            border: "1px solid rgba(255, 255, 255, 0.82)",
                            borderRadius: 8,
                            background: "rgba(255, 255, 255, 0.94)",
                            boxShadow: "0 18px 36px rgba(47, 64, 101, 0.14)",
                          }}
                          formatter={(value) => [formatPercent(Number(value), { signed: false }), "Rolling volatility"]}
                          labelFormatter={(label) => `Date: ${formatDateLabel(String(label))}`}
                        />
                        <Area
                          type="monotone"
                          dataKey="rolling_volatility_pct"
                          name="30-day rolling volatility"
                          stroke="#a88bff"
                          fill="rgba(168, 139, 255, 0.2)"
                          strokeWidth={2.35}
                          dot={false}
                        />
                      </AreaChart>
                    </ResponsiveContainer>
                  </div>
                </div>
              ) : (
                <div className="table-empty-state">
                  <strong>No rolling volatility available</strong>
                  <span>At least 30 daily return rows are needed for the rolling calculation.</span>
                </div>
              )}
            </div>
          </div>

          <div className="performance-ranking-grid">
            <div className="content-panel performance-ranking-panel">
              <div className="panel-heading-row">
                <div>
                  <span className="eyebrow">Ranking</span>
                  <h2>Top Performers</h2>
                </div>
                <Trophy size={22} />
              </div>
              <div className="performance-ranking-list">
                {sortedTopRanking.length > 0 ? (
                  sortedTopRanking.map((row, index) => (
                    <div className="performance-ranking-row" key={`top-${row.ticker}`}>
                      <span className="ranking-index">{index + 1}</span>
                      <strong>{row.ticker}</strong>
                      <div className="ranking-track">
                        <span
                          className="ranking-fill ranking-fill-positive"
                          style={{ width: `${Math.max(4, Math.abs(row.cumulative_return_pct ?? 0) / rankingMaxAbs * 100)}%` }}
                        />
                      </div>
                      <span className={getPerformanceClass(row.cumulative_return_pct)}>
                        {formatPercent(row.cumulative_return_pct)}
                      </span>
                    </div>
                  ))
                ) : (
                  <div className="table-empty-state">
                    <strong>No top ranking available</strong>
                    <span>The ranking endpoint returned an empty top list.</span>
                  </div>
                )}
              </div>
            </div>

            <div className="content-panel performance-ranking-panel">
              <div className="panel-heading-row">
                <div>
                  <span className="eyebrow">Ranking</span>
                  <h2>Worst Performers</h2>
                </div>
                <TrendingDown size={22} />
              </div>
              <div className="performance-ranking-list">
                {sortedWorstRanking.length > 0 ? (
                  sortedWorstRanking.map((row, index) => (
                    <div className="performance-ranking-row" key={`worst-${row.ticker}`}>
                      <span className="ranking-index">{index + 1}</span>
                      <strong>{row.ticker}</strong>
                      <div className="ranking-track">
                        <span
                          className={isPositive(row.cumulative_return_pct) ? "ranking-fill ranking-fill-muted" : "ranking-fill ranking-fill-negative"}
                          style={{ width: `${Math.max(4, Math.abs(row.cumulative_return_pct ?? 0) / rankingMaxAbs * 100)}%` }}
                        />
                      </div>
                      <span className={getPerformanceClass(row.cumulative_return_pct)}>
                        {formatPercent(row.cumulative_return_pct)}
                      </span>
                    </div>
                  ))
                ) : (
                  <div className="table-empty-state">
                    <strong>No worst ranking available</strong>
                    <span>The ranking endpoint returned an empty worst list.</span>
                  </div>
                )}
              </div>
            </div>
          </div>

          <div className="content-panel split-panel interpretation-panel performance-interpretation-panel">
            <DatabaseZap className="panel-icon" size={32} />
            <div>
              <span className="eyebrow">Interpretation</span>
              <h2>Performance Analysis Context</h2>
              <p>
                Performance Analysis measures historical asset behavior using cumulative returns, volatility, drawdown,
                win rate, and Sharpe ratio from the FastAPI performance endpoints.
              </p>
              <p>
                These metrics support BI-style comparison of past market behavior and risk characteristics across
                selected assets.
              </p>
              <p>Historical performance does not guarantee future performance, and this page does not provide financial advice.</p>
            </div>
          </div>

          <div className="content-panel recommendation-panel">
            <div className="panel-heading-row">
              <div>
                <span className="eyebrow">FastAPI Data</span>
                <h2>Latest Returns</h2>
                <p className="performance-table-note">
                  Showing latest {tableRows.length.toLocaleString()} rows from the selected daily performance result.
                </p>
              </div>
              {canToggleTable ? (
                <button
                  className="secondary-button performance-table-toggle"
                  type="button"
                  onClick={() => setIsTableExpanded((currentValue) => !currentValue)}
                >
                  {isTableExpanded ? "Show less" : "Show more"}
                </button>
              ) : (
                <BarChart3 size={22} />
              )}
            </div>

            {tableRows.length > 0 ? (
              <div className="recommendation-table-wrap">
                <table className="recommendation-table performance-table">
                  <thead>
                    <tr>
                      <th scope="col">Date</th>
                      <th scope="col">Ticker</th>
                      <th scope="col">Close</th>
                      <th scope="col">Close Prev</th>
                      <th scope="col">Daily Return %</th>
                    </tr>
                  </thead>
                  <tbody>
                    {tableRows.map((row) => (
                      <tr key={`${row.ticker}-${row.date_id}`}>
                        <td data-label="Date">{row.date_id}</td>
                        <td data-label="Ticker">
                          <strong className="ticker-cell">{row.ticker}</strong>
                        </td>
                        <td data-label="Close">{formatPrice(row.close)}</td>
                        <td data-label="Close Prev">{formatPrice(row.close_prev)}</td>
                        <td data-label="Daily Return %" className={getPerformanceClass(row.daily_return_pct)}>
                          {formatPercent(row.daily_return_pct)}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <div className="table-empty-state">
                <strong>No return rows available</strong>
                <span>The API returned an empty daily performance data set.</span>
              </div>
            )}
          </div>
        </>
      )}
    </section>
  );
}
