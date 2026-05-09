import axios from "axios";
import { useCallback, useEffect, useMemo, useState } from "react";
import type { LucideIcon } from "lucide-react";
import {
  Activity,
  BarChart3,
  DatabaseZap,
  Droplets,
  Gauge,
  LineChart as LineChartIcon,
  RefreshCw,
  Search,
  Sigma,
  Split,
  TrendingUp,
  Waves,
} from "lucide-react";
import {
  Area,
  AreaChart,
  CartesianGrid,
  Legend,
  Line,
  LineChart as RechartsLineChart,
  ReferenceLine,
  ResponsiveContainer,
  Scatter,
  ScatterChart,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import { apiClient } from "../api/client";
import CountUpValue from "../components/reactbits/CountUpValue";
import SpotlightPanel from "../components/reactbits/SpotlightPanel";
import ErrorMessage from "../components/ui/ErrorMessage";
import Loader from "../components/ui/Loader";
import type {
  EnergyMergedRow,
  EnergyOilDailyRow,
  EnergyRollingCorrelationRow,
  EnergyScatterPoint,
  EnergyScatterRegression,
  EnergyScatterResponse,
  EnergySummary,
} from "../types/energy";

type PriceChartPoint = {
  date: string;
  close: number;
  ma30: number | null;
};

type ReturnComparisonPoint = {
  date: string;
  oil_daily_return_pct: number | null;
  asset_daily_return_pct: number | null;
};

type RollingCorrelationPoint = {
  date: string;
  rolling_correlation: number;
};

type ScatterChartPoint = {
  date_id: string;
  oil_daily_return_pct: number;
  asset_daily_return_pct: number;
};

type KpiTone = "positive" | "negative" | "risk" | "neutral" | "purple";

type EnergyKpiCardProps = {
  title: string;
  value: string;
  detail: string;
  icon: LucideIcon;
  tone: KpiTone;
};

const DEFAULT_TABLE_LIMIT = 15;
const EXPANDED_TABLE_LIMIT = 50;
const PRICE_POINT_LIMIT = 320;
const RETURN_POINT_LIMIT = 260;
const ROLLING_POINT_LIMIT = 320;
const SCATTER_POINT_LIMIT = 420;

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

const normalizeStringList = (payload: unknown, nestedKey: string): string[] => {
  if (Array.isArray(payload)) {
    return payload.map((item) => parseText(item)).filter((item): item is string => item !== null);
  }

  if (!isRecord(payload) || !Array.isArray(payload[nestedKey])) {
    return [];
  }

  return payload[nestedKey].map((item) => parseText(item)).filter((item): item is string => item !== null);
};

const normalizeOilDailyRows = (payload: unknown): EnergyOilDailyRow[] =>
  rowsFromPayload(payload, ["data", "rows", "items"]).map((row) => ({
    date_id: parseText(row.date_id) ?? "N/A",
    ticker: parseText(row.ticker) ?? "N/A",
    open: parseNumber(row.open),
    high: parseNumber(row.high),
    low: parseNumber(row.low),
    close: parseNumber(row.close),
    adj_close: parseNumber(row.adj_close),
    volume: parseNumber(row.volume),
    daily_return: parseNumber(row.daily_return),
    daily_return_pct: parseNumber(row.daily_return_pct),
  }));

const normalizeMergedRows = (payload: unknown): EnergyMergedRow[] =>
  rowsFromPayload(payload, ["data", "rows", "items"]).map((row) => ({
    date_id: parseText(row.date_id) ?? "N/A",
    oil_ticker: parseText(row.oil_ticker) ?? "N/A",
    asset_ticker: parseText(row.asset_ticker) ?? "N/A",
    oil_close: parseNumber(row.oil_close),
    oil_daily_return: parseNumber(row.oil_daily_return),
    oil_daily_return_pct: parseNumber(row.oil_daily_return_pct),
    asset_daily_return: parseNumber(row.asset_daily_return),
    asset_daily_return_pct: parseNumber(row.asset_daily_return_pct),
    rolling_correlation: parseNumber(row.rolling_correlation),
  }));

const normalizeRollingRows = (payload: unknown): EnergyRollingCorrelationRow[] =>
  rowsFromPayload(payload, ["data", "rows", "items"]).map((row) => ({
    date_id: parseText(row.date_id) ?? "N/A",
    rolling_correlation: parseNumber(row.rolling_correlation),
  }));

const normalizeSummary = (payload: unknown): EnergySummary | null => {
  if (!isRecord(payload)) {
    return null;
  }

  return {
    oil_ticker: parseText(payload.oil_ticker) ?? "N/A",
    asset_ticker: parseText(payload.asset_ticker) ?? "N/A",
    start_date: parseText(payload.start_date),
    end_date: parseText(payload.end_date),
    common_sessions: parseNumber(payload.common_sessions),
    oil_last_close: parseNumber(payload.oil_last_close),
    oil_previous_close: parseNumber(payload.oil_previous_close),
    oil_change_pct: parseNumber(payload.oil_change_pct),
    oil_period_return_pct: parseNumber(payload.oil_period_return_pct),
    oil_average_volume: parseNumber(payload.oil_average_volume),
    oil_period_high: parseNumber(payload.oil_period_high),
    oil_period_low: parseNumber(payload.oil_period_low),
    oil_annualized_volatility_pct: parseNumber(payload.oil_annualized_volatility_pct),
    global_correlation: parseNumber(payload.global_correlation),
    global_correlation_label: parseText(payload.global_correlation_label),
    latest_rolling_correlation: parseNumber(payload.latest_rolling_correlation),
    latest_rolling_correlation_label: parseText(payload.latest_rolling_correlation_label),
    corr_window: parseNumber(payload.corr_window),
    beta: parseNumber(payload.beta),
    alpha: parseNumber(payload.alpha),
    r_squared: parseNumber(payload.r_squared),
  };
};

const normalizeScatter = (payload: unknown): EnergyScatterResponse => {
  if (!isRecord(payload)) {
    return {
      points: [],
      regression: { beta: null, alpha: null, r_squared: null, correlation: null },
    };
  }

  const regressionPayload = isRecord(payload.regression) ? payload.regression : {};

  return {
    points: rowsFromPayload(payload.points, ["data", "rows", "items"]).map((row) => ({
      date_id: parseText(row.date_id) ?? "N/A",
      oil_daily_return_pct: parseNumber(row.oil_daily_return_pct),
      asset_daily_return_pct: parseNumber(row.asset_daily_return_pct),
    })),
    regression: {
      beta: parseNumber(regressionPayload.beta),
      alpha: parseNumber(regressionPayload.alpha),
      r_squared: parseNumber(regressionPayload.r_squared),
      correlation: parseNumber(regressionPayload.correlation),
    },
  };
};

const buildQueryParams = (params: Record<string, string | number | null | undefined>) => {
  const searchParams = new URLSearchParams();

  Object.entries(params).forEach(([key, value]) => {
    if (value === null || value === undefined) {
      return;
    }

    const textValue = String(value).trim();
    if (textValue) {
      searchParams.set(key, textValue);
    }
  });

  return searchParams;
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

    return `Energy request failed with status ${error.response.status}.`;
  }

  return "Unable to load energy market data.";
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

const formatCorrelation = (value: number | null) => formatNumber(value, 3);

const formatCompactNumber = (value: number | null) => {
  if (value === null || !Number.isFinite(value)) {
    return "N/A";
  }

  return Intl.NumberFormat(undefined, {
    notation: "compact",
    maximumFractionDigits: 2,
  }).format(value);
};

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

const correlationTone = (value: number | null | undefined): KpiTone => {
  if (value === null || value === undefined || !Number.isFinite(value)) {
    return "neutral";
  }

  if (Math.abs(value) < 0.3) {
    return "purple";
  }

  return value >= 0 ? "positive" : "negative";
};

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

const computeMovingAverage = (rows: Array<{ close: number }>, windowSize: number) =>
  rows.map((_, index) => {
    if (index + 1 < windowSize) {
      return null;
    }

    const windowRows = rows.slice(index + 1 - windowSize, index + 1);
    return windowRows.reduce((total, row) => total + row.close, 0) / windowRows.length;
  });

const buildPriceChartData = (rows: EnergyOilDailyRow[]): PriceChartPoint[] => {
  const sortedRows = [...rows]
    .sort((left, right) => left.date_id.localeCompare(right.date_id))
    .map((row) => ({
      date: row.date_id,
      close: row.close,
    }))
    .filter((row): row is { date: string; close: number } => row.close !== null && Number.isFinite(row.close));
  const ma30Values = computeMovingAverage(sortedRows, 30);

  return sortedRows.map((row, index) => ({
    ...row,
    ma30: ma30Values[index],
  }));
};

const buildReturnComparisonData = (rows: EnergyMergedRow[]): ReturnComparisonPoint[] =>
  [...rows]
    .sort((left, right) => left.date_id.localeCompare(right.date_id))
    .map((row) => ({
      date: row.date_id,
      oil_daily_return_pct: row.oil_daily_return_pct,
      asset_daily_return_pct: row.asset_daily_return_pct,
    }));

const buildRollingData = (rows: EnergyRollingCorrelationRow[]): RollingCorrelationPoint[] =>
  [...rows]
    .sort((left, right) => left.date_id.localeCompare(right.date_id))
    .map((row) => ({
      date: row.date_id,
      rolling_correlation: row.rolling_correlation,
    }))
    .filter(
      (row): row is RollingCorrelationPoint =>
        row.rolling_correlation !== null && Number.isFinite(row.rolling_correlation),
    );

const buildScatterData = (points: EnergyScatterPoint[]): ScatterChartPoint[] =>
  points
    .map((point) => ({
      date_id: point.date_id,
      oil_daily_return_pct: point.oil_daily_return_pct,
      asset_daily_return_pct: point.asset_daily_return_pct,
    }))
    .filter(
      (point): point is ScatterChartPoint =>
        point.oil_daily_return_pct !== null &&
        point.asset_daily_return_pct !== null &&
        Number.isFinite(point.oil_daily_return_pct) &&
        Number.isFinite(point.asset_daily_return_pct),
    );

const getLatestRows = (rows: EnergyMergedRow[], limit: number) =>
  [...rows].sort((left, right) => right.date_id.localeCompare(left.date_id)).slice(0, limit);

function EnergyKpiCard({ title, value, detail, icon: Icon, tone }: EnergyKpiCardProps) {
  return (
    <SpotlightPanel className={`energy-kpi-card energy-kpi-card-${tone}`}>
      <div className="kpi-card-header">
        <span>{title}</span>
        <span className="kpi-icon">
          <Icon size={18} />
        </span>
      </div>
      <strong>
        <CountUpValue value={value} />
      </strong>
      <p>{detail}</p>
    </SpotlightPanel>
  );
}

function ScatterTooltip({
  active,
  payload,
}: {
  active?: boolean;
  payload?: Array<{ payload?: ScatterChartPoint }>;
}) {
  if (!active || !payload?.[0]?.payload) {
    return null;
  }

  const point = payload[0].payload;

  return (
    <div className="energy-scatter-tooltip">
      <strong>{formatDateLabel(point.date_id)}</strong>
      <span>Oil return: {formatPercent(point.oil_daily_return_pct)}</span>
      <span>Asset return: {formatPercent(point.asset_daily_return_pct)}</span>
    </div>
  );
}

export default function EnergyMarket() {
  const [oilSeries, setOilSeries] = useState<string[]>([]);
  const [assets, setAssets] = useState<string[]>([]);
  const [selectedOilTicker, setSelectedOilTicker] = useState("");
  const [selectedAssetTicker, setSelectedAssetTicker] = useState("");
  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");
  const [corrWindow, setCorrWindow] = useState(30);
  const [summary, setSummary] = useState<EnergySummary | null>(null);
  const [oilDailyRows, setOilDailyRows] = useState<EnergyOilDailyRow[]>([]);
  const [mergedRows, setMergedRows] = useState<EnergyMergedRow[]>([]);
  const [rollingRows, setRollingRows] = useState<EnergyRollingCorrelationRow[]>([]);
  const [scatterPoints, setScatterPoints] = useState<EnergyScatterPoint[]>([]);
  const [scatterRegression, setScatterRegression] = useState<EnergyScatterRegression>({
    beta: null,
    alpha: null,
    r_squared: null,
    correlation: null,
  });
  const [isReferenceLoading, setIsReferenceLoading] = useState(true);
  const [isEnergyLoading, setIsEnergyLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [isTableExpanded, setIsTableExpanded] = useState(false);

  const fetchReferenceData = useCallback(async () => {
    setIsReferenceLoading(true);
    setErrorMessage(null);

    try {
      const [oilResponse, assetResponse] = await Promise.all([
        apiClient.get<unknown>("/api/energy/oil-series"),
        apiClient.get<unknown>("/api/energy/assets"),
      ]);
      const oilList = normalizeStringList(oilResponse.data, "oil_series");
      const assetList = normalizeStringList(assetResponse.data, "assets");
      const defaultOilTicker = oilList[0] ?? "";
      const defaultAssetTicker = assetList.includes("AAPL") ? "AAPL" : assetList[0] ?? "";

      setOilSeries(oilList);
      setAssets(assetList);
      setSelectedOilTicker((currentTicker) => (oilList.includes(currentTicker) ? currentTicker : defaultOilTicker));
      setSelectedAssetTicker((currentTicker) =>
        assetList.includes(currentTicker) ? currentTicker : defaultAssetTicker,
      );
    } catch (error) {
      setErrorMessage(getErrorMessage(error));
      setOilSeries([]);
      setAssets([]);
      setSelectedOilTicker("");
      setSelectedAssetTicker("");
      setSummary(null);
      setOilDailyRows([]);
      setMergedRows([]);
      setRollingRows([]);
      setScatterPoints([]);
      setScatterRegression({ beta: null, alpha: null, r_squared: null, correlation: null });
    } finally {
      setIsReferenceLoading(false);
    }
  }, []);

  const fetchEnergyData = useCallback(async () => {
    if (!selectedOilTicker || !selectedAssetTicker) {
      return;
    }

    setIsEnergyLoading(true);
    setErrorMessage(null);

    const baseParams = {
      oil_ticker: selectedOilTicker,
      asset_ticker: selectedAssetTicker,
      start_date: startDate,
      end_date: endDate,
    };

    try {
      const [summaryResponse, oilDailyResponse, mergedResponse, rollingResponse, scatterResponse] = await Promise.all([
        apiClient.get<unknown>("/api/energy/summary", {
          params: buildQueryParams({ ...baseParams, corr_window: corrWindow }),
        }),
        apiClient.get<unknown>("/api/energy/oil-daily", {
          params: buildQueryParams({
            oil_ticker: selectedOilTicker,
            start_date: startDate,
            end_date: endDate,
            limit: 2000,
          }),
        }),
        apiClient.get<unknown>("/api/energy/merged", {
          params: buildQueryParams({ ...baseParams, corr_window: corrWindow, limit: 2000 }),
        }),
        apiClient.get<unknown>("/api/energy/rolling-correlation", {
          params: buildQueryParams({ ...baseParams, corr_window: corrWindow }),
        }),
        apiClient.get<unknown>("/api/energy/scatter", {
          params: buildQueryParams(baseParams),
        }),
      ]);

      const scatterData = normalizeScatter(scatterResponse.data);

      setSummary(normalizeSummary(summaryResponse.data));
      setOilDailyRows(normalizeOilDailyRows(oilDailyResponse.data));
      setMergedRows(normalizeMergedRows(mergedResponse.data));
      setRollingRows(normalizeRollingRows(rollingResponse.data));
      setScatterPoints(scatterData.points);
      setScatterRegression(scatterData.regression);
      setIsTableExpanded(false);
    } catch (error) {
      setErrorMessage(getErrorMessage(error));
      setSummary(null);
      setOilDailyRows([]);
      setMergedRows([]);
      setRollingRows([]);
      setScatterPoints([]);
      setScatterRegression({ beta: null, alpha: null, r_squared: null, correlation: null });
    } finally {
      setIsEnergyLoading(false);
    }
  }, [corrWindow, endDate, selectedAssetTicker, selectedOilTicker, startDate]);

  useEffect(() => {
    void fetchReferenceData();
  }, [fetchReferenceData]);

  useEffect(() => {
    void fetchEnergyData();
  }, [fetchEnergyData]);

  const isLoading = isReferenceLoading || isEnergyLoading;
  const priceChartData = useMemo(
    () => downsampleRows(buildPriceChartData(oilDailyRows), PRICE_POINT_LIMIT),
    [oilDailyRows],
  );
  const returnComparisonData = useMemo(
    () => downsampleRows(buildReturnComparisonData(mergedRows), RETURN_POINT_LIMIT),
    [mergedRows],
  );
  const rollingChartData = useMemo(
    () => downsampleRows(buildRollingData(rollingRows), ROLLING_POINT_LIMIT),
    [rollingRows],
  );
  const scatterChartData = useMemo(
    () => downsampleRows(buildScatterData(scatterPoints), SCATTER_POINT_LIMIT),
    [scatterPoints],
  );
  const tableLimit = isTableExpanded ? EXPANDED_TABLE_LIMIT : DEFAULT_TABLE_LIMIT;
  const tableRows = useMemo(() => getLatestRows(mergedRows, tableLimit), [mergedRows, tableLimit]);
  const canToggleTable = mergedRows.length > DEFAULT_TABLE_LIMIT;
  const selectedWindow = summary?.corr_window ?? corrWindow;

  return (
    <section className="page-stack">
      <div className="page-hero hero-energy">
        <div className="hero-copy">
          <span className="eyebrow">Energy Market</span>
          <h1>Oil Market Context Layer</h1>
          <p>Analyze oil prices, returns, rolling correlation, and historical asset sensitivity through FastAPI.</p>
        </div>
        <div className="hero-visual" aria-hidden="true">
          <div className="energy-hero-rig">
            <span />
            <span />
            <span />
            <span />
          </div>
          <div className="hero-card hero-card-secondary">
            <span>Oil vs Asset</span>
            <strong>{selectedOilTicker && selectedAssetTicker ? `${selectedOilTicker} / ${selectedAssetTicker}` : "Loading"}</strong>
          </div>
        </div>
      </div>

      <div className="content-panel energy-filter-panel">
        <div className="panel-heading-row">
          <div>
            <span className="eyebrow">Filters</span>
            <h2>Energy Data Controls</h2>
          </div>
          <Search size={22} />
        </div>

        <div className="energy-filter-grid">
          <label className="advisor-filter-field">
            <span>Oil Series</span>
            <select
              value={selectedOilTicker}
              onChange={(event) => setSelectedOilTicker(event.target.value)}
              disabled={isReferenceLoading || oilSeries.length === 0}
            >
              {oilSeries.length === 0 ? (
                <option value="">No oil series</option>
              ) : (
                oilSeries.map((ticker) => (
                  <option key={ticker} value={ticker}>
                    {ticker}
                  </option>
                ))
              )}
            </select>
          </label>

          <label className="advisor-filter-field">
            <span>Asset</span>
            <select
              value={selectedAssetTicker}
              onChange={(event) => setSelectedAssetTicker(event.target.value)}
              disabled={isReferenceLoading || assets.length === 0}
            >
              {assets.length === 0 ? (
                <option value="">No assets</option>
              ) : (
                assets.map((ticker) => (
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

          <label className="advisor-filter-field energy-window-field">
            <span>Correlation Window</span>
            <input
              type="number"
              min={10}
              max={90}
              step={5}
              value={corrWindow}
              onChange={(event) => setCorrWindow(Math.max(10, Math.min(90, Number(event.target.value) || 30)))}
            />
          </label>

          <div className="energy-filter-actions">
            <button
              className="primary-button"
              type="button"
              onClick={() => void fetchEnergyData()}
              disabled={isLoading || !selectedOilTicker || !selectedAssetTicker}
            >
              <RefreshCw size={18} />
              Refresh Energy
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
          <Droplets className="panel-icon" size={32} />
          <Loader label="Loading energy market data" />
        </div>
      )}

      {errorMessage && !isLoading && <ErrorMessage title="Energy market data unavailable" message={errorMessage} />}

      {!isLoading && !errorMessage && (
        <>
          <div className="energy-kpi-grid">
            <EnergyKpiCard
              title="Oil Last Close"
              value={formatPrice(summary?.oil_last_close ?? null)}
              detail={`Previous close ${formatPrice(summary?.oil_previous_close ?? null)}`}
              icon={Droplets}
              tone="neutral"
            />
            <EnergyKpiCard
              title="Oil Change %"
              value={formatPercent(summary?.oil_change_pct ?? null)}
              detail="Latest close versus previous close"
              icon={TrendingUp}
              tone={isPositive(summary?.oil_change_pct) ? "positive" : "negative"}
            />
            <EnergyKpiCard
              title="Oil Period Return"
              value={formatPercent(summary?.oil_period_return_pct ?? null)}
              detail={`${formatDateLabel(summary?.start_date)} to ${formatDateLabel(summary?.end_date)}`}
              icon={LineChartIcon}
              tone={isPositive(summary?.oil_period_return_pct) ? "positive" : "negative"}
            />
            <EnergyKpiCard
              title="Oil Annualized Volatility"
              value={formatPercent(summary?.oil_annualized_volatility_pct ?? null, { signed: false })}
              detail={`Average volume ${formatCompactNumber(summary?.oil_average_volume ?? null)}`}
              icon={Waves}
              tone="risk"
            />
            <EnergyKpiCard
              title="Global Correlation"
              value={formatCorrelation(summary?.global_correlation ?? null)}
              detail={summary?.global_correlation_label ?? "N/A"}
              icon={Split}
              tone={correlationTone(summary?.global_correlation)}
            />
            <EnergyKpiCard
              title="Latest Rolling Correlation"
              value={formatCorrelation(summary?.latest_rolling_correlation ?? null)}
              detail={`${summary?.latest_rolling_correlation_label ?? "N/A"} over ${selectedWindow} sessions`}
              icon={Activity}
              tone={correlationTone(summary?.latest_rolling_correlation)}
            />
            <EnergyKpiCard
              title="Beta"
              value={formatNumber(summary?.beta ?? null, 3)}
              detail="Historical asset sensitivity to oil returns"
              icon={Sigma}
              tone={correlationTone(summary?.beta)}
            />
            <EnergyKpiCard
              title="R²"
              value={formatNumber(summary?.r_squared ?? null, 3)}
              detail={`Regression alpha ${formatNumber(summary?.alpha ?? null, 3)}`}
              icon={Gauge}
              tone="purple"
            />
            <EnergyKpiCard
              title="Common Sessions"
              value={formatCount(summary?.common_sessions ?? null)}
              detail={`High / low ${formatPrice(summary?.oil_period_high ?? null)} / ${formatPrice(summary?.oil_period_low ?? null)}`}
              icon={BarChart3}
              tone="neutral"
            />
          </div>

          <div className="energy-chart-grid">
            <div className="content-panel energy-price-panel energy-wide-panel">
              <div className="panel-heading-row">
                <div>
                  <span className="eyebrow">Oil Price Evolution</span>
                  <h2>{selectedOilTicker || "Oil"} Close with MA30</h2>
                  <p className="energy-chart-helper">Close prices returned by the oil daily endpoint with a frontend MA30 overlay.</p>
                </div>
              </div>

              {priceChartData.length > 0 ? (
                <div className="energy-recharts-card">
                  <div className="energy-recharts-box energy-recharts-box-large">
                    <ResponsiveContainer width="100%" height="100%">
                      <AreaChart data={priceChartData} margin={{ top: 18, right: 22, left: 8, bottom: 12 }}>
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
                          tickFormatter={(value) => formatPrice(Number(value))}
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
                          formatter={(value, name) => [formatPrice(Number(value)), name === "ma30" ? "MA30" : selectedOilTicker]}
                          labelFormatter={(label) => `Date: ${formatDateLabel(String(label))}`}
                        />
                        <Legend wrapperStyle={{ color: "#53627b", fontWeight: 800, paddingTop: 8 }} />
                        <Area
                          type="monotone"
                          dataKey="close"
                          name={selectedOilTicker || "Oil close"}
                          stroke="#277dff"
                          fill="rgba(39, 125, 255, 0.16)"
                          strokeWidth={2.6}
                          dot={false}
                        />
                        <Line
                          type="monotone"
                          dataKey="ma30"
                          name="MA30"
                          stroke="#ff5da2"
                          strokeWidth={2.25}
                          dot={false}
                          connectNulls
                        />
                      </AreaChart>
                    </ResponsiveContainer>
                  </div>
                  <div className="energy-chart-caption">
                    <span>{formatDateLabel(priceChartData[0]?.date)}</span>
                    <strong>{selectedOilTicker}</strong>
                    <span>{formatDateLabel(priceChartData[priceChartData.length - 1]?.date)}</span>
                  </div>
                </div>
              ) : (
                <div className="table-empty-state">
                  <strong>No oil prices available</strong>
                  <span>The oil daily endpoint returned no numeric close values for this selection.</span>
                </div>
              )}
            </div>

            <div className="content-panel energy-return-panel">
              <div className="panel-heading-row">
                <div>
                  <span className="eyebrow">Returns</span>
                  <h2>Daily Returns Comparison</h2>
                </div>
              </div>

              {returnComparisonData.length > 0 ? (
                <div className="energy-recharts-card energy-recharts-card-compact">
                  <div className="energy-recharts-box">
                    <ResponsiveContainer width="100%" height="100%">
                      <RechartsLineChart data={returnComparisonData} margin={{ top: 16, right: 18, left: 4, bottom: 8 }}>
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
                          cursor={{ stroke: "rgba(18, 214, 197, 0.22)", strokeWidth: 1 }}
                          contentStyle={{
                            border: "1px solid rgba(255, 255, 255, 0.82)",
                            borderRadius: 8,
                            background: "rgba(255, 255, 255, 0.94)",
                            boxShadow: "0 18px 36px rgba(47, 64, 101, 0.14)",
                          }}
                          formatter={(value, name) => [
                            formatPercent(Number(value)),
                            name === "oil_daily_return_pct" ? `${selectedOilTicker} return` : `${selectedAssetTicker} return`,
                          ]}
                          labelFormatter={(label) => `Date: ${formatDateLabel(String(label))}`}
                        />
                        <Legend wrapperStyle={{ color: "#53627b", fontWeight: 800, paddingTop: 8 }} />
                        <ReferenceLine y={0} stroke="#53627b" strokeDasharray="4 5" />
                        <Line
                          type="monotone"
                          dataKey="oil_daily_return_pct"
                          name={`${selectedOilTicker} return`}
                          stroke="#12d6c5"
                          strokeWidth={2.25}
                          dot={false}
                          connectNulls
                        />
                        <Line
                          type="monotone"
                          dataKey="asset_daily_return_pct"
                          name={`${selectedAssetTicker} return`}
                          stroke="#ff5da2"
                          strokeWidth={2.25}
                          dot={false}
                          connectNulls
                        />
                      </RechartsLineChart>
                    </ResponsiveContainer>
                  </div>
                </div>
              ) : (
                <div className="table-empty-state">
                  <strong>No merged returns available</strong>
                  <span>The merged endpoint returned no daily return rows for this selection.</span>
                </div>
              )}
            </div>

            <div className="content-panel energy-correlation-panel">
              <div className="panel-heading-row">
                <div>
                  <span className="eyebrow">Rolling Correlation</span>
                  <h2>{selectedWindow}-Session Oil / Asset Correlation</h2>
                </div>
              </div>

              {rollingChartData.length > 0 ? (
                <div className="energy-recharts-card energy-recharts-card-compact">
                  <div className="energy-recharts-box">
                    <ResponsiveContainer width="100%" height="100%">
                      <AreaChart data={rollingChartData} margin={{ top: 16, right: 18, left: 4, bottom: 8 }}>
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
                          domain={[-1, 1]}
                          tickFormatter={(value) => formatCorrelation(Number(value))}
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
                          formatter={(value) => [formatCorrelation(Number(value)), "Rolling correlation"]}
                          labelFormatter={(label) => `Date: ${formatDateLabel(String(label))}`}
                        />
                        <Legend wrapperStyle={{ color: "#53627b", fontWeight: 800, paddingTop: 8 }} />
                        <ReferenceLine y={0} stroke="#53627b" strokeDasharray="4 5" />
                        <ReferenceLine y={0.3} stroke="#12d6c5" strokeDasharray="3 6" />
                        <ReferenceLine y={-0.3} stroke="#ff7b7b" strokeDasharray="3 6" />
                        <Area
                          type="monotone"
                          dataKey="rolling_correlation"
                          name="Rolling correlation"
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
                  <strong>No rolling correlation available</strong>
                  <span>The API returned no non-null rolling correlation rows for this selection.</span>
                </div>
              )}
            </div>

            <div className="content-panel energy-scatter-panel energy-wide-panel">
              <div className="panel-heading-row">
                <div>
                  <span className="eyebrow">Scatter</span>
                  <h2>Oil Return vs Asset Return</h2>
                  <p className="energy-chart-helper">Scatter points use percentages; regression metrics are calculated from decimal returns.</p>
                </div>
              </div>

              <div className="energy-scatter-layout">
                {scatterChartData.length > 0 ? (
                  <div className="energy-recharts-card">
                    <div className="energy-recharts-box energy-recharts-box-scatter">
                      <ResponsiveContainer width="100%" height="100%">
                        <ScatterChart margin={{ top: 18, right: 24, left: 8, bottom: 16 }}>
                          <CartesianGrid stroke="rgba(83, 98, 123, 0.18)" strokeDasharray="3 4" />
                          <XAxis
                            type="number"
                            dataKey="oil_daily_return_pct"
                            name={`${selectedOilTicker} return`}
                            tickFormatter={(value) => formatPercent(Number(value))}
                            tick={{ fill: "#66738c", fontSize: 12, fontWeight: 700 }}
                            axisLine={{ stroke: "rgba(83, 98, 123, 0.22)" }}
                            tickLine={false}
                          />
                          <YAxis
                            type="number"
                            dataKey="asset_daily_return_pct"
                            name={`${selectedAssetTicker} return`}
                            tickFormatter={(value) => formatPercent(Number(value))}
                            tick={{ fill: "#66738c", fontSize: 12, fontWeight: 700 }}
                            axisLine={false}
                            tickLine={false}
                          />
                          <Tooltip content={<ScatterTooltip />} cursor={{ strokeDasharray: "3 4" }} />
                          <ReferenceLine x={0} stroke="#53627b" strokeDasharray="4 5" />
                          <ReferenceLine y={0} stroke="#53627b" strokeDasharray="4 5" />
                          <Scatter
                            name={`${selectedOilTicker} vs ${selectedAssetTicker}`}
                            data={scatterChartData}
                            fill="#277dff"
                            fillOpacity={0.76}
                          />
                        </ScatterChart>
                      </ResponsiveContainer>
                    </div>
                  </div>
                ) : (
                  <div className="table-empty-state">
                    <strong>No scatter points available</strong>
                    <span>The scatter endpoint returned no valid return pairs for this selection.</span>
                  </div>
                )}

                <div className="energy-regression-card">
                  <span className="eyebrow">Regression Summary</span>
                  <div className="energy-regression-grid">
                    <div>
                      <span>Beta</span>
                      <strong>{formatNumber(scatterRegression.beta, 3)}</strong>
                    </div>
                    <div>
                      <span>Alpha</span>
                      <strong>{formatNumber(scatterRegression.alpha, 3)}</strong>
                    </div>
                    <div>
                      <span>R²</span>
                      <strong>{formatNumber(scatterRegression.r_squared, 3)}</strong>
                    </div>
                    <div>
                      <span>Correlation</span>
                      <strong>{formatCorrelation(scatterRegression.correlation)}</strong>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <div className="content-panel split-panel interpretation-panel energy-interpretation-panel">
            <DatabaseZap className="panel-icon" size={32} />
            <div>
              <span className="eyebrow">Interpretation</span>
              <h2>Energy Market Context</h2>
              <p>
                Energy Market adds oil-market context to the investment decision workflow by connecting oil prices and
                oil daily returns with selected financial asset returns.
              </p>
              <p>
                Correlation compares oil daily returns with the selected asset's daily returns, while beta estimates how
                the asset historically moved with oil returns.
              </p>
              <p>Historical relationships may change over time and this view does not provide financial advice.</p>
            </div>
          </div>

          <div className="content-panel recommendation-panel">
            <div className="panel-heading-row">
              <div>
                <span className="eyebrow">FastAPI Data</span>
                <h2>Latest Merged Sessions</h2>
                <p className="energy-table-note">
                  Showing latest {tableRows.length.toLocaleString()} rows from the selected merged energy result.
                </p>
              </div>
              {canToggleTable ? (
                <button
                  className="secondary-button energy-table-toggle"
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
                <table className="recommendation-table energy-table">
                  <thead>
                    <tr>
                      <th scope="col">Date</th>
                      <th scope="col">Oil Ticker</th>
                      <th scope="col">Asset Ticker</th>
                      <th scope="col">Oil Close</th>
                      <th scope="col">Oil Return %</th>
                      <th scope="col">Asset Return %</th>
                      <th scope="col">Rolling Correlation</th>
                    </tr>
                  </thead>
                  <tbody>
                    {tableRows.map((row) => (
                      <tr key={`${row.oil_ticker}-${row.asset_ticker}-${row.date_id}`}>
                        <td data-label="Date">{row.date_id}</td>
                        <td data-label="Oil Ticker">
                          <strong className="ticker-cell">{row.oil_ticker}</strong>
                        </td>
                        <td data-label="Asset Ticker">
                          <strong className="ticker-cell">{row.asset_ticker}</strong>
                        </td>
                        <td data-label="Oil Close">{formatPrice(row.oil_close)}</td>
                        <td
                          data-label="Oil Return %"
                          className={isPositive(row.oil_daily_return_pct) ? "energy-value-positive" : "energy-value-negative"}
                        >
                          {formatPercent(row.oil_daily_return_pct)}
                        </td>
                        <td
                          data-label="Asset Return %"
                          className={isPositive(row.asset_daily_return_pct) ? "energy-value-positive" : "energy-value-negative"}
                        >
                          {formatPercent(row.asset_daily_return_pct)}
                        </td>
                        <td data-label="Rolling Correlation">{formatCorrelation(row.rolling_correlation)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <div className="table-empty-state">
                <strong>No merged sessions available</strong>
                <span>The API returned an empty merged energy data set.</span>
              </div>
            )}
          </div>
        </>
      )}
    </section>
  );
}
