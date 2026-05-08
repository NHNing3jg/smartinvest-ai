import axios from "axios";
import {
  Activity,
  BarChart3,
  Brain,
  ChartNoAxesCombined,
  CheckCircle2,
  CircleAlert,
  CircleDot,
  DatabaseZap,
  Droplets,
  Gauge,
  Globe2,
  Layers3,
  LineChart,
  PieChart,
  RefreshCw,
  Route,
  ShieldCheck,
  Sparkles,
  TrendingUp,
  WalletCards,
} from "lucide-react";
import type { LucideIcon } from "lucide-react";
import { useCallback, useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";

import { apiClient } from "../api/client";
import ErrorMessage from "../components/ui/ErrorMessage";
import Loader from "../components/ui/Loader";
import type { BacktestMetricRow, BacktestSignal, BacktestSummaryRow } from "../types/backtest";
import type { DashboardData, DashboardModuleStatus } from "../types/dashboard";
import type { EnergySummary } from "../types/energy";
import type { MacroSummary } from "../types/macro";
import type { MarketSummary } from "../types/market";
import type { PerformanceSummary } from "../types/performance";
import type { PortfolioAllocationRow, PortfolioSummaryRow } from "../types/portfolio";
import type { Recommendation, RecommendationSignal, RecommendationSummary } from "../types/recommendation";

const SIGNALS: RecommendationSignal[] = ["BUY", "HOLD", "SELL"];

type EndpointKey = keyof DashboardData;

type EndpointResult = {
  key: EndpointKey;
  ok: boolean;
  data: unknown;
  error: string | null;
};

type ExecutiveKpi = {
  title: string;
  value: string;
  detail: string;
  icon: LucideIcon;
  tone: "positive" | "negative" | "risk" | "neutral" | "purple";
};

const emptyDashboardData: DashboardData = {
  health: null,
  recommendationSummary: null,
  recommendations: [],
  backtestSummary: [],
  backtestMetrics: [],
  portfolioSummary: null,
  portfolioAllocation: [],
  marketSummary: null,
  macroSummary: null,
  performanceSummary: null,
  energySummary: null,
};

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

  const rows: Record<string, unknown>[] = [];
  for (const [key, value] of Object.entries(payload)) {
    if (isRecord(value)) {
      rows.push({ ...value, signal: value.signal ?? key });
    }
  }

  return rows;
};

const normalizeSignal = (value: unknown): RecommendationSignal | null => {
  if (typeof value !== "string") {
    return null;
  }

  const normalized = value.toUpperCase();
  return SIGNALS.includes(normalized as RecommendationSignal) ? (normalized as RecommendationSignal) : null;
};

const normalizeRecommendations = (payload: unknown): Recommendation[] =>
  rowsFromPayload(payload, ["data", "recommendations", "rows", "items"]).map((row) => ({
    date_id: parseText(row.date_id),
    ticker: parseText(row.ticker) ?? "N/A",
    proba_up: parseNumber(row.proba_up),
    predicted_direction: parseText(row.predicted_direction),
    signal: normalizeSignal(row.signal) ?? "HOLD",
    confidence: parseText(row.confidence),
    advisor_score: parseNumber(row.advisor_score),
    momentum_5: parseNumber(row.momentum_5),
    momentum_10: parseNumber(row.momentum_10),
    rolling_vol_10: parseNumber(row.rolling_vol_10),
    oil_return: parseNumber(row.oil_return),
    sp500_return: parseNumber(row.sp500_return),
    nasdaq_return: parseNumber(row.nasdaq_return),
    explanation: parseText(row.explanation),
  }));

const normalizeRecommendationSummary = (payload: unknown): RecommendationSummary | null => {
  if (!isRecord(payload)) {
    return null;
  }

  return {
    total_recommendations: parseNumber(payload.total_recommendations) ?? 0,
    buy_count: parseNumber(payload.buy_count) ?? 0,
    hold_count: parseNumber(payload.hold_count) ?? 0,
    sell_count: parseNumber(payload.sell_count) ?? 0,
    average_proba_up: parseNumber(payload.average_proba_up),
    top_advisor_score: parseNumber(payload.top_advisor_score),
  };
};

const normalizeBacktestSummary = (payload: unknown): BacktestSummaryRow[] =>
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

