export type RecommendationSignal = "BUY" | "HOLD" | "SELL";

export type Recommendation = {
  date_id: string | null;
  ticker: string;
  proba_up: number | null;
  predicted_direction: string | null;
  signal: RecommendationSignal;
  confidence: string | null;
  advisor_score: number | null;
  momentum_5: number | null;
  momentum_10: number | null;
  rolling_vol_10: number | null;
  oil_return: number | null;
  sp500_return: number | null;
  nasdaq_return: number | null;
  explanation: string | null;
};

export type RecommendationSummary = {
  total_recommendations: number;
  buy_count: number;
  hold_count: number;
  sell_count: number;
  average_proba_up: number | null;
  top_advisor_score: number | null;
};
