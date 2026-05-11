export type ModelMetricKey = "accuracy" | "precision" | "recall" | "f1_score";

export type ModelClassificationMetrics = {
  model_name: string;
  metric_type: string;
  timestamp: string;
  observations: number;
  accuracy: number;
  precision: number;
  recall: number;
  f1_score: number;
};

export type ModelComparisonRow = Record<string, string>;