const normalizeBacktestMetrics = (payload: unknown): BacktestMetricRow[] => {
  const rows = rowsFromPayload(payload, ["metrics", "data", "rows", "items"]);
  if (rows.length > 0) {
    return rows.map((row) => ({
      ...row,
      metric: parseText(row.metric) ?? undefined,
      signal: parseText(row.signal) ?? undefined,
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

const normalizePortfolioAllocation = (payload: unknown): PortfolioAllocationRow[] =>
  rowsFromPayload(payload, ["allocation", "data", "rows", "items"]).map((row) => ({
    ticker: parseText(row.ticker) ?? "N/A",
    signal: parseText(row.signal),
    confidence: parseText(row.confidence),
    proba_up: parseNumber(row.proba_up),
    advisor_score: parseNumber(row.advisor_score),
    expected_return: parseNumber(row.expected_return),
    risk_score: parseNumber(row.risk_score),
    weight: parseNumber(row.weight),
    explanation: parseText(row.explanation),
  }));

const normalizePortfolioSummary = (payload: unknown): PortfolioSummaryRow | null => {
  if (isRecord(payload)) {
    return {
      expected_return: parseNumber(payload.expected_return),
      risk_score: parseNumber(payload.risk_score),
      risk_level: parseText(payload.risk_level),
    };
  }

  const rows = rowsFromPayload(payload, ["summary", "data", "rows", "items"]);
  if (rows.length === 0) {
    return null;
  }

  const metricMap = new Map<string, unknown>();
  rows.forEach((row) => {
    const metric = parseText(row.metric);
    if (metric) {
      metricMap.set(normalizeKey(metric), row.value);
    }
  });

  return {
    expected_return: parseNumber(metricMap.get("portfolio_expected_return")),
    risk_score: parseNumber(metricMap.get("portfolio_risk_score")),
    risk_level: parseText(metricMap.get("portfolio_risk_level")),
  };
};

const normalizeMarketSummary = (payload: unknown): MarketSummary | null => {
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

const normalizeMacroSummary = (payload: unknown): MacroSummary | null => {
  if (!isRecord(payload)) {
    return null;
  }

  return {
    series_id: parseText(payload.series_id) ?? "N/A",
    label: parseText(payload.label) ?? parseText(payload.series_id) ?? "N/A",
    start_date: parseText(payload.start_date),
    end_date: parseText(payload.end_date),
    observations: parseNumber(payload.observations),
    latest_value: parseNumber(payload.latest_value),
    previous_value: parseNumber(payload.previous_value),
    absolute_change: parseNumber(payload.absolute_change),
    percent_change: parseNumber(payload.percent_change),
    period_change: parseNumber(payload.period_change),
    period_change_pct: parseNumber(payload.period_change_pct),
    period_mean: parseNumber(payload.period_mean),
    period_std: parseNumber(payload.period_std),
    period_min: parseNumber(payload.period_min),
    period_max: parseNumber(payload.period_max),
  };
};

const normalizePerformanceSummary = (payload: unknown): PerformanceSummary | null => {
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

const normalizeEnergySummary = (payload: unknown): EnergySummary | null => {
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

const normalizeKey = (value: string) => value.toLowerCase().replace(/[^a-z0-9]+/g, "_");

const endpointErrorMessage = (error: unknown) => {
  if (axios.isAxiosError(error)) {
    if (!error.response) {
      return "FastAPI backend unavailable.";
    }

    const detail = error.response.data?.detail;
    if (typeof detail === "string") {
      return detail;
    }

    if (detail?.message) {
      return detail.message;
    }

    return `Request failed with status ${error.response.status}.`;
  }

  return "Module data unavailable.";
};

const buildQueryParams = (params: Record<string, string | number>) => {
  const searchParams = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => searchParams.set(key, String(value)));
  return searchParams;
};

const fetchEndpoint = async (key: EndpointKey, url: string, params?: URLSearchParams): Promise<EndpointResult> => {
  try {
    const response = await apiClient.get<unknown>(url, params ? { params } : undefined);
    return { key, ok: true, data: response.data, error: null };
  } catch (error) {
    return { key, ok: false, data: null, error: endpointErrorMessage(error) };
  }
};

const formatCount = (value: number | null) => {
  if (value === null || !Number.isFinite(value)) {
    return "N/A";
  }

  return Math.round(value).toLocaleString();
};

const formatDecimal = (value: number | null, digits = 3) => {
  if (value === null || !Number.isFinite(value)) {
    return "N/A";
  }

  return value.toFixed(digits);
};

const formatSignedPercent = (value: number | null, options?: { alreadyPercent?: boolean }) => {
  if (value === null || !Number.isFinite(value)) {
    return "N/A";
  }

  const percentValue = options?.alreadyPercent ? value : value * 100;
  return `${percentValue > 0 ? "+" : ""}${percentValue.toFixed(2)}%`;
};

const formatUnsignedPercent = (value: number | null) => {
  if (value === null || !Number.isFinite(value)) {
    return "N/A";
  }

  const percentValue = Math.abs(value) <= 1 ? value * 100 : value;
  return `${percentValue.toFixed(2)}%`;
};

const getSignalCount = (summary: RecommendationSummary | null, signal: RecommendationSignal) => {
  if (!summary) {
    return 0;
  }

  if (signal === "BUY") {
    return summary.buy_count;
  }
  if (signal === "HOLD") {
    return summary.hold_count;
  }
  return summary.sell_count;
};

const findSummaryRow = (rows: BacktestSummaryRow[], signal: BacktestSignal) =>
  rows.find((row) => normalizeSignal(row.signal) === signal);

const findBacktestMetric = (
  summaryRows: BacktestSummaryRow[],
  metrics: BacktestMetricRow[],
  signal: BacktestSignal,
  field: "win_rate" | "avg_next_return" | "nb_obs",
) => {
  const directMetric = metrics.find((metric) => normalizeSignal(metric.signal) === signal);
  const directValue = parseNumber(directMetric?.[field]);
  if (directValue !== null) {
    return directValue;
  }

  const namedMetric = metrics.find((metric) => {
    if (!metric.metric) {
      return false;
    }

    const metricKey = normalizeKey(metric.metric);
    return metricKey.includes(signal.toLowerCase()) && metricKey.includes(normalizeKey(field));
  });
  const metricValue = parseNumber(namedMetric?.value);

  return metricValue ?? parseNumber(findSummaryRow(summaryRows, signal)?.[field]);
};

const signalClass = (signal: string) => `dashboard-signal-${signal.toLowerCase()}`;

function ExecutiveKpiCard({ title, value, detail, icon: Icon, tone }: ExecutiveKpi) {
  return (
    <article className={`dashboard-kpi-card dashboard-kpi-card-${tone}`}>
      <div className="kpi-card-header">
        <span>{title}</span>
        <span className="kpi-icon">
          <Icon size={18} />
        </span>
      </div>
      <strong>{value}</strong>
      <p>{detail}</p>
    </article>
  );
}

export default function Dashboard() {
  const [data, setData] = useState<DashboardData>(emptyDashboardData);
  const [errors, setErrors] = useState<Partial<Record<EndpointKey, string>>>({});
  const [isLoading, setIsLoading] = useState(true);

  const fetchDashboard = useCallback(async () => {
    setIsLoading(true);

    const results = await Promise.all([
      fetchEndpoint("health", "/api/health"),
      fetchEndpoint("recommendationSummary", "/api/recommendations/summary"),
      fetchEndpoint("recommendations", "/api/recommendations/latest"),
      fetchEndpoint("backtestSummary", "/api/backtest/summary"),
      fetchEndpoint("backtestMetrics", "/api/backtest/metrics"),
      fetchEndpoint("portfolioSummary", "/api/portfolio/summary"),
      fetchEndpoint("portfolioAllocation", "/api/portfolio/allocation"),
      fetchEndpoint("marketSummary", "/api/market/summary", buildQueryParams({ ticker: "^GSPC" })),
      fetchEndpoint("macroSummary", "/api/macro/summary", buildQueryParams({ series_id: "UNRATE" })),
      fetchEndpoint("performanceSummary", "/api/performance/summary", buildQueryParams({ ticker: "AAPL" })),
      fetchEndpoint(
        "energySummary",
        "/api/energy/summary",
        buildQueryParams({ oil_ticker: "BZ=F", asset_ticker: "AAPL" }),
      ),
    ]);

    const nextData: DashboardData = { ...emptyDashboardData };
    const nextErrors: Partial<Record<EndpointKey, string>> = {};

    results.forEach((result) => {
      if (!result.ok) {
        nextErrors[result.key] = result.error ?? "Unavailable";
        return;
      }

      if (result.key === "health") {
        nextData.health = result.data;
      } else if (result.key === "recommendationSummary") {
        nextData.recommendationSummary = normalizeRecommendationSummary(result.data);
      } else if (result.key === "recommendations") {
        nextData.recommendations = normalizeRecommendations(result.data);
      } else if (result.key === "backtestSummary") {
        nextData.backtestSummary = normalizeBacktestSummary(result.data);
      } else if (result.key === "backtestMetrics") {
        nextData.backtestMetrics = normalizeBacktestMetrics(result.data);
      } else if (result.key === "portfolioSummary") {
        nextData.portfolioSummary = normalizePortfolioSummary(result.data);
      } else if (result.key === "portfolioAllocation") {
        nextData.portfolioAllocation = normalizePortfolioAllocation(result.data);
      } else if (result.key === "marketSummary") {
        nextData.marketSummary = normalizeMarketSummary(result.data);
      } else if (result.key === "macroSummary") {
        nextData.macroSummary = normalizeMacroSummary(result.data);
      } else if (result.key === "performanceSummary") {
        nextData.performanceSummary = normalizePerformanceSummary(result.data);
      } else if (result.key === "energySummary") {
        nextData.energySummary = normalizeEnergySummary(result.data);
      }
    });

    setData(nextData);
    setErrors(nextErrors);
    setIsLoading(false);
  }, []);

  useEffect(() => {
    void fetchDashboard();
  }, [fetchDashboard]);

  const hasAnyData = Object.values(data).some((value) => (Array.isArray(value) ? value.length > 0 : value !== null));
  const buyWinRate = findBacktestMetric(data.backtestSummary, data.backtestMetrics, "BUY", "win_rate");
  const topRecommendations = useMemo(
    () =>
      [...data.recommendations]
        .sort((left, right) => (right.advisor_score ?? -Infinity) - (left.advisor_score ?? -Infinity))
        .slice(0, 3),
    [data.recommendations],
  );
  const signalMetrics = useMemo(
    () =>
      SIGNALS.map((signal) => ({
        signal,
        count: getSignalCount(data.recommendationSummary, signal),
        winRate: findBacktestMetric(data.backtestSummary, data.backtestMetrics, signal, "win_rate"),
      })),
    [data.backtestMetrics, data.backtestSummary, data.recommendationSummary],
  );
  const topHoldings = useMemo(
    () =>
      [...data.portfolioAllocation]
        .sort((left, right) => (right.weight ?? -Infinity) - (left.weight ?? -Infinity))
        .slice(0, 5),
    [data.portfolioAllocation],
  );
  const maxWeight = Math.max(...topHoldings.map((row) => row.weight ?? 0), 0.001);
  const totalRecommendations = data.recommendationSummary?.total_recommendations ?? null;
  const totalSignalCount = SIGNALS.reduce((total, signal) => total + getSignalCount(data.recommendationSummary, signal), 0);

  const moduleStatuses: DashboardModuleStatus[] = [
    {
      key: "api",
      title: "API Health",
      status: data.health ? "online" : "offline",
      detail: data.health ? "FastAPI responded" : errors.health ?? "Health endpoint unavailable",
    },
    {
      key: "market",
      title: "BI Market Layer",
      status:
        data.marketSummary && data.macroSummary && data.performanceSummary && data.energySummary
          ? "online"
          : data.marketSummary || data.macroSummary || data.performanceSummary || data.energySummary
            ? "partial"
            : "offline",
      detail: data.marketSummary ? "Market, macro, performance, energy context" : errors.marketSummary ?? "BI data unavailable",
    },
    {
      key: "advisor",
      title: "AI Advisor",
      status: data.recommendationSummary && data.recommendations.length > 0 ? "online" : data.recommendationSummary ? "partial" : "offline",
      detail: data.recommendationSummary
        ? `${formatCount(totalRecommendations)} recommendations`
        : errors.recommendationSummary ?? "Advisor data unavailable",
    },
    {
      key: "backtest",
      title: "Backtest",
      status: data.backtestSummary.length > 0 || data.backtestMetrics.length > 0 ? "online" : "offline",
      detail: buyWinRate !== null ? `BUY win rate ${formatUnsignedPercent(buyWinRate)}` : errors.backtestSummary ?? "Backtest unavailable",
    },
    {
      key: "portfolio",
      title: "Portfolio",
      status: data.portfolioSummary && data.portfolioAllocation.length > 0 ? "online" : data.portfolioSummary ? "partial" : "offline",
      detail: data.portfolioSummary?.risk_level ?? errors.portfolioSummary ?? "Portfolio unavailable",
    },
  ];

  const executiveKpis: ExecutiveKpi[] = [
    {
      title: "Total Recommendations",
      value: formatCount(totalRecommendations),
      detail: "Latest AI Advisor universe",
      icon: Brain,
      tone: "neutral",
    },
    {
      title: "BUY / HOLD / SELL Mix",
      value: `${getSignalCount(data.recommendationSummary, "BUY")} / ${getSignalCount(data.recommendationSummary, "HOLD")} / ${getSignalCount(data.recommendationSummary, "SELL")}`,
      detail: totalSignalCount > 0 ? "Signal distribution loaded" : "Signal mix unavailable",
      icon: Sparkles,
      tone: "purple",
    },
    {
      title: "Top Advisor Score",
      value: formatDecimal(data.recommendationSummary?.top_advisor_score ?? null, 3),
      detail: "Highest explainable recommendation score",
      icon: Activity,
      tone: "positive",
    },
    {
      title: "Portfolio Expected Return",
      value: formatSignedPercent(data.portfolioSummary?.expected_return ?? null),
      detail: data.portfolioSummary?.risk_level ?? "Portfolio summary",
      icon: WalletCards,
      tone: "positive",
    },
    {
      title: "Portfolio Risk Level",
      value: data.portfolioSummary?.risk_level ?? "N/A",
      detail: `Risk score ${formatDecimal(data.portfolioSummary?.risk_score ?? null, 3)}`,
      icon: ShieldCheck,
      tone: "risk",
    },
    {
      title: "Backtest BUY Win Rate",
      value: formatUnsignedPercent(buyWinRate),
      detail: "Historical validation for BUY signals",
      icon: ChartNoAxesCombined,
      tone: "positive",
    },
    {
      title: "AAPL Cumulative Return",
      value: formatSignedPercent(data.performanceSummary?.cumulative_return_pct ?? null, { alreadyPercent: true }),
      detail: "Performance Analysis endpoint",
      icon: TrendingUp,
      tone: (data.performanceSummary?.cumulative_return_pct ?? 0) >= 0 ? "positive" : "negative",
    },
    {
      title: "S&P 500 Market Return",
      value: formatSignedPercent(data.marketSummary?.period_return_pct ?? null, { alreadyPercent: true }),
      detail: "Market Overview benchmark",
      icon: LineChart,
      tone: (data.marketSummary?.period_return_pct ?? 0) >= 0 ? "positive" : "negative",
    },
    {
      title: "UNRATE Latest Value",
      value: formatDecimal(data.macroSummary?.latest_value ?? null, 2),
      detail: "Macro Analysis labor context",
      icon: Globe2,
      tone: "purple",
    },
    {
      title: "Oil / AAPL Correlation",
      value: formatDecimal(data.energySummary?.global_correlation ?? null, 3),
      detail: data.energySummary?.global_correlation_label ?? "Energy Market context",
      icon: Droplets,
      tone: "risk",
    },
  ];

  const pipelineSteps = [
    { icon: DatabaseZap, label: "Data Sources", detail: "Market, macro, oil and model feature inputs" },
    { icon: Layers3, label: "PostgreSQL DW", detail: "Curated analytical views for BI and AI" },
    { icon: BarChart3, label: "BI Dashboards", detail: "Market, macro, energy and performance context" },
    { icon: Brain, label: "XGBoost Model", detail: "Directional prediction features power the advisor" },
    { icon: Sparkles, label: "AI Advisor", detail: "Explainable BUY / HOLD / SELL signals" },
    { icon: ChartNoAxesCombined, label: "Backtesting", detail: "Historical validation of signal behavior" },
    { icon: PieChart, label: "Portfolio Simulation", detail: "Allocation view from signals and risk" },
  ];

  const modules = [
    { icon: Layers3, title: "Platform Concept", path: "/platform-concept", detail: "Architecture, BI + AI workflow and CRISP-DM alignment" },
    { icon: LineChart, title: "Market Overview", path: "/market-overview", detail: "Price, volume and market movement" },
    { icon: Globe2, title: "Macro Analysis", path: "/macro-analysis", detail: "Economic context" },
    { icon: Activity, title: "Performance Analysis", path: "/performance-analysis", detail: "Returns, risk, drawdown" },
    { icon: Droplets, title: "Energy Market", path: "/energy-market", detail: "Oil-market context and correlations" },
    { icon: Brain, title: "AI Advisor", path: "/ai-advisor", detail: "BUY/HOLD/SELL explainable recommendations" },
    { icon: ChartNoAxesCombined, title: "Backtest", path: "/backtest", detail: "Historical validation" },
    { icon: WalletCards, title: "Portfolio", path: "/portfolio", detail: "Allocation simulation" },
  ];

  return (
    <section className="page-stack dashboard-page">
      <div className="page-hero hero-dashboard dashboard-executive-hero">
        <div className="hero-copy">
          <span className="eyebrow">Executive Overview</span>
          <h1>SmartInvest AI</h1>
          <p>Business Intelligence + Artificial Intelligence for investment decision support.</p>
          <p>From market, macro and energy data to AI recommendations, backtesting and portfolio simulation.</p>
          <div className="dashboard-hero-badges">
            <span>PostgreSQL Data Warehouse</span>
            <span>FastAPI + React</span>
            <span>Explainable AI</span>
          </div>
        </div>
        <div className="hero-visual" aria-hidden="true">
          <div className="dashboard-command-center">
            <span />
            <span />
            <span />
            <span />
          </div>
          <div className="hero-card hero-card-secondary">
            <span>Platform State</span>
            <strong>{isLoading ? "Loading" : hasAnyData ? "Live" : "Offline"}</strong>
          </div>
        </div>
      </div>

      <div className="dashboard-toolbar">
        <button className="primary-button" type="button" onClick={() => void fetchDashboard()} disabled={isLoading}>
          <RefreshCw size={18} />
          Refresh Dashboard
        </button>
        {isLoading && <Loader label="Loading executive dashboard" />}
      </div>

      {!isLoading && !hasAnyData && (
        <ErrorMessage
          title="Backend data unavailable"
          message="The executive concept is still visible below. Start FastAPI and refresh to populate live BI + AI metrics."
        />
      )}

      <div className="dashboard-status-grid">
        {moduleStatuses.map((module) => {
          const Icon = module.status === "online" ? CheckCircle2 : module.status === "partial" ? CircleAlert : CircleDot;
          return (
            <article className={`dashboard-status-card dashboard-status-${module.status}`} key={module.key}>
              <div>
                <span>{module.title}</span>
                <strong>{module.status}</strong>
              </div>
              <Icon size={22} />
              <p>{module.detail}</p>
            </article>
          );
        })}
      </div>

      <div className="dashboard-kpi-grid">
        {executiveKpis.map((kpi) => (
          <ExecutiveKpiCard key={kpi.title} {...kpi} />
        ))}
      </div>

      <div className="content-panel dashboard-pipeline-panel">
        <div className="panel-heading-row">
          <div>
            <span className="eyebrow">BI + AI Pipeline</span>
            <h2>End-to-end investment decision workflow</h2>
          </div>
          <Route size={22} />
        </div>
        <div className="dashboard-pipeline">
          {pipelineSteps.map((step) => {
            const Icon = step.icon;
            return (
              <article className="dashboard-pipeline-step" key={step.label}>
                <span className="dashboard-pipeline-icon">
                  <Icon size={18} />
                </span>
                <strong>{step.label}</strong>
                <p>{step.detail}</p>
              </article>
            );
          })}
        </div>
      </div>

      <div className="dashboard-module-grid">
        {modules.map((module) => {
          const Icon = module.icon;
          return (
            <Link className="dashboard-module-card" key={module.path} to={module.path}>
              <span className="dashboard-module-icon">
                <Icon size={20} />
              </span>
              <strong>{module.title}</strong>
              <p>{module.detail}</p>
            </Link>
          );
        })}
      </div>

      <div className="dashboard-snapshot-grid">
        <div className="content-panel dashboard-snapshot-panel">
          <div className="panel-heading-row">
            <div>
              <span className="eyebrow">AI Snapshot</span>
              <h2>Top Recommendations</h2>
            </div>
            <Brain size={22} />
          </div>
          {topRecommendations.length > 0 ? (
            <div className="dashboard-recommendation-list">
              {topRecommendations.map((recommendation) => (
                <article className="dashboard-recommendation-card" key={`${recommendation.ticker}-${recommendation.signal}`}>
                  <div>
                    <strong>{recommendation.ticker}</strong>
                    <span className={`dashboard-signal-badge ${signalClass(recommendation.signal)}`}>{recommendation.signal}</span>
                  </div>
                  <dl>
                    <div>
                      <dt>Proba Up</dt>
                      <dd>{formatUnsignedPercent(recommendation.proba_up)}</dd>
                    </div>
                    <div>
                      <dt>Confidence</dt>
                      <dd>{recommendation.confidence ?? "N/A"}</dd>
                    </div>
                    <div>
                      <dt>Advisor Score</dt>
                      <dd>{formatDecimal(recommendation.advisor_score, 3)}</dd>
                    </div>
                  </dl>
                </article>
              ))}
            </div>
          ) : (
            <div className="table-empty-state">
              <strong>No recommendation snapshot available</strong>
              <span>{errors.recommendations ?? "Latest recommendations endpoint returned no rows."}</span>
            </div>
          )}
        </div>

        <div className="content-panel dashboard-snapshot-panel">
          <div className="panel-heading-row">
            <div>
              <span className="eyebrow">Validation</span>
              <h2>Signal Win Rates</h2>
            </div>
            <ChartNoAxesCombined size={22} />
          </div>
          <div className="dashboard-validation-bars">
            {signalMetrics.map((metric) => {
              const width = metric.winRate === null ? 0 : Math.min(100, Math.max(0, Math.abs(metric.winRate) <= 1 ? metric.winRate * 100 : metric.winRate));
              return (
                <div className="dashboard-validation-row" key={metric.signal}>
                  <div>
                    <span className={`dashboard-signal-badge ${signalClass(metric.signal)}`}>{metric.signal}</span>
                    <strong>{formatUnsignedPercent(metric.winRate)}</strong>
                  </div>
                  <span className="dashboard-validation-track">
                    <span className={`dashboard-validation-fill ${signalClass(metric.signal)}`} style={{ width: `${width}%` }} />
                  </span>
                </div>
              );
            })}
          </div>
        </div>

        <div className="content-panel dashboard-snapshot-panel dashboard-portfolio-panel">
          <div className="panel-heading-row">
            <div>
              <span className="eyebrow">Portfolio Snapshot</span>
              <h2>Top Holdings by Weight</h2>
              <p className="dashboard-panel-note">
                Expected return {formatSignedPercent(data.portfolioSummary?.expected_return ?? null)} · Risk level{" "}
                {data.portfolioSummary?.risk_level ?? "N/A"}
              </p>
            </div>
            <WalletCards size={22} />
          </div>
          {topHoldings.length > 0 ? (
            <div className="dashboard-holding-list">
              {topHoldings.map((holding) => {
                const width = Math.max(4, ((holding.weight ?? 0) / maxWeight) * 100);
                return (
                  <div className="dashboard-holding-row" key={holding.ticker}>
                    <div>
                      <strong>{holding.ticker}</strong>
                      <span>{formatUnsignedPercent(holding.weight)}</span>
                    </div>
                    <span className="dashboard-holding-track">
                      <span style={{ width: `${width}%` }} />
                    </span>
                  </div>
                );
              })}
            </div>
          ) : (
            <div className="table-empty-state">
              <strong>No portfolio allocation available</strong>
              <span>{errors.portfolioAllocation ?? "Portfolio allocation endpoint returned no rows."}</span>
            </div>
          )}
        </div>
      </div>

      <div className="content-panel split-panel interpretation-panel dashboard-interpretation-panel">
        <DatabaseZap className="panel-icon" size={32} />
        <div>
          <span className="eyebrow">Interpretation</span>
          <h2>What SmartInvest AI Demonstrates</h2>
          <p>
            SmartInvest AI is not only a dashboard; it is an end-to-end BI + AI decision workflow. BI explores market,
            macro, energy and performance context.
          </p>
          <p>
            AI predicts direction and generates explainable signals. Backtesting validates historical behavior, and
            portfolio simulation converts signals into an investable allocation view.
          </p>
          <p>Historical results do not guarantee future performance.</p>
        </div>
      </div>
    </section>
  );
}
