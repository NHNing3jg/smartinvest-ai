import {
  ArrowUpRight,
  BarChart3,
  Brain,
  CalendarRange,
  FileText,
  Filter,
  Gauge,
  ListChecks,
  RefreshCw,
  ShieldCheck,
  Sparkles,
  TrendingDown,
  TrendingUp,
} from "lucide-react";
import { useCallback, useEffect, useMemo, useState } from "react";
import axios from "axios";

import { apiClient } from "../api/client";
import RecommendationTable from "../components/tables/RecommendationTable";
import TopRecommendationsTable from "../components/tables/TopRecommendationsTable";
import ErrorMessage from "../components/ui/ErrorMessage";
import ExplanationCard from "../components/ui/ExplanationCard";
import KpiCard from "../components/ui/KpiCard";
import Loader from "../components/ui/Loader";
import RecommendationMetricBar from "../components/ui/RecommendationMetricBar";
import SignalDistribution from "../components/ui/SignalDistribution";
import type { Recommendation, RecommendationSummary } from "../types/recommendation";
import type { RecommendationSignal } from "../types/recommendation";

const SIGNALS: RecommendationSignal[] = ["BUY", "HOLD", "SELL"];
type SignalFilter = "ALL" | RecommendationSignal;

const formatCount = (value: number) => value.toLocaleString();

const formatMetric = (value: number | null, digits = 3) => {
  if (value === null || Number.isNaN(value)) {
    return "N/A";
  }

  return value.toFixed(digits);
};

const formatPercent = (value: number | null) => {
  if (value === null || Number.isNaN(value)) {
    return "N/A";
  }

  return `${(value * 100).toFixed(2)}%`;
};

const formatDateId = (value: string | null) => {
  if (!value) {
    return "N/A";
  }

  const dateMatch = value.match(/^(\d{4})-(\d{2})-(\d{2})/);

  if (dateMatch) {
    const [, year, month, day] = dateMatch;
    return new Intl.DateTimeFormat(undefined, {
      year: "numeric",
      month: "short",
      day: "2-digit",
    }).format(new Date(Number(year), Number(month) - 1, Number(day)));
  }

  return value;
};

const getFiniteNumber = (value: number | null | undefined) =>
  typeof value === "number" && Number.isFinite(value) ? value : null;

const getAverage = (values: Array<number | null>) => {
  const finiteValues = values.filter((value): value is number => value !== null);

  if (finiteValues.length === 0) {
    return null;
  }

  return finiteValues.reduce((total, value) => total + value, 0) / finiteValues.length;
};

const getMax = (values: Array<number | null>) => {
  const finiteValues = values.filter((value): value is number => value !== null);

  return finiteValues.length > 0 ? Math.max(...finiteValues) : null;
};

const getLatestDateId = (recommendations: Recommendation[]) => {
  const dateIds = recommendations
    .map((recommendation) => recommendation.date_id)
    .filter((dateId): dateId is string => typeof dateId === "string" && dateId.trim() !== "");

  if (dateIds.length === 0) {
    return null;
  }

  return dateIds.sort((left, right) => {
    const leftTime = Date.parse(left);
    const rightTime = Date.parse(right);

    if (Number.isFinite(leftTime) && Number.isFinite(rightTime)) {
      return rightTime - leftTime;
    }

    return right.localeCompare(left);
  })[0];
};

const getErrorMessage = (error: unknown) => {
  if (axios.isAxiosError(error)) {
    if (!error.response) {
      return "Could not reach the FastAPI backend. Make sure it is running on port 8000.";
    }

    const detail = error.response.data?.detail;
    if (typeof detail === "string") {
      return detail;
    }

    if (detail?.message) {
      return detail.message;
    }

    return `Request failed with status ${error.response.status}.`;
  }

  return "Unable to load recommendation data.";
};

