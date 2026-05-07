export type EnergyOilSeriesResponse = string[];

export type EnergyAssetResponse = string[];

export type EnergyOilDailyRow = {
  date_id: string;
  ticker: string;
  open: number | null;
  high: number | null;
  low: number | null;
  close: number | null;
  adj_close: number | null;
  volume: number | null;
  daily_return: number | null;
  daily_return_pct: number | null;
};

export type EnergySummary = {
  oil_ticker: string;
  asset_ticker: string;
  start_date: string | null;
  end_date: string | null;
  common_sessions: number | null;
  oil_last_close: number | null;
  oil_previous_close: number | null;
  oil_change_pct: number | null;
  oil_period_return_pct: number | null;
  oil_average_volume: number | null;
  oil_period_high: number | null;
  oil_period_low: number | null;
  oil_annualized_volatility_pct: number | null;
  global_correlation: number | null;
  global_correlation_label: string | null;
  latest_rolling_correlation: number | null;
  latest_rolling_correlation_label: string | null;
  corr_window: number | null;
  beta: number | null;
  alpha: number | null;
  r_squared: number | null;
};

export type EnergyMergedRow = {
  date_id: string;
  oil_ticker: string;
  asset_ticker: string;
  oil_close: number | null;
  oil_daily_return: number | null;
  oil_daily_return_pct: number | null;
  asset_daily_return: number | null;
  asset_daily_return_pct: number | null;
  rolling_correlation: number | null;
};

export type EnergyRollingCorrelationRow = {
  date_id: string;
  rolling_correlation: number | null;
};

export type EnergyScatterPoint = {
  date_id: string;
  oil_daily_return_pct: number | null;
  asset_daily_return_pct: number | null;
};

export type EnergyScatterRegression = {
  beta: number | null;
  alpha: number | null;
  r_squared: number | null;
  correlation: number | null;
};

export type EnergyScatterResponse = {
  points: EnergyScatterPoint[];
  regression: EnergyScatterRegression;
};
