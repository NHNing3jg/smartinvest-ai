export type BacktestMetric = {
  metric: string;
  value: number | string;
};

export type BacktestSeriesPoint = {
  date: string;
  strategy_value: number;
  benchmark_value?: number;
};
