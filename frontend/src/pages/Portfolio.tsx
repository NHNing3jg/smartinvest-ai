import axios from "axios";
import type { CSSProperties } from "react";
import { useCallback, useEffect, useMemo, useState } from "react";
import {
  Activity,
  BrainCircuit,
  FileText,
  Gauge,
  PieChart,
  RefreshCw,
  Scale,
  ShieldCheck,
  WalletCards,
} from "lucide-react";

import { apiClient } from "../api/client";
import PortfolioTable from "../components/tables/PortfolioTable";
import AllocationBar from "../components/ui/AllocationBar";
import ErrorMessage from "../components/ui/ErrorMessage";
import KpiCard from "../components/ui/KpiCard";
import Loader from "../components/ui/Loader";
import type { PortfolioAllocationRow, PortfolioSummaryRow } from "../types/portfolio";

const DONUT_COLORS = ["#12d6c5", "#277dff", "#a88bff", "#ff7b7b", "#ffd86b", "#ff5da2", "#5df2a9"];

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

const normalizeKey = (value: string) => value.toLowerCase().replace(/[^a-z0-9]+/g, "_");

const normalizeAllocationRows = (payload: unknown): PortfolioAllocationRow[] => {
  if (!Array.isArray(payload)) {
    return [];
  }

  return payload.filter(isRecord).map((row) => ({
    ticker: parseText(row.ticker) ?? "N/A",
    signal: parseText(row.signal),
    confidence: parseText(row.confidence),
    proba_up: parseNumber(row.proba_up),
    advisor_score: parseNumber(row.advisor_score),
    expected_return: parseNumber(row.expected_return),
    risk_score: parseNumber(row.risk_score),
    weight: parseNumber(row.weight),
    explanation: parseText(row.explanation),
  }));
};

const normalizeSummary = (payload: unknown): PortfolioSummaryRow | null => {
  if (isRecord(payload)) {
    return {
      expected_return: parseNumber(payload.expected_return),
      risk_score: parseNumber(payload.risk_score),
      risk_level: parseText(payload.risk_level),
    };
  }

  if (!Array.isArray(payload)) {
    return null;
  }

  const metricMap = new Map<string, unknown>();
  payload.filter(isRecord).forEach((row) => {
    const metric = parseText(row.metric);

    if (metric) {
      metricMap.set(normalizeKey(metric), row.value);
    }
  });

  return {
    expected_return: parseNumber(metricMap.get("portfolio_expected_return")),
    risk_score: parseNumber(metricMap.get("portfolio_risk_score")),
    risk_level: parseText(metricMap.get("portfolio_risk_level")),
  };
};

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

    return `Portfolio request failed with status ${error.response.status}.`;
  }

  return "Unable to load portfolio data.";
};

const formatCount = (value: number) => value.toLocaleString();

const formatDecimal = (value: number | null, digits = 3) => {
  if (value === null || Number.isNaN(value)) {
    return "N/A";
  }

  return value.toFixed(digits);
};

const formatSignedPercent = (value: number | null) => {
  if (value === null || Number.isNaN(value)) {
    return "N/A";
  }

  const percentValue = value * 100;
  return `${percentValue > 0 ? "+" : ""}${percentValue.toFixed(2)}%`;
};

const formatWeight = (value: number | null) => {
  if (value === null || Number.isNaN(value)) {
    return "N/A";
  }

  const percentValue = Math.abs(value) <= 1 ? value * 100 : value;
  return `${percentValue.toFixed(2)}%`;
};

const sumWeights = (rows: PortfolioAllocationRow[]) => {
  const weights = rows.map((row) => row.weight).filter((value): value is number => value !== null);
  return weights.length === 0 ? null : weights.reduce((total, value) => total + value, 0);
};

const buildDonutBackground = (rows: PortfolioAllocationRow[], totalWeight: number | null) => {
  if (totalWeight === null || totalWeight <= 0) {
    return undefined;
  }

  let cursor = 0;
  const segments = rows
    .filter((row) => row.weight !== null && row.weight > 0)
    .map((row, index) => {
      const start = cursor;
      cursor += ((row.weight ?? 0) / totalWeight) * 100;
      return `${DONUT_COLORS[index % DONUT_COLORS.length]} ${start.toFixed(2)}% ${cursor.toFixed(2)}%`;
    });

  return segments.length > 0 ? `conic-gradient(${segments.join(", ")})` : undefined;
};

