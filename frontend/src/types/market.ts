export type MarketDailyRow = {
  date_id: string;
  ticker: string;
  open: number | null;
  high: number | null;
  low: number | null;
  close: number | null;
  volume: number | null;
};

export type MarketSummary = {
  ticker: string;
  start_date: string | null;
  end_date: string | null;
  observations: number | null;
  last_close: number | null;
  previous_close: number | null;
  price_change: number | null;
  price_change_pct: number | null;
  period_return_pct: number | null;
  average_volume: number | null;
  period_high: number | null;
  period_low: number | null;
  annualized_volatility_pct: number | null;
};

export type MarketReturnRow = {
  date_id: string;
  ticker: string;
  daily_return_pct: number | null;
};
