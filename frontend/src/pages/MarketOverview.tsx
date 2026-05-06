import axios from "axios";
import { useCallback, useEffect, useMemo, useState } from "react";
import {
  Activity,
  BarChart3,
  CandlestickChart,
  DatabaseZap,
  Gauge,
  LineChart as LineChartIcon,
  RefreshCw,
  Search,
  TrendingUp,
  Waves,
} from "lucide-react";
import {
  Bar,
  BarChart as RechartsBarChart,
  CartesianGrid,
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
import type { MarketDailyRow, MarketReturnRow, MarketSummary } from "../types/market";

type ReturnBin = {
  range: string;
  count: number;
  start: number;
  end: number;
};

type PriceChartPoint = {
  date: string;
  close: number;
  ma20: number | null;
  ma50: number | null;
};

type VolumeChartPoint = {
  date: string;
  volume: number;
};

const DEFAULT_TABLE_LIMIT = 15;
const EXPANDED_TABLE_LIMIT = 50;
const PRICE_POINT_LIMIT = 240;
const VOLUME_POINT_LIMIT = 180;

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

  if (!isRecord(payload)) {
    return [];
  }

  const nested = payload.tickers;
  if (!Array.isArray(nested)) {
    return [];
  }

  return nested.map((ticker) => parseText(ticker)).filter((ticker): ticker is string => ticker !== null);
};

const normalizeSummary = (payload: unknown): MarketSummary | null => {
  if (!isRecord(payload)) {
    return null;
  }

  return {
    ticker: parseText(payload.ticker) ?? "N/A",
    start_date: parseText(payload.start_date),
    end_date: parseText(payload.end_date),
    observations: parseNumber(payload.observations),
    last_close: parseNumber(payload.last_close),
    previous_close: parseNumber(payload.previous_close),
    price_change: parseNumber(payload.price_change),
    price_change_pct: parseNumber(payload.price_change_pct),
    period_return_pct: parseNumber(payload.period_return_pct),
    average_volume: parseNumber(payload.average_volume),
    period_high: parseNumber(payload.period_high),
    period_low: parseNumber(payload.period_low),
    annualized_volatility_pct: parseNumber(payload.annualized_volatility_pct),
  };
};

const normalizeDailyRows = (payload: unknown): MarketDailyRow[] =>
  rowsFromPayload(payload, ["data", "rows", "items"]).map((row) => ({
    date_id: parseText(row.date_id) ?? "N/A",
    ticker: parseText(row.ticker) ?? "N/A",
    open: parseNumber(row.open),
    high: parseNumber(row.high),
    low: parseNumber(row.low),
    close: parseNumber(row.close),
    volume: parseNumber(row.volume),
  }));

const normalizeReturnRows = (payload: unknown): MarketReturnRow[] =>
  rowsFromPayload(payload, ["data", "rows", "items"]).map((row) => ({
    date_id: parseText(row.date_id) ?? "N/A",
    ticker: parseText(row.ticker) ?? "N/A",
    daily_return_pct: parseNumber(row.daily_return_pct),
  }));

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

    return `Market request failed with status ${error.response.status}.`;
  }

  return "Unable to load market data.";
};

const formatCurrency = (value: number | null) => {
  if (value === null || Number.isNaN(value)) {
    return "N/A";
  }

  return value.toLocaleString(undefined, {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  });
};

const formatSignedPrice = (value: number | null) => {
  if (value === null || Number.isNaN(value)) {
    return "N/A";
  }

  return `${value > 0 ? "+" : ""}${formatCurrency(value)}`;
};

const formatPercent = (value: number | null) => {
  if (value === null || Number.isNaN(value)) {
    return "N/A";
  }

  return `${value > 0 ? "+" : ""}${value.toFixed(2)}%`;
};

const formatVolume = (value: number | null) => {
  if (value === null || Number.isNaN(value)) {
    return "N/A";
  }

  return Math.round(value).toLocaleString();
};

const formatCompactNumber = (value: number | null) => {
  if (value === null || Number.isNaN(value)) {
    return "N/A";
  }

  return Intl.NumberFormat(undefined, {
    notation: "compact",
    maximumFractionDigits: 2,
  }).format(value);
};

