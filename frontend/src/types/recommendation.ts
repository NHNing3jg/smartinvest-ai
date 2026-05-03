export type RecommendationSignal = "BUY" | "HOLD" | "SELL";

export type Recommendation = {
  date_id: string;
  ticker: string;
  proba_up: number;
  predicted_direction: string;
  signal: RecommendationSignal;
  confidence: string;
  advisor_score: number;
  momentum_5: number;
  momentum_10: number;
  rolling_vol_10: number;
  oil_return: number;
  sp500_return: number;
  nasdaq_return: number;
  explanation: string;
};

export type RecommendationSummary = {
  total_recommendations: number;
  buy_count: number;
  hold_count: number;
  sell_count: number;
  average_proba_up: number | null;
  top_advisor_score: number | null;
};
