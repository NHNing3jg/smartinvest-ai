export type MacroSeries = {
  series_id: string;
  label: string;
};

export type MacroDailyRow = {
  date_id: string;
  series_id: string;
  label: string;
  value: number | null;
};

export type MacroSummary = {
  series_id: string;
  label: string;
  start_date: string | null;
  end_date: string | null;
  observations: number | null;
  latest_value: number | null;
  previous_value: number | null;
  absolute_change: number | null;
  percent_change: number | null;
  period_change: number | null;
  period_change_pct: number | null;
  period_mean: number | null;
  period_std: number | null;
  period_min: number | null;
  period_max: number | null;
};

export type MacroYoyRow = {
  date_id: string;
  series_id: string;
  label: string;
  value: number | null;
  yoy_change_pct: number | null;
};