const formatCount = (value: number | null) => {
  if (value === null || Number.isNaN(value)) {
    return "N/A";
  }

  return Math.round(value).toLocaleString();
};

const formatDateLabel = (value: string | null | undefined) => {
  if (!value || value === "N/A") {
    return "N/A";
  }

  const date = new Date(value);

  if (Number.isNaN(date.getTime())) {
    return value;
  }

  return date.toLocaleDateString(undefined, {
    month: "short",
    day: "numeric",
    year: "2-digit",
  });
};

const sortDailyRowsDesc = (rows: MarketDailyRow[]) =>
  [...rows].sort((left, right) => right.date_id.localeCompare(left.date_id));

const sortDailyRowsAsc = (rows: MarketDailyRow[]) =>
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

const getLatestRows = (rows: MarketDailyRow[], limit: number) => sortDailyRowsDesc(rows).slice(0, limit);

const toChartNumber = (value: number | null) => (value === null ? Number.NaN : Number(value));

const computeMovingAverage = (rows: Array<{ close: number }>, windowSize: number) =>
  rows.map((_, index) => {
    if (index + 1 < windowSize) {
      return null;
    }

    const windowRows = rows.slice(index + 1 - windowSize, index + 1);
    const closeValues = windowRows.map((windowRow) => windowRow.close);

    if (closeValues.length !== windowSize) {
      return null;
    }

    return closeValues.reduce((total, value) => total + value, 0) / windowSize;
  });

const buildPriceChartData = (rows: MarketDailyRow[]): PriceChartPoint[] => {
  const sortedRows = sortDailyRowsAsc(rows)
    .map((row) => ({
      date: row.date_id,
      close: toChartNumber(row.close),
    }))
    .filter((row) => Number.isFinite(row.close));
  const ma20Values = computeMovingAverage(sortedRows, 20);
  const ma50Values = computeMovingAverage(sortedRows, 50);

  return sortedRows.map((row, index) => ({
    date: row.date,
    close: row.close,
    ma20: ma20Values[index],
    ma50: ma50Values[index],
  }));
};

const buildVolumeChartData = (rows: MarketDailyRow[]): VolumeChartPoint[] =>
  sortDailyRowsAsc(rows)
    .map((row) => ({
      date: row.date_id,
      volume: toChartNumber(row.volume),
    }))
    .filter((row) => Number.isFinite(row.volume));

const buildReturnBins = (rows: MarketReturnRow[], binCount = 7): ReturnBin[] => {
  const returns = rows
    .map((row) => toChartNumber(row.daily_return_pct))
    .filter((value) => Number.isFinite(value));

  if (returns.length === 0) {
    return [];
  }

  const minReturn = Math.min(...returns);
  const maxReturn = Math.max(...returns);
  const range = maxReturn - minReturn;

  if (range === 0) {
    return [
      {
        range: `${minReturn.toFixed(2)}%`,
        count: returns.length,
        start: minReturn,
        end: maxReturn,
      },
    ];
  }

  const step = range / binCount;
  const bins = Array.from({ length: binCount }, (_, index) => {
    const start = minReturn + index * step;
    const end = index === binCount - 1 ? maxReturn : start + step;
    return {
      range: `${start.toFixed(1)}% to ${end.toFixed(1)}%`,
      count: 0,
      start,
      end,
    };
  });

  returns.forEach((value) => {
    const index = Math.min(binCount - 1, Math.floor((value - minReturn) / step));
    bins[index].count += 1;
  });

  return bins;
};

