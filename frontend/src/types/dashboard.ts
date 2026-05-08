import type { Recommendation, RecommendationSummary } from "./recommendation";
import type { BacktestMetricRow, BacktestSummaryRow } from "./backtest";
import type { PortfolioAllocationRow, PortfolioSummaryRow } from "./portfolio";
import type { MarketSummary } from "./market";
import type { MacroSummary } from "./macro";
import type { PerformanceSummary } from "./performance";
import type { EnergySummary } from "./energy";

export type DashboardModuleKey = "api" | "market" | "advisor" | "backtest" | "portfolio";

export type DashboardModuleStatus = {
  key: DashboardModuleKey;
  title: string;
  status: "online" | "partial" | "offline";
  detail: string;
};

export type DashboardData = {
  health: unknown | null;
  recommendationSummary: RecommendationSummary | null;
  recommendations: Recommendation[];
  backtestSummary: BacktestSummaryRow[];
  backtestMetrics: BacktestMetricRow[];
  portfolioSummary: PortfolioSummaryRow | null;
  portfolioAllocation: PortfolioAllocationRow[];
  marketSummary: MarketSummary | null;
  macroSummary: MacroSummary | null;
  performanceSummary: PerformanceSummary | null;
  energySummary: EnergySummary | null;
};
