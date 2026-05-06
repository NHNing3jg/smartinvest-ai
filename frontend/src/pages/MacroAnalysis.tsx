import axios from "axios";
import { useCallback, useEffect, useMemo, useState } from "react";
import {
  Activity,
  BarChart3,
  CalendarDays,
  DatabaseZap,
  Gauge,
  LineChart as LineChartIcon,
  RefreshCw,
  Search,
  Sigma,
  TrendingUp,
  Waves,
} from "lucide-react";
import {
  CartesianGrid,
  Legend,
  Line,
  LineChart as RechartsLineChart,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import { apiClient } from "../api/client";
import ErrorMessage from "../components/ui/ErrorMessage";
import KpiCard from "../components/ui/KpiCard";
import Loader from "../components/ui/Loader";
import type { MacroDailyRow, MacroSeries, MacroSummary, MacroYoyRow } from "../types/macro";

type MacroChartPoint = {
  date: string;
  value: number;
};

type MacroYoyChartPoint = {
  date: string;
  yoy_change_pct: number;
};

type MacroTableRow = MacroDailyRow & {
  yoy_change_pct: number | null;
};

const DEFAULT_TABLE_LIMIT = 15;
const EXPANDED_TABLE_LIMIT = 50;
const MACRO_POINT_LIMIT = 320;
const YOY_POINT_LIMIT = 300;

const SERIES_DISPLAY_NAMES: Record<string, string> = {
  CPIAUCSL: "Consumer Price Index",
  FEDFUNDS: "Federal Funds Rate",
  GDP: "Gross Domestic Product",
  UNRATE: "Unemployment Rate",
};

const isRecord = (value: unknown): value is Record<string, unknown> =>
  typeof value === "object" && value !== null && !Array.isArray(value);

const parseNumber = (value: unknown): number | null => {
  if (typeof value === "number") {
    return Number.isFinite(value) ? value : null;
  }

  if (typeof value === "string" && value.trim() !== "") {
    const parsed = Number(value);
    return Number.isFinite(parsed) ? parsed : null;
  }

  return null;
};

const parseText = (value: unknown): string | null => {
  if (typeof value !== "string") {
    return null;
  }

  const trimmed = value.trim();
  return trimmed === "" ? null : trimmed;
};

const rowsFromPayload = (payload: unknown, nestedKeys: string[]): Record<string, unknown>[] => {
  if (Array.isArray(payload)) {
    return payload.filter(isRecord);
  }

  if (!isRecord(payload)) {
    return [];
  }

  for (const key of nestedKeys) {
    const nested = payload[key];
    if (Array.isArray(nested)) {
      return nested.filter(isRecord);
    }
  }

  return [];
};

const normalizeSeries = (payload: unknown): MacroSeries[] =>
  rowsFromPayload(payload, ["series", "data", "items"])
    .map((row) => {
      const seriesId = parseText(row.series_id);

      if (!seriesId) {
        return null;
      }

      return {
        series_id: seriesId,
        label: parseText(row.label) ?? seriesId,
      };
    })
    .filter((series): series is MacroSeries => series !== null);

const normalizeDailyRows = (payload: unknown): MacroDailyRow[] =>
  rowsFromPayload(payload, ["data", "rows", "items"]).map((row) => {
    const seriesId = parseText(row.series_id) ?? "N/A";

    return {
      date_id: parseText(row.date_id) ?? "N/A",
      series_id: seriesId,
      label: parseText(row.label) ?? seriesId,
      value: parseNumber(row.value),
    };
  });

const normalizeYoyRows = (payload: unknown): MacroYoyRow[] =>
  rowsFromPayload(payload, ["data", "rows", "items"]).map((row) => {
    const seriesId = parseText(row.series_id) ?? "N/A";

    return {
      date_id: parseText(row.date_id) ?? "N/A",
      series_id: seriesId,
      label: parseText(row.label) ?? seriesId,
      value: parseNumber(row.value),
      yoy_change_pct: parseNumber(row.yoy_change_pct),
    };
  });

const normalizeSummary = (payload: unknown): MacroSummary | null => {
  if (!isRecord(payload)) {
    return null;
  }

  return {
    series_id: parseText(payload.series_id) ?? "N/A",
    label: parseText(payload.label) ?? parseText(payload.series_id) ?? "N/A",
    start_date: parseText(payload.start_date),
    end_date: parseText(payload.end_date),
    observations: parseNumber(payload.observations),
    latest_value: parseNumber(payload.latest_value),
    previous_value: parseNumber(payload.previous_value),
    absolute_change: parseNumber(payload.absolute_change),
    percent_change: parseNumber(payload.percent_change),
    period_change: parseNumber(payload.period_change),
    period_change_pct: parseNumber(payload.period_change_pct),
    period_mean: parseNumber(payload.period_mean),
    period_std: parseNumber(payload.period_std),
    period_min: parseNumber(payload.period_min),
    period_max: parseNumber(payload.period_max),
  };
};

const buildQueryParams = (seriesId: string, startDate: string, endDate: string) => ({
  series_id: seriesId,
  ...(startDate.trim() ? { start_date: startDate.trim() } : {}),
  ...(endDate.trim() ? { end_date: endDate.trim() } : {}),
});

const getErrorMessage = (error: unknown) => {
  if (axios.isAxiosError(error)) {
    if (!error.response) {
      return "Could not reach the FastAPI backend. Start it with python -m uvicorn app.main:app --reload, then refresh this page.";
    }

    const detail = error.response.data?.detail;
    if (typeof detail === "string") {
      return detail;
    }

    if (detail?.message) {
      return detail.message;
    }

    return `Macro request failed with status ${error.response.status}.`;
  }

  return "Unable to load macro data.";
};

const formatNumber = (value: number | null) => {
  if (value === null || !Number.isFinite(value)) {
    return "N/A";
  }

  const absoluteValue = Math.abs(value);
  if (absoluteValue >= 1_000_000) {
    return Intl.NumberFormat(undefined, {
      notation: "compact",
      maximumFractionDigits: 2,
    }).format(value);
  }

  return value.toLocaleString(undefined, {
    minimumFractionDigits: absoluteValue < 10 ? 2 : 0,
    maximumFractionDigits: absoluteValue < 10 ? 3 : 2,
  });
};

const formatSignedNumber = (value: number | null) => {
  if (value === null || !Number.isFinite(value)) {
    return "N/A";
  }

  return `${value > 0 ? "+" : ""}${formatNumber(value)}`;
};

const formatPercent = (value: number | null) => {
  if (value === null || !Number.isFinite(value)) {
    return "N/A";
  }

  return `${value > 0 ? "+" : ""}${value.toFixed(2)}%`;
};

const formatDateLabel = (value: string | null | undefined) => {
  if (!value || value === "N/A") {
    return "N/A";
  }

  const parsedDate = new Date(value);

  if (Number.isNaN(parsedDate.getTime())) {
    return value;
  }

  return parsedDate.toLocaleDateString(undefined, {
    month: "short",
    day: "numeric",
    year: "2-digit",
  });
};

const formatMacroValue = (value: number | null) => formatNumber(value);

const formatCount = (value: number | null) => {
  if (value === null || !Number.isFinite(value)) {
    return "N/A";
  }

  return Math.round(value).toLocaleString();
};

const downsampleRows = <T,>(rows: T[], maxPoints: number) => {
  if (rows.length <= maxPoints) {
    return rows;
  }

  if (maxPoints <= 1) {
    return rows.slice(0, 1);
  }

  const step = (rows.length - 1) / (maxPoints - 1);
  const sampledRows: T[] = [];

  for (let index = 0; index < maxPoints; index += 1) {
    const row = rows[Math.round(index * step)];

    if (row !== undefined) {
      sampledRows.push(row);
    }
  }

  return sampledRows;
};

const sortDailyRowsAsc = (rows: MacroDailyRow[]) => [...rows].sort((left, right) => left.date_id.localeCompare(right.date_id));

const sortDailyRowsDesc = (rows: MacroDailyRow[]) =>
  [...rows].sort((left, right) => right.date_id.localeCompare(left.date_id));

const getLatestRows = (rows: MacroDailyRow[], yoyRows: MacroYoyRow[], limit: number): MacroTableRow[] => {
  const yoyByDate = new Map(yoyRows.map((row) => [row.date_id, row.yoy_change_pct]));

  return sortDailyRowsDesc(rows)
    .slice(0, limit)
    .map((row) => ({
      ...row,
      yoy_change_pct: yoyByDate.get(row.date_id) ?? null,
    }));
};

const getSeriesDisplayName = (seriesId: string, label?: string | null) => {
  const mappedLabel = SERIES_DISPLAY_NAMES[seriesId];
  if (mappedLabel) {
    return mappedLabel;
  }

  return label && label !== seriesId ? label : seriesId;
};

const buildSeriesChartData = (rows: MacroDailyRow[]): MacroChartPoint[] =>
  sortDailyRowsAsc(rows)
    .map((row) => ({
      date: row.date_id,
      value: row.value,
    }))
    .filter((row): row is MacroChartPoint => row.value !== null && Number.isFinite(row.value));

const buildYoyChartData = (rows: MacroYoyRow[]): MacroYoyChartPoint[] =>
  [...rows]
    .sort((left, right) => left.date_id.localeCompare(right.date_id))
    .map((row) => ({
      date: row.date_id,
      yoy_change_pct: row.yoy_change_pct,
    }))
    .filter((row): row is MacroYoyChartPoint => row.yoy_change_pct !== null && Number.isFinite(row.yoy_change_pct));

export default function MacroAnalysis() {
  const [series, setSeries] = useState<MacroSeries[]>([]);
  const [selectedSeriesId, setSelectedSeriesId] = useState("");
  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");
  const [summary, setSummary] = useState<MacroSummary | null>(null);
  const [dailyRows, setDailyRows] = useState<MacroDailyRow[]>([]);
  const [yoyRows, setYoyRows] = useState<MacroYoyRow[]>([]);
  const [isSeriesLoading, setIsSeriesLoading] = useState(true);
  const [isMacroLoading, setIsMacroLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [isTableExpanded, setIsTableExpanded] = useState(false);

  const fetchSeries = useCallback(async () => {
    setIsSeriesLoading(true);
    setErrorMessage(null);

    try {
      const response = await apiClient.get<unknown>("/api/macro/series");
      const macroSeries = normalizeSeries(response.data);
      const defaultSeriesId = macroSeries.some((item) => item.series_id === "UNRATE")
        ? "UNRATE"
        : macroSeries[0]?.series_id ?? "";

      setSeries(macroSeries);
      setSelectedSeriesId((currentSeriesId) =>
        macroSeries.some((item) => item.series_id === currentSeriesId) ? currentSeriesId : defaultSeriesId,
      );
    } catch (error) {
      setErrorMessage(getErrorMessage(error));
      setSeries([]);
      setSelectedSeriesId("");
      setSummary(null);
      setDailyRows([]);
      setYoyRows([]);
    } finally {
      setIsSeriesLoading(false);
    }
  }, []);

  const fetchMacroData = useCallback(async () => {
    if (!selectedSeriesId) {
      return;
    }

    setIsMacroLoading(true);
    setErrorMessage(null);

    const params = buildQueryParams(selectedSeriesId, startDate, endDate);

    try {
      const [summaryResponse, dailyResponse, yoyResponse] = await Promise.all([
        apiClient.get<unknown>("/api/macro/summary", { params }),
        apiClient.get<unknown>("/api/macro/daily", { params }),
        apiClient.get<unknown>("/api/macro/yoy", { params }),
      ]);

      setSummary(normalizeSummary(summaryResponse.data));
      setDailyRows(normalizeDailyRows(dailyResponse.data));
      setYoyRows(normalizeYoyRows(yoyResponse.data));
      setIsTableExpanded(false);
    } catch (error) {
      setErrorMessage(getErrorMessage(error));
      setSummary(null);
      setDailyRows([]);
      setYoyRows([]);
    } finally {
      setIsMacroLoading(false);
    }
  }, [endDate, selectedSeriesId, startDate]);

  useEffect(() => {
    void fetchSeries();
  }, [fetchSeries]);

  useEffect(() => {
    void fetchMacroData();
  }, [fetchMacroData]);

  const selectedSeries = useMemo(
    () => series.find((item) => item.series_id === selectedSeriesId) ?? null,
    [selectedSeriesId, series],
  );
  const displayName = getSeriesDisplayName(selectedSeriesId, selectedSeries?.label ?? summary?.label);
  const isLoading = isSeriesLoading || isMacroLoading;
  const tableLimit = isTableExpanded ? EXPANDED_TABLE_LIMIT : DEFAULT_TABLE_LIMIT;
  const tableRows = useMemo(() => getLatestRows(dailyRows, yoyRows, tableLimit), [dailyRows, tableLimit, yoyRows]);
  const canToggleTable = dailyRows.length > DEFAULT_TABLE_LIMIT;
  const seriesChartData = useMemo(
    () => downsampleRows(buildSeriesChartData(dailyRows), MACRO_POINT_LIMIT),
    [dailyRows],
  );
  const yoyChartData = useMemo(() => downsampleRows(buildYoyChartData(yoyRows), YOY_POINT_LIMIT), [yoyRows]);

  return (
    <section className="page-stack">
      <div className="page-hero hero-macro">
        <div className="hero-copy">
          <span className="eyebrow">Macro Analysis</span>
          <h1>Economic Context Layer</h1>
          <p>Explore macroeconomic indicators from PostgreSQL through the FastAPI macro endpoints.</p>
        </div>
        <div className="hero-visual" aria-hidden="true">
          <div className="macro-hero-bars">
            <span />
            <span />
            <span />
            <span />
          </div>
          <div className="hero-card hero-card-secondary">
            <span>Selected Indicator</span>
            <strong>{selectedSeriesId || "Loading"}</strong>
          </div>
        </div>
      </div>

      <div className="content-panel macro-filter-panel">
        <div className="panel-heading-row">
          <div>
            <span className="eyebrow">Filters</span>
            <h2>Macro Data Controls</h2>
          </div>
          <Search size={22} />
        </div>

        <div className="macro-filter-grid">
          <label className="advisor-filter-field">
            <span>Indicator</span>
            <select
              value={selectedSeriesId}
              onChange={(event) => setSelectedSeriesId(event.target.value)}
              disabled={isSeriesLoading || series.length === 0}
            >
              {series.length === 0 ? (
                <option value="">No macro series</option>
              ) : (
                series.map((item) => (
                  <option key={item.series_id} value={item.series_id}>
                    {getSeriesDisplayName(item.series_id, item.label)} ({item.series_id})
                  </option>
                ))
              )}
            </select>
          </label>

          <label className="advisor-filter-field">
            <span>Start Date</span>
            <input type="date" value={startDate} onChange={(event) => setStartDate(event.target.value)} />
          </label>

          <label className="advisor-filter-field">
            <span>End Date</span>
            <input type="date" value={endDate} onChange={(event) => setEndDate(event.target.value)} />
          </label>

          <div className="macro-filter-actions">
            <button
              className="primary-button"
              type="button"
              onClick={() => void fetchMacroData()}
              disabled={isLoading || !selectedSeriesId}
            >
              <RefreshCw size={18} />
              Refresh Macro
            </button>
            <button
              className="secondary-button"
              type="button"
              onClick={() => {
                setStartDate("");
                setEndDate("");
              }}
              disabled={isLoading || (!startDate && !endDate)}
            >
              Clear Dates
            </button>
          </div>
        </div>
      </div>

      {isLoading && (
        <div className="content-panel split-panel">
          <CalendarDays className="panel-icon" size={32} />
          <Loader label="Loading macro data" />
        </div>
      )}

      {errorMessage && !isLoading && <ErrorMessage title="Macro data unavailable" message={errorMessage} />}

      {!isLoading && !errorMessage && (
        <>
          <div className="kpi-grid macro-kpi-grid">
            <KpiCard title="Latest Value" value={formatMacroValue(summary?.latest_value ?? null)} detail={`${displayName} (${selectedSeriesId || "N/A"})`} icon={Gauge} />
            <KpiCard title="Absolute Change" value={formatSignedNumber(summary?.absolute_change ?? null)} detail={`Previous value ${formatMacroValue(summary?.previous_value ?? null)}`} icon={TrendingUp} />
            <KpiCard title="Percent Change" value={formatPercent(summary?.percent_change ?? null)} detail="Change from previous observation" icon={Activity} />
            <KpiCard title="Period Change %" value={formatPercent(summary?.period_change_pct ?? null)} detail="Change across selected period" icon={LineChartIcon} />
            <KpiCard title="Period Mean" value={formatMacroValue(summary?.period_mean ?? null)} detail="Average value in selected period" icon={Sigma} />
            <KpiCard title="Period Min / Max" value={`${formatMacroValue(summary?.period_min ?? null)} / ${formatMacroValue(summary?.period_max ?? null)}`} detail="Observed range in selected period" icon={BarChart3} />
            <KpiCard title="Period Std" value={formatMacroValue(summary?.period_std ?? null)} detail="Sample standard deviation" icon={Waves} />
            <KpiCard title="Observations" value={formatCount(summary?.observations ?? null)} detail={`${formatDateLabel(summary?.start_date)} to ${formatDateLabel(summary?.end_date)}`} icon={CalendarDays} />
          </div>

          <div className="macro-chart-grid">
            <div className="content-panel macro-line-panel">
              <div className="panel-heading-row">
                <div>
                  <span className="eyebrow">Series Evolution</span>
                  <h2>Macro Series Evolution</h2>
                  <p className="macro-chart-helper">{displayName} values returned by the daily macro endpoint.</p>
                </div>
              </div>

              {seriesChartData.length > 0 ? (
                <div className="macro-recharts-card">
                  <div className="macro-recharts-box macro-recharts-box-large">
                    <ResponsiveContainer width="100%" height="100%">
                      <RechartsLineChart data={seriesChartData} margin={{ top: 18, right: 22, left: 10, bottom: 12 }}>
                        <CartesianGrid stroke="rgba(83, 98, 123, 0.18)" strokeDasharray="3 4" vertical={false} />
                        <XAxis
                          dataKey="date"
                          minTickGap={30}
                          tickFormatter={formatDateLabel}
                          tick={{ fill: "#66738c", fontSize: 12, fontWeight: 700 }}
                          axisLine={{ stroke: "rgba(83, 98, 123, 0.22)" }}
                          tickLine={false}
                        />
                        <YAxis
                          width={72}
                          domain={["auto", "auto"]}
                          tickFormatter={(value) => formatNumber(Number(value))}
                          tick={{ fill: "#66738c", fontSize: 12, fontWeight: 700 }}
                          axisLine={false}
                          tickLine={false}
                        />
                        <Tooltip
                          cursor={{ stroke: "rgba(39, 125, 255, 0.24)", strokeWidth: 1 }}
                          contentStyle={{
                            border: "1px solid rgba(255, 255, 255, 0.82)",
                            borderRadius: 8,
                            background: "rgba(255, 255, 255, 0.94)",
                            boxShadow: "0 18px 36px rgba(47, 64, 101, 0.14)",
                          }}
                          formatter={(value) => [formatMacroValue(Number(value)), selectedSeriesId || "Value"]}
                          labelFormatter={(label) => `Date: ${formatDateLabel(String(label))}`}
                        />
                        <Legend wrapperStyle={{ color: "#53627b", fontWeight: 800, paddingTop: 8 }} />
                        <Line
                          type="monotone"
                          dataKey="value"
                          name={`${selectedSeriesId || "Macro"} value`}
                          stroke="#277dff"
                          strokeWidth={2.5}
                          dot={false}
                          activeDot={{ r: 4, strokeWidth: 2, stroke: "#ffffff" }}
                        />
                      </RechartsLineChart>
                    </ResponsiveContainer>
                  </div>
                  <div className="macro-chart-caption">
                    <span>{formatDateLabel(seriesChartData[0]?.date)}</span>
                    <strong>{selectedSeriesId}</strong>
                    <span>{formatDateLabel(seriesChartData[seriesChartData.length - 1]?.date)}</span>
                  </div>
                </div>
              ) : (
                <div className="table-empty-state">
                  <strong>No macro values available</strong>
                  <span>The API did not return numeric daily values for this selection.</span>
                </div>
              )}
            </div>

            <div className="content-panel macro-yoy-panel">
              <div className="panel-heading-row">
                <div>
                  <span className="eyebrow">Year over Year</span>
                  <h2>Year-over-Year Change</h2>
                  <p className="macro-chart-helper">Null year-over-year rows are skipped in this chart.</p>
                </div>
              </div>

              {yoyChartData.length > 0 ? (
                <div className="macro-recharts-card macro-recharts-card-compact">
                  <div className="macro-recharts-box">
                    <ResponsiveContainer width="100%" height="100%">
                      <RechartsLineChart data={yoyChartData} margin={{ top: 16, right: 20, left: 8, bottom: 10 }}>
                        <CartesianGrid stroke="rgba(83, 98, 123, 0.16)" strokeDasharray="3 4" vertical={false} />
                        <XAxis
                          dataKey="date"
                          minTickGap={30}
                          tickFormatter={formatDateLabel}
                          tick={{ fill: "#66738c", fontSize: 12, fontWeight: 700 }}
                          axisLine={{ stroke: "rgba(83, 98, 123, 0.22)" }}
                          tickLine={false}
                        />
                        <YAxis
                          width={68}
                          tickFormatter={(value) => formatPercent(Number(value))}
                          tick={{ fill: "#66738c", fontSize: 12, fontWeight: 700 }}
                          axisLine={false}
                          tickLine={false}
                        />
                        <Tooltip
                          cursor={{ stroke: "rgba(255, 93, 162, 0.2)", strokeWidth: 1 }}
                          contentStyle={{
                            border: "1px solid rgba(255, 255, 255, 0.82)",
                            borderRadius: 8,
                            background: "rgba(255, 255, 255, 0.94)",
                            boxShadow: "0 18px 36px rgba(47, 64, 101, 0.14)",
                          }}
                          formatter={(value) => [formatPercent(Number(value)), "YoY change"]}
                          labelFormatter={(label) => `Date: ${formatDateLabel(String(label))}`}
                        />
                        <Legend wrapperStyle={{ color: "#53627b", fontWeight: 800, paddingTop: 8 }} />
                        <ReferenceLine y={0} stroke="#53627b" strokeDasharray="4 5" />
                        <Line
                          type="monotone"
                          dataKey="yoy_change_pct"
                          name="YoY change %"
                          stroke="#ff5da2"
                          strokeWidth={2.4}
                          dot={false}
                          activeDot={{ r: 4, strokeWidth: 2, stroke: "#ffffff" }}
                        />
                      </RechartsLineChart>
                    </ResponsiveContainer>
                  </div>
                </div>
              ) : (
                <div className="table-empty-state">
                  <strong>No year-over-year values available</strong>
                  <span>The API returned no numeric YoY values for this selection.</span>
                </div>
              )}
            </div>
          </div>

          <div className="content-panel split-panel interpretation-panel macro-interpretation-panel">
            <DatabaseZap className="panel-icon" size={32} />
            <div>
              <span className="eyebrow">Context</span>
              <h2>Macro Indicator Context</h2>
              <p>
                This page explores macroeconomic indicators stored in PostgreSQL and served through the FastAPI macro
                layer.
              </p>
              <p>
                Macro indicators can provide broad economic context for investment decision support, especially when
                viewed alongside market, portfolio, backtest, and AI advisor workflows.
              </p>
              <p>The view is descriptive and does not make financial conclusions or recommendations.</p>
            </div>
          </div>

          <div className="content-panel recommendation-panel">
            <div className="panel-heading-row">
              <div>
                <span className="eyebrow">FastAPI Data</span>
                <h2>Latest Macro Observations</h2>
                <p className="macro-table-note">
                  Showing latest {tableRows.length.toLocaleString()} rows from the selected API result.
                </p>
              </div>
              {canToggleTable ? (
                <button
                  className="secondary-button macro-table-toggle"
                  type="button"
                  onClick={() => setIsTableExpanded((currentValue) => !currentValue)}
                >
                  {isTableExpanded ? "Show less" : "Show more"}
                </button>
              ) : (
                <CalendarDays size={22} />
              )}
            </div>

            {tableRows.length > 0 ? (
              <div className="recommendation-table-wrap">
                <table className="recommendation-table macro-table">
                  <thead>
                    <tr>
                      <th scope="col">Date</th>
                      <th scope="col">Series</th>
                      <th scope="col">Label</th>
                      <th scope="col">Value</th>
                      <th scope="col">YoY Change %</th>
                    </tr>
                  </thead>
                  <tbody>
                    {tableRows.map((row) => (
                      <tr key={`${row.series_id}-${row.date_id}`}>
                        <td data-label="Date">{row.date_id}</td>
                        <td data-label="Series">
                          <strong className="ticker-cell">{row.series_id}</strong>
                        </td>
                        <td data-label="Label">{getSeriesDisplayName(row.series_id, row.label)}</td>
                        <td data-label="Value">{formatMacroValue(row.value)}</td>
                        <td data-label="YoY Change %">{formatPercent(row.yoy_change_pct)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <div className="table-empty-state">
                <strong>No macro rows available</strong>
                <span>The API returned an empty daily macro data set.</span>
              </div>
            )}
          </div>
        </>
      )}
    </section>
  );
}