export default function MarketOverview() {
  const [tickers, setTickers] = useState<string[]>([]);
  const [selectedTicker, setSelectedTicker] = useState("");
  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");
  const [summary, setSummary] = useState<MarketSummary | null>(null);
  const [dailyRows, setDailyRows] = useState<MarketDailyRow[]>([]);
  const [returnRows, setReturnRows] = useState<MarketReturnRow[]>([]);
  const [isTickerLoading, setIsTickerLoading] = useState(true);
  const [isMarketLoading, setIsMarketLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [isTableExpanded, setIsTableExpanded] = useState(false);

  const fetchTickers = useCallback(async () => {
    setIsTickerLoading(true);
    setErrorMessage(null);

    try {
      const response = await apiClient.get<unknown>("/api/market/tickers");
      const tickerList = normalizeTickers(response.data);

      setTickers(tickerList);
      setSelectedTicker((currentTicker) => currentTicker || tickerList[0] || "");
    } catch (error) {
      setErrorMessage(getErrorMessage(error));
      setTickers([]);
      setSelectedTicker("");
      setSummary(null);
      setDailyRows([]);
      setReturnRows([]);
    } finally {
      setIsTickerLoading(false);
    }
  }, []);

  const fetchMarketData = useCallback(async () => {
    if (!selectedTicker) {
      return;
    }

    setIsMarketLoading(true);
    setErrorMessage(null);

    const trimmedStartDate = startDate.trim();
    const trimmedEndDate = endDate.trim();
    const params = {
      ticker: selectedTicker,
      ...(trimmedStartDate ? { start_date: trimmedStartDate } : {}),
      ...(trimmedEndDate ? { end_date: trimmedEndDate } : {}),
    };

    try {
      const [summaryResponse, dailyResponse, returnsResponse] = await Promise.all([
        apiClient.get<unknown>("/api/market/summary", { params }),
        apiClient.get<unknown>("/api/market/daily", { params }),
        apiClient.get<unknown>("/api/market/returns-distribution", { params }),
      ]);

      console.log("Summary response:", summaryResponse.data);
      console.log("Daily response:", dailyResponse.data);
      console.log("Returns response:", returnsResponse.data);

      setSummary(normalizeSummary(summaryResponse.data));
      setDailyRows(normalizeDailyRows(dailyResponse.data));
      setReturnRows(normalizeReturnRows(returnsResponse.data));
      setIsTableExpanded(false);
    } catch (error) {
      setErrorMessage(getErrorMessage(error));
      setSummary(null);
      setDailyRows([]);
      setReturnRows([]);
    } finally {
      setIsMarketLoading(false);
    }
  }, [endDate, selectedTicker, startDate]);

  useEffect(() => {
    void fetchTickers();
  }, [fetchTickers]);

  useEffect(() => {
    void fetchMarketData();
  }, [fetchMarketData]);

  const isLoading = isTickerLoading || isMarketLoading;
  const sortedDailyRows = useMemo(() => sortDailyRowsDesc(dailyRows), [dailyRows]);
  const tableLimit = isTableExpanded ? EXPANDED_TABLE_LIMIT : DEFAULT_TABLE_LIMIT;
  const tableRows = useMemo(() => getLatestRows(dailyRows, tableLimit), [dailyRows, tableLimit]);
  const priceChartData = useMemo(() => {
    const data = downsampleRows(buildPriceChartData(dailyRows), PRICE_POINT_LIMIT);
    console.log("Daily rows:", dailyRows.length, dailyRows.slice(0, 3));
    console.log("Price chart data:", data.length, data.slice(0, 3));
    return data;
  }, [dailyRows]);
  const volumeChartData = useMemo(() => {
    const data = downsampleRows(buildVolumeChartData(dailyRows).slice(-VOLUME_POINT_LIMIT), VOLUME_POINT_LIMIT);
    console.log("Volume chart data:", data.length, data.slice(0, 3));
    return data;
  }, [dailyRows]);
  const averageVolume = useMemo(() => {
    const values = volumeChartData.map((row) => row.volume);
    return values.length > 0 ? values.reduce((total, value) => total + value, 0) / values.length : null;
  }, [volumeChartData]);
  const returnBins = useMemo(() => {
    const bins = buildReturnBins(returnRows, 9);
    console.log("Return rows:", returnRows.length, returnRows.slice(0, 3));
    console.log("Return bins:", bins.length, bins);
    return bins;
  }, [returnRows]);
  const canToggleTable = sortedDailyRows.length > DEFAULT_TABLE_LIMIT;

  return (
    <section className="page-stack">
      <div className="page-hero hero-market">
        <div className="hero-copy">
          <span className="eyebrow">Market Overview</span>
          <h1>Historical Market Intelligence</h1>
          <p>Explore PostgreSQL-backed prices, volume, returns, and volatility through the FastAPI market layer.</p>
        </div>
        <div className="hero-visual" aria-hidden="true">
          <div className="market-hero-chart">
            <span />
            <span />
            <span />
          </div>
          <div className="hero-card hero-card-secondary">
            <span>BI Layer</span>
            <strong>{selectedTicker || "Loading"}</strong>
          </div>
        </div>
      </div>

      <div className="content-panel market-filter-panel">
        <div className="panel-heading-row">
          <div>
            <span className="eyebrow">Filters</span>
            <h2>Market Data Controls</h2>
          </div>
          <Search size={22} />
        </div>

        <div className="market-filter-grid">
          <label className="advisor-filter-field">
            <span>Ticker</span>
            <select
              value={selectedTicker}
              onChange={(event) => setSelectedTicker(event.target.value)}
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

          <div className="market-filter-actions">
            <button
              className="primary-button"
              type="button"
              onClick={() => void fetchMarketData()}
              disabled={isLoading || !selectedTicker}
            >
              <RefreshCw size={18} />
              Refresh Market
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
      </div>

      {isLoading && (
        <div className="content-panel split-panel">
          <CandlestickChart className="panel-icon" size={32} />
          <Loader label="Loading market data" />
        </div>
      )}

      {errorMessage && !isLoading && <ErrorMessage title="Market data unavailable" message={errorMessage} />}

      {!isLoading && !errorMessage && (
        <>
          <div className="kpi-grid market-kpi-grid">
            <KpiCard title="Last Close" value={formatCurrency(summary?.last_close ?? null)} detail="Latest close in selected period" icon={CandlestickChart} />
            <KpiCard title="Price Change %" value={formatPercent(summary?.price_change_pct ?? null)} detail={`Price change ${formatSignedPrice(summary?.price_change ?? null)}`} icon={TrendingUp} />
            <KpiCard title="Period Return %" value={formatPercent(summary?.period_return_pct ?? null)} detail="Return across selected period" icon={LineChartIcon} />
            <KpiCard title="Average Volume" value={formatCompactNumber(summary?.average_volume ?? null)} detail="Mean traded volume" icon={BarChart3} />
            <KpiCard title="Period High / Low" value={`${formatCurrency(summary?.period_high ?? null)} / ${formatCurrency(summary?.period_low ?? null)}`} detail="Observed range in selected period" icon={Activity} />
            <KpiCard title="Annualized Volatility" value={formatPercent(summary?.annualized_volatility_pct ?? null)} detail="Volatility returned by FastAPI" icon={Waves} />
            <KpiCard title="Observations" value={formatCount(summary?.observations ?? null)} detail="Market rows in selected period" icon={Gauge} />
          </div>

          <div className="market-chart-grid">
            <div className="content-panel market-line-panel">
              <div className="panel-heading-row">
                <div>
                  <span className="eyebrow">Price</span>
                  <h2>Price Evolution with Moving Averages</h2>
                </div>
              </div>
              {priceChartData.length > 0 ? (
                <div className="market-recharts-card">
                  <div className="market-recharts-box market-recharts-box-large">
                    <ResponsiveContainer width="100%" height="100%">
                      <RechartsLineChart data={priceChartData} margin={{ top: 18, right: 22, left: 10, bottom: 12 }}>
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
                          width={72}
                          domain={["auto", "auto"]}
                          tickFormatter={(value) => formatCurrency(Number(value))}
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
                          formatter={(value, name) => [
                            formatCurrency(Number(value)),
                            name === "ma20" ? "MA20" : name === "ma50" ? "MA50" : "Close",
                          ]}
                          labelFormatter={(label) => `Date: ${formatDateLabel(String(label))}`}
                        />
                        <Legend wrapperStyle={{ color: "#53627b", fontWeight: 800, paddingTop: 8 }} />
                        {summary?.last_close !== null && summary?.last_close !== undefined && (
                          <ReferenceLine
                            y={summary.last_close}
                            stroke="#ff5da2"
                            strokeDasharray="4 5"
                            ifOverflow="extendDomain"
                          />
                        )}
                        <Line
                          type="monotone"
                          dataKey="close"
                          name="Close"
                          stroke="#277dff"
                          strokeWidth={2.5}
                          dot={false}
                          activeDot={{ r: 4, strokeWidth: 2, stroke: "#ffffff" }}
                        />
                        <Line
                          type="monotone"
                          dataKey="ma20"
                          name="MA20"
                          stroke="#12d6c5"
                          strokeWidth={2.25}
                          dot={false}
                          connectNulls
                        />
                        <Line
                          type="monotone"
                          dataKey="ma50"
                          name="MA50"
                          stroke="#ff7b7b"
                          strokeWidth={2.25}
                          dot={false}
                          connectNulls
                        />
                      </RechartsLineChart>
                    </ResponsiveContainer>
                  </div>
                  <div className="market-chart-caption">
                    <span>{formatDateLabel(priceChartData[0]?.date)}</span>
                    <strong>{selectedTicker}</strong>
                    <span>{formatDateLabel(priceChartData[priceChartData.length - 1]?.date)}</span>
                  </div>
                </div>
              ) : (
                <div className="table-empty-state">
                  <strong>No close prices available</strong>
                  <span>The API did not return close values for this selection.</span>
                </div>
              )}
            </div>

            <div className="content-panel market-volume-panel">
              <div className="panel-heading-row">
                <div>
                  <span className="eyebrow">Volume</span>
                  <h2>Volume by Date</h2>
                </div>
              </div>
              {volumeChartData.length > 0 ? (
                <div className="market-recharts-card market-recharts-card-compact">
                  <p className="market-chart-helper">Average volume in view: {formatCompactNumber(averageVolume)}</p>
                  <div className="market-recharts-box">
                    <ResponsiveContainer width="100%" height="100%">
                      <RechartsBarChart data={volumeChartData} margin={{ top: 12, right: 18, left: 4, bottom: 8 }}>
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
                          width={58}
                          tickFormatter={(value) => formatCompactNumber(Number(value))}
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
                          formatter={(value) => [formatCompactNumber(Number(value)), "Volume"]}
                          labelFormatter={(label) => `Date: ${formatDateLabel(String(label))}`}
                        />
                        {averageVolume !== null && (
                          <ReferenceLine
                            y={averageVolume}
                            stroke="#ff5da2"
                            strokeDasharray="4 5"
                            label={{ value: "Avg", fill: "#9b4b6e", fontSize: 11, fontWeight: 800 }}
                          />
                        )}
                        <Bar dataKey="volume" name="Volume" fill="#12d6c5" radius={[5, 5, 0, 0]} maxBarSize={18} />
                      </RechartsBarChart>
                    </ResponsiveContainer>
                  </div>
                </div>
              ) : (
                <div className="table-empty-state">
                  <strong>No volume rows available</strong>
                  <span>The API did not return volume values for this selection.</span>
                </div>
              )}
            </div>

            <div className="content-panel market-return-panel">
              <div className="panel-heading-row">
                <div>
                  <span className="eyebrow">Returns</span>
                  <h2>Daily Return Distribution</h2>
                </div>
              </div>
              {returnBins.length > 0 ? (
                <div className="market-recharts-card market-recharts-card-compact">
                  <p className="market-chart-helper">
                    Distribution of daily returns across the selected period.
                  </p>
                  <div className="market-recharts-box">
                    <ResponsiveContainer width="100%" height="100%">
                      <RechartsBarChart data={returnBins} margin={{ top: 12, right: 18, left: 4, bottom: 8 }}>
                        <CartesianGrid stroke="rgba(83, 98, 123, 0.16)" strokeDasharray="3 4" vertical={false} />
                        <XAxis
                          dataKey="range"
                          interval={0}
                          angle={-18}
                          textAnchor="end"
                          height={64}
                          tick={{ fill: "#66738c", fontSize: 11, fontWeight: 700 }}
                          axisLine={{ stroke: "rgba(83, 98, 123, 0.22)" }}
                          tickLine={false}
                        />
                        <YAxis
                          width={44}
                          allowDecimals={false}
                          tick={{ fill: "#66738c", fontSize: 12, fontWeight: 700 }}
                          axisLine={false}
                          tickLine={false}
                        />
                        <Tooltip
                          cursor={{ fill: "rgba(255, 216, 107, 0.12)" }}
                          contentStyle={{
                            border: "1px solid rgba(255, 255, 255, 0.82)",
                            borderRadius: 8,
                            background: "rgba(255, 255, 255, 0.94)",
                            boxShadow: "0 18px 36px rgba(47, 64, 101, 0.14)",
                          }}
                          formatter={(value) => [Number(value).toLocaleString(), "Sessions"]}
                          labelFormatter={(label) => `Return interval: ${label}`}
                        />
                        <Bar dataKey="count" name="Sessions" fill="#277dff" radius={[5, 5, 0, 0]} maxBarSize={44} />
                      </RechartsBarChart>
                    </ResponsiveContainer>
                  </div>
                </div>
              ) : (
                <div className="table-empty-state">
                  <strong>No return distribution available</strong>
                  <span>The API did not return daily return values for this selection.</span>
                </div>
              )}
            </div>
          </div>

          <div className="content-panel split-panel interpretation-panel market-interpretation-panel">
            <DatabaseZap className="panel-icon" size={32} />
            <div>
              <span className="eyebrow">Interpretation</span>
              <h2>BI market layer</h2>
              <p>
                Market Overview is the BI layer for exploring historical prices, volumes, returns, and volatility for
                the selected ticker and date range.
              </p>
              <p>Data comes from PostgreSQL through the FastAPI market endpoints.</p>
              <p>The page displays only the API data and derived visual groupings from that returned data.</p>
            </div>
          </div>

          <div className="content-panel recommendation-panel">
            <div className="panel-heading-row">
              <div>
                <span className="eyebrow">FastAPI Data</span>
                <h2>Latest Market Sessions</h2>
                <p className="market-table-note">
                  Showing latest {tableRows.length.toLocaleString()} rows from the selected API result.
                </p>
              </div>
              {canToggleTable ? (
                <button
                  className="secondary-button market-table-toggle"
                  type="button"
                  onClick={() => setIsTableExpanded((currentValue) => !currentValue)}
                >
                  {isTableExpanded ? "Show less" : "Show more"}
                </button>
              ) : (
                <CandlestickChart size={22} />
              )}
            </div>
            {tableRows.length > 0 ? (
              <div className="recommendation-table-wrap">
                <table className="recommendation-table market-table">
                  <thead>
                    <tr>
                      <th scope="col">Date</th>
                      <th scope="col">Ticker</th>
                      <th scope="col">Open</th>
                      <th scope="col">High</th>
                      <th scope="col">Low</th>
                      <th scope="col">Close</th>
                      <th scope="col">Volume</th>
                    </tr>
                  </thead>
                  <tbody>
                    {tableRows.map((row) => (
                      <tr key={`${row.ticker}-${row.date_id}`}>
                        <td data-label="Date">{row.date_id}</td>
                        <td data-label="Ticker">
                          <strong className="ticker-cell">{row.ticker}</strong>
                        </td>
                        <td data-label="Open">{formatCurrency(row.open)}</td>
                        <td data-label="High">{formatCurrency(row.high)}</td>
                        <td data-label="Low">{formatCurrency(row.low)}</td>
                        <td data-label="Close">{formatCurrency(row.close)}</td>
                        <td data-label="Volume" title={formatVolume(row.volume)}>{formatCompactNumber(row.volume)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <div className="table-empty-state">
                <strong>No market rows available</strong>
                <span>The API returned an empty daily market data set.</span>
              </div>
            )}
          </div>
        </>
      )}
    </section>
  );
}
