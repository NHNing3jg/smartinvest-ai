import type { RecommendationSignal } from "./recommendation";

export type BacktestSignal = RecommendationSignal;

export type BacktestSummaryRow = {
  signal: BacktestSignal | string;
  nb_obs?: number | null;
  avg_next_return?: number | null;
  median_next_return?: number | null;
  win_rate?: number | null;
  avg_proba_up?: number | null;
  avg_advisor_score?: number | null;
  [key: string]: unknown;
};

export type BacktestMetricRow = {
  metric?: string;
  signal?: BacktestSignal | string | null;
  value?: number | string | null;
  win_rate?: number | null;
  avg_next_return?: number | null;
  nb_obs?: number | null;
  [key: string]: unknown;
};

export type BacktestMetric = BacktestMetricRow;
