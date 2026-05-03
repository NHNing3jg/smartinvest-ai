export type PortfolioPosition = {
  ticker: string;
  shares: number;
  average_cost: number;
  current_price?: number;
  market_value?: number;
  allocation_percent?: number;
};

export type PortfolioSummary = {
  total_value: number;
  cash_balance?: number;
  positions_count: number;
};