export default function Portfolio() {
  const [allocationRows, setAllocationRows] = useState<PortfolioAllocationRow[]>([]);
  const [summary, setSummary] = useState<PortfolioSummaryRow | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const fetchPortfolio = useCallback(async () => {
    setIsLoading(true);
    setErrorMessage(null);

    try {
      const [allocationResponse, summaryResponse] = await Promise.all([
        apiClient.get<unknown>("/api/portfolio/allocation"),
        apiClient.get<unknown>("/api/portfolio/summary"),
      ]);

      setAllocationRows(normalizeAllocationRows(allocationResponse.data));
      setSummary(normalizeSummary(summaryResponse.data));
    } catch (error) {
      setErrorMessage(getErrorMessage(error));
      setAllocationRows([]);
      setSummary(null);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    void fetchPortfolio();
  }, [fetchPortfolio]);

  const totalWeight = useMemo(() => sumWeights(allocationRows), [allocationRows]);
  const maxWeight = useMemo(() => Math.max(...allocationRows.map((row) => row.weight ?? 0), 0.001), [allocationRows]);
  const maxRiskScore = useMemo(
    () => Math.max(...allocationRows.map((row) => row.risk_score ?? 0), 0.001),
    [allocationRows],
  );
  const donutBackground = useMemo(
    () => buildDonutBackground(allocationRows, totalWeight),
    [allocationRows, totalWeight],
  );
  const donutStyle = donutBackground ? ({ background: donutBackground } as CSSProperties) : undefined;

  return (
    <section className="page-stack">
      <div className="page-hero hero-portfolio">
        <div className="hero-copy">
          <span className="eyebrow">Portfolio</span>
          <h1>AI Allocation Simulation</h1>
          <p>Convert FastAPI-backed recommendations into an investable allocation view with risk and weight context.</p>
        </div>
        <div className="hero-visual" aria-hidden="true">
          <div className="allocation-rings">
            <span />
            <span />
            <span />
          </div>
        </div>
      </div>

      <div className="toolbar-row">
        <button className="primary-button" type="button" onClick={() => void fetchPortfolio()} disabled={isLoading}>
          <RefreshCw size={18} />
          Refresh Portfolio
        </button>
      </div>

      {isLoading && (
        <div className="content-panel split-panel">
          <WalletCards className="panel-icon" size={32} />
          <Loader label="Loading portfolio data" />
        </div>
      )}

      {errorMessage && !isLoading && <ErrorMessage title="Portfolio unavailable" message={errorMessage} />}

      {!isLoading && !errorMessage && (
        <>
          <div className="kpi-grid portfolio-kpi-grid">
            <KpiCard
              title="Selected Assets"
              value={formatCount(allocationRows.length)}
              detail="Tickers returned by portfolio allocation API"
              icon={WalletCards}
            />
            <KpiCard
              title="Expected Return"
              value={formatSignedPercent(summary?.expected_return ?? null)}
              detail="Portfolio expected return from summary API"
              icon={Activity}
            />
            <KpiCard
              title="Risk Score"
              value={formatDecimal(summary?.risk_score ?? null, 4)}
              detail="Aggregate portfolio risk score"
              icon={Gauge}
            />
            <KpiCard
              title="Risk Level"
              value={summary?.risk_level ?? "N/A"}
              detail="Risk category returned by FastAPI"
              icon={ShieldCheck}
            />
            <KpiCard
              title="Total Weight"
              value={formatWeight(totalWeight)}
              detail="Sum of allocation weights"
              icon={Scale}
            />
          </div>

          <div className="portfolio-chart-grid">
            <div className="content-panel allocation-panel">
              <div className="panel-heading-row">
                <div>
                  <span className="eyebrow">Allocation</span>
                  <h2>Weight by Asset</h2>
                </div>
              </div>
              <div className="allocation-bar-stack">
                {allocationRows.length > 0 ? (
                  allocationRows.map((row) => (
                    <AllocationBar
                      key={`weight-${row.ticker}`}
                      label={row.ticker}
                      value={row.weight}
                      maxValue={maxWeight}
                      variant="weight"
                      formatter={formatWeight}
                    />
                  ))
                ) : (
                  <div className="table-empty-state">
                    <strong>No allocation weights available</strong>
                    <span>The API did not return allocation rows.</span>
                  </div>
                )}
              </div>
            </div>

            <div className="content-panel allocation-panel">
              <div className="panel-heading-row">
                <div>
                  <span className="eyebrow">Risk</span>
                  <h2>Risk Score by Asset</h2>
                </div>
              </div>
              <div className="allocation-bar-stack">
                {allocationRows.length > 0 ? (
                  allocationRows.map((row) => (
                    <AllocationBar
                      key={`risk-${row.ticker}`}
                      label={row.ticker}
                      value={row.risk_score}
                      maxValue={maxRiskScore}
                      variant="risk"
                      formatter={(value) => formatDecimal(value, 4)}
                    />
                  ))
                ) : (
                  <div className="table-empty-state">
                    <strong>No risk scores available</strong>
                    <span>The API did not return allocation rows.</span>
                  </div>
                )}
              </div>
            </div>

            <div className="content-panel allocation-donut-panel">
              <div className="panel-heading-row">
                <div>
                  <span className="eyebrow">Mix</span>
                  <h2>Allocation Donut</h2>
                </div>
              </div>
              {donutStyle ? (
                <div className="portfolio-donut-wrap">
                  <div className="portfolio-donut" style={donutStyle}>
                    <span>{formatWeight(totalWeight)}</span>
                    <strong>Total</strong>
                  </div>
                  <div className="portfolio-donut-legend">
                    {allocationRows
                      .filter((row) => row.weight !== null && row.weight > 0)
                      .map((row, index) => (
                        <div key={`legend-${row.ticker}`} className="portfolio-donut-legend-row">
                          <span style={{ background: DONUT_COLORS[index % DONUT_COLORS.length] }} />
                          <strong>{row.ticker}</strong>
                          <em>{formatWeight(row.weight)}</em>
                        </div>
                      ))}
                  </div>
                </div>
              ) : (
                <div className="table-empty-state">
                  <strong>No positive weights available</strong>
                  <span>The API did not return weights that can be drawn as a donut.</span>
                </div>
              )}
            </div>
          </div>

          <div className="content-panel split-panel interpretation-panel portfolio-interpretation-panel">
            <BrainCircuit className="panel-icon" size={32} />
            <div>
              <span className="eyebrow">Interpretation</span>
              <h2>How to read this simulation</h2>
              <p>
                The portfolio converts AI recommendations into an investable allocation using the real FastAPI
                portfolio outputs.
              </p>
              <p>
                Higher weights reflect stronger recommendation profiles, combining signals such as confidence,
                upside probability, advisor score, expected return, and risk.
              </p>
              <p>This is a simulation for decision support and is not financial advice.</p>
            </div>
          </div>

          <div className="content-panel recommendation-panel">
            <div className="panel-heading-row">
              <div>
                <span className="eyebrow">FastAPI Data</span>
                <h2>Portfolio Allocation</h2>
              </div>
              <PieChart size={22} />
            </div>
            <PortfolioTable rows={allocationRows} />
          </div>

          {allocationRows.some((row) => row.explanation) && (
            <div className="content-panel allocation-explanations-panel">
              <div className="panel-heading-row">
                <div>
                  <span className="eyebrow">Model Context</span>
                  <h2>AI Allocation Explanations</h2>
                </div>
                <FileText size={22} />
              </div>
              <div className="allocation-explanation-grid">
                {allocationRows
                  .filter((row) => row.explanation)
                  .map((row) => (
                    <article key={`explanation-${row.ticker}`} className="allocation-explanation-card">
                      <strong>{row.ticker}</strong>
                      <p>{row.explanation}</p>
                    </article>
                  ))}
              </div>
            </div>
          )}
        </>
      )}
    </section>
  );
}
