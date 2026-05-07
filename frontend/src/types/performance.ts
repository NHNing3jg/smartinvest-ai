export type PerformanceDailyRow = {
  date_id: string;
  ticker: string;
  close: number | null;
  close_prev: number | null;
  daily_return: number | null;
  daily_return_pct: number | null;
};

export type PerformanceCumulativeRow = {
  date_id: string;
  ticker: string;
  daily_return: number | null;
  cumulative_return_pct: number | null;
};

export type PerformanceSummary = {
  ticker: string;
  start_date: string | null;
  end_date: string | null;
  observations: number | null;
  start_close: number | null;
  last_close: number | null;
  cumulative_return_pct: number | null;
  annualized_return_pct: number | null;
  annualized_volatility_pct: number | null;
  sharpe_ratio: number | null;
  max_drawdown_pct: number | null;
  win_rate_pct: number | null;
  best_daily_return_pct: number | null;
  worst_daily_return_pct: number | null;
  average_daily_return_pct: number | null;
};

export type PerformanceRankingRow = {
  ticker: string;
  start_date: string | null;
  end_date: string | null;
  cumulative_return_pct: number | null;
};

export type PerformanceRankingResponse = {
  top: PerformanceRankingRow[];
  worst: PerformanceRankingRow[];
};

export type PerformanceCompareRow = {
  date_id: string;
  ticker: string;
  cumulative_return_pct: number | null;
};

export type PerformanceCumReturnRow = {
  date_id: string;
  ticker: string;
  cum_return: number | null;
  cum_return_pct: number | null;
};