export default function AIAdvisor() {
  const [recommendations, setRecommendations] = useState<Recommendation[]>([]);
  const [summary, setSummary] = useState<RecommendationSummary | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [signalFilter, setSignalFilter] = useState<SignalFilter>("ALL");
  const [confidenceFilter, setConfidenceFilter] = useState("ALL");
  const [minProbaUp, setMinProbaUp] = useState(0);

  const fetchRecommendations = useCallback(async () => {
    setIsLoading(true);
    setErrorMessage(null);

    try {
      const [latestResponse, summaryResponse] = await Promise.all([
        apiClient.get<Recommendation[]>("/api/recommendations/latest"),
        apiClient.get<RecommendationSummary>("/api/recommendations/summary"),
      ]);

      setRecommendations(latestResponse.data);
      setSummary(summaryResponse.data);
    } catch (error) {
      setErrorMessage(getErrorMessage(error));
      setRecommendations([]);
      setSummary(null);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    void fetchRecommendations();
  }, [fetchRecommendations]);

  const confidenceOptions = useMemo(
    () =>
      Array.from(
        new Set(
          recommendations
            .map((recommendation) => recommendation.confidence?.trim())
            .filter((confidence): confidence is string => Boolean(confidence)),
        ),
      ).sort((left, right) => left.localeCompare(right)),
    [recommendations],
  );

  useEffect(() => {
    if (confidenceFilter !== "ALL" && !confidenceOptions.includes(confidenceFilter)) {
      setConfidenceFilter("ALL");
    }
  }, [confidenceFilter, confidenceOptions]);

  const filteredRecommendations = useMemo(
    () =>
      recommendations.filter((recommendation) => {
        const signal = recommendation.signal?.toUpperCase();
        const confidence = recommendation.confidence?.trim() ?? "";
        const probaUp = getFiniteNumber(recommendation.proba_up);

        if (signalFilter !== "ALL" && signal !== signalFilter) {
          return false;
        }

        if (confidenceFilter !== "ALL" && confidence !== confidenceFilter) {
          return false;
        }

        return probaUp !== null && probaUp >= minProbaUp;
      }),
    [confidenceFilter, minProbaUp, recommendations, signalFilter],
  );

  const signalCounts = useMemo(
    () =>
      filteredRecommendations.reduce<Record<RecommendationSignal, number>>(
        (counts, recommendation) => {
          const signal = recommendation.signal?.toUpperCase();

          if (SIGNALS.includes(signal as RecommendationSignal)) {
            counts[signal as RecommendationSignal] += 1;
          }

          return counts;
        },
        { BUY: 0, HOLD: 0, SELL: 0 },
      ),
    [filteredRecommendations],
  );

  const averageProbaUp = useMemo(
    () => getAverage(filteredRecommendations.map((recommendation) => getFiniteNumber(recommendation.proba_up))),
    [filteredRecommendations],
  );
  const topAdvisorScore = useMemo(
    () => getMax(filteredRecommendations.map((recommendation) => getFiniteNumber(recommendation.advisor_score))),
    [filteredRecommendations],
  );
  const latestDateId = useMemo(() => getLatestDateId(filteredRecommendations), [filteredRecommendations]);

  const probabilityRanking = useMemo(
    () =>
      [...filteredRecommendations].sort(
        (left, right) => (getFiniteNumber(right.proba_up) ?? -Infinity) - (getFiniteNumber(left.proba_up) ?? -Infinity),
      ),
    [filteredRecommendations],
  );
  const advisorScoreRanking = useMemo(
    () =>
      [...filteredRecommendations].sort(
        (left, right) =>
          (getFiniteNumber(right.advisor_score) ?? -Infinity) - (getFiniteNumber(left.advisor_score) ?? -Infinity),
      ),
    [filteredRecommendations],
  );
  const advisorScoreMax = useMemo(
    () =>
      Math.max(
        ...filteredRecommendations.map((recommendation) => Math.abs(getFiniteNumber(recommendation.advisor_score) ?? 0)),
        0.001,
      ),
    [filteredRecommendations],
  );
  const topBuyRecommendations = useMemo(
    () =>
      filteredRecommendations
        .filter((recommendation) => recommendation.signal?.toUpperCase() === "BUY")
        .sort(
          (left, right) =>
            (getFiniteNumber(right.advisor_score) ?? -Infinity) - (getFiniteNumber(left.advisor_score) ?? -Infinity),
        )
        .slice(0, 5),
    [filteredRecommendations],
  );
  const topSellRecommendations = useMemo(
    () =>
      filteredRecommendations
        .filter((recommendation) => recommendation.signal?.toUpperCase() === "SELL")
        .sort(
          (left, right) =>
            (getFiniteNumber(left.advisor_score) ?? Infinity) - (getFiniteNumber(right.advisor_score) ?? Infinity),
        )
        .slice(0, 5),
    [filteredRecommendations],
  );

  const resetFilters = () => {
    setSignalFilter("ALL");
    setConfidenceFilter("ALL");
    setMinProbaUp(0);
  };

  return (
    <section className="page-stack">
      <div className="page-hero hero-advisor">
        <div className="hero-copy">
          <span className="eyebrow">AI Advisor</span>
          <h1>Recommendation Center</h1>
          <p>Review model-driven buy, hold, and sell signals with confidence and explanation context.</p>
        </div>
        <div className="hero-visual" aria-hidden="true">
          <div className="signal-strip">
            <span />
            <span />
            <span />
          </div>
          <div className="hero-card hero-card-primary">
            <span>Model Lens</span>
            <strong>Explainable</strong>
          </div>
        </div>
      </div>

      <div className="toolbar-row">
        <button
          className="primary-button"
          type="button"
          onClick={() => void fetchRecommendations()}
          disabled={isLoading}
        >
          <RefreshCw size={18} />
          Refresh View
        </button>
      </div>

      {isLoading && (
        <div className="content-panel split-panel">
          <Brain className="panel-icon" size={32} />
          <Loader label="Loading recommendations" />
        </div>
      )}

      {errorMessage && !isLoading && (
        <ErrorMessage title="Recommendations unavailable" message={errorMessage} />
      )}

      {!isLoading && !errorMessage && (
        <>
          <div className="content-panel advisor-filter-panel">
            <div className="panel-heading-row">
              <div>
                <span className="eyebrow">Frontend Filters</span>
                <h2>Refine Recommendations</h2>
              </div>
              <Filter size={22} />
            </div>
            <div className="advisor-filter-grid">
              <label className="advisor-filter-field">
                <span>Signal</span>
                <select value={signalFilter} onChange={(event) => setSignalFilter(event.target.value as SignalFilter)}>
                  <option value="ALL">ALL</option>
                  {SIGNALS.map((signal) => (
                    <option key={signal} value={signal}>
                      {signal}
                    </option>
                  ))}
                </select>
              </label>

              <label className="advisor-filter-field">
                <span>Confidence</span>
                <select value={confidenceFilter} onChange={(event) => setConfidenceFilter(event.target.value)}>
                  <option value="ALL">ALL</option>
                  {confidenceOptions.map((confidence) => (
                    <option key={confidence} value={confidence}>
                      {confidence}
                    </option>
                  ))}
                </select>
              </label>

              <div className="advisor-filter-field advisor-proba-filter">
                <span>Minimum Proba Up</span>
                <div className="advisor-range-control">
                  <input
                    type="range"
                    min="0"
                    max="1"
                    step="0.01"
                    value={minProbaUp}
                    onChange={(event) => setMinProbaUp(Number(event.target.value))}
                  />
                  <input
                    type="number"
                    min="0"
                    max="1"
                    step="0.01"
                    value={minProbaUp}
                    onChange={(event) => setMinProbaUp(Math.min(Math.max(Number(event.target.value), 0), 1))}
                  />
                </div>
              </div>

              <button className="secondary-button" type="button" onClick={resetFilters}>
                Reset Filters
              </button>
            </div>
          </div>

          <div className="kpi-grid advisor-kpi-grid">
            <KpiCard
              title="Filtered Recommendations"
              value={formatCount(filteredRecommendations.length)}
              detail="Rows matching the active filters"
              icon={Sparkles}
            />
            <KpiCard
              title="BUY Count"
              value={formatCount(signalCounts.BUY)}
              detail="Mint opportunity signals"
              icon={TrendingUp}
            />
            <KpiCard
              title="HOLD Count"
              value={formatCount(signalCounts.HOLD)}
              detail="Balanced watchlist signals"
              icon={ShieldCheck}
            />
            <KpiCard
              title="SELL Count"
              value={formatCount(signalCounts.SELL)}
              detail="Coral risk-off signals"
              icon={TrendingDown}
            />
            <KpiCard
              title="Average Proba Up"
              value={formatPercent(averageProbaUp)}
              detail="Mean upside probability in filtered rows"
              icon={Gauge}
            />
            <KpiCard
              title="Top Advisor Score"
              value={formatMetric(topAdvisorScore)}
              detail="Highest model-ranked score in view"
              icon={ArrowUpRight}
            />
            <KpiCard
              title="Latest Date"
              value={formatDateId(latestDateId)}
              detail="Most recent date_id in filtered rows"
              icon={CalendarRange}
            />
          </div>

          <div className="advisor-chart-grid">
            <div className="content-panel advisor-chart-panel">
              <div className="panel-heading-row">
                <div>
                  <span className="eyebrow">Probability Lens</span>
                  <h2>Probability of Upward Movement</h2>
                </div>
                <BarChart3 size={22} />
              </div>
              <div className="advisor-metric-bar-stack">
                {probabilityRanking.length > 0 ? (
                  probabilityRanking.map((recommendation) => (
                    <RecommendationMetricBar
                      key={`proba-${recommendation.date_id}-${recommendation.ticker}`}
                      label={recommendation.ticker}
                      value={recommendation.proba_up}
                      maxValue={1}
                      formatter={formatPercent}
                      variant="probability"
                    />
                  ))
                ) : (
                  <div className="table-empty-state">
                    <strong>No probability data available</strong>
                    <span>No filtered rows include proba_up values.</span>
                  </div>
                )}
              </div>
            </div>

            <div className="content-panel advisor-chart-panel">
              <div className="panel-heading-row">
                <div>
                  <span className="eyebrow">Ranking</span>
                  <h2>Advisor Score Ranking</h2>
                </div>
                <ListChecks size={22} />
              </div>
              <div className="advisor-metric-bar-stack">
                {advisorScoreRanking.length > 0 ? (
                  advisorScoreRanking.map((recommendation) => (
                    <RecommendationMetricBar
                      key={`score-${recommendation.date_id}-${recommendation.ticker}`}
                      label={recommendation.ticker}
                      value={recommendation.advisor_score}
                      maxValue={advisorScoreMax}
                      formatter={(value) => formatMetric(value)}
                      variant={recommendation.signal?.toLowerCase() as "buy" | "hold" | "sell"}
                    />
                  ))
                ) : (
                  <div className="table-empty-state">
                    <strong>No advisor scores available</strong>
                    <span>No filtered rows include advisor_score values.</span>
                  </div>
                )}
              </div>
            </div>

            <div className="content-panel advisor-chart-panel advisor-distribution-panel">
              <div className="panel-heading-row">
                <div>
                  <span className="eyebrow">Signal Mix</span>
                  <h2>Signal Distribution</h2>
                </div>
              </div>
              <SignalDistribution counts={signalCounts} total={filteredRecommendations.length} />
            </div>
          </div>

          <div className="top-recommendations-grid">
            <div className="content-panel recommendation-panel">
              <div className="panel-heading-row">
                <div>
                  <span className="eyebrow">Top BUY</span>
                  <h2>Top BUY Opportunities</h2>
                </div>
                <TrendingUp size={22} />
              </div>
              <TopRecommendationsTable
                recommendations={topBuyRecommendations}
                emptyTitle="No BUY opportunities in this view"
                emptyDetail="Adjust the filters to include BUY signals returned by the API."
                formatPercent={formatPercent}
                formatNumber={formatMetric}
              />
            </div>

            <div className="content-panel recommendation-panel">
              <div className="panel-heading-row">
                <div>
                  <span className="eyebrow">Top SELL</span>
                  <h2>Top SELL Alerts</h2>
                </div>
                <TrendingDown size={22} />
              </div>
              <TopRecommendationsTable
                recommendations={topSellRecommendations}
                emptyTitle="No SELL alerts in this view"
                emptyDetail="Adjust the filters to include SELL signals returned by the API."
                formatPercent={formatPercent}
                formatNumber={formatMetric}
              />
            </div>
          </div>

          <div className="content-panel advisor-explanations-panel">
            <div className="panel-heading-row">
              <div>
                <span className="eyebrow">Model Context</span>
                <h2>AI Explanations by Asset</h2>
              </div>
              <FileText size={22} />
            </div>
            {filteredRecommendations.length > 0 ? (
              <div className="advisor-explanation-grid">
                {filteredRecommendations.map((recommendation) => (
                  <ExplanationCard
                    key={`explanation-${recommendation.date_id}-${recommendation.ticker}`}
                    recommendation={recommendation}
                    formatPercent={formatPercent}
                    formatNumber={formatMetric}
                  />
                ))}
              </div>
            ) : (
              <div className="table-empty-state">
                <strong>No explanations in this view</strong>
                <span>The active filters do not match any recommendations returned by the API.</span>
              </div>
            )}
          </div>

          <div className="content-panel recommendation-panel">
            <div className="panel-heading-row">
              <div>
                <span className="eyebrow">Live API Data</span>
                <h2>Latest Recommendations</h2>
              </div>
            </div>
            <RecommendationTable recommendations={filteredRecommendations} />
          </div>

          {summary && (
            <div className="compact-panel">
              <Sparkles size={20} />
              <span>
                Summary endpoint loaded {formatCount(summary.total_recommendations)} total rows; dashboard KPIs above
                are recalculated from the filtered recommendations.
              </span>
            </div>
          )}
        </>
      )}
    </section>
  );
}
