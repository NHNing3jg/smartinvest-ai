export type PortfolioAllocationRow = {
  ticker: string;
  signal: string | null;
  confidence: string | null;
  proba_up: number | null;
  advisor_score: number | null;
  expected_return: number | null;
  risk_score: number | null;
  weight: number | null;
  explanation: string | null;
};

export type PortfolioSummaryRow = {
  expected_return: number | null;
  risk_score: number | null;
  risk_level: string | null;
};
