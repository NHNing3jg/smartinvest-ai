import {
  ArrowUpRight,
  Brain,
  Gauge,
  RefreshCw,
  ShieldCheck,
  Sparkles,
  TrendingDown,
  TrendingUp,
} from "lucide-react";
import { useCallback, useEffect, useState } from "react";
import axios from "axios";

import { apiClient } from "../api/client";
import RecommendationTable from "../components/tables/RecommendationTable";
import ErrorMessage from "../components/ui/ErrorMessage";
import KpiCard from "../components/ui/KpiCard";
import Loader from "../components/ui/Loader";
import type { Recommendation, RecommendationSummary } from "../types/recommendation";

const formatCount = (value: number) => value.toLocaleString();

const formatMetric = (value: number | null, digits = 3) => {
  if (value === null || Number.isNaN(value)) {
    return "N/A";
  }

  return value.toFixed(digits);
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

      {summary && !isLoading && !errorMessage && (
        <div className="kpi-grid advisor-kpi-grid">
          <KpiCard
            title="Total Recommendations"
            value={formatCount(summary.total_recommendations)}
            detail="Signals returned by the advisor API"
            icon={Sparkles}
          />
          <KpiCard
            title="BUY Count"
            value={formatCount(summary.buy_count)}
            detail="Mint opportunity signals"
            icon={TrendingUp}
          />
          <KpiCard
            title="HOLD Count"
            value={formatCount(summary.hold_count)}
            detail="Balanced watchlist signals"
            icon={ShieldCheck}
          />
          <KpiCard
            title="SELL Count"
            value={formatCount(summary.sell_count)}
            detail="Coral risk-off signals"
            icon={TrendingDown}
          />
          <KpiCard
            title="Average Proba Up"
            value={formatMetric(summary.average_proba_up)}
            detail="Mean upside probability"
            icon={Gauge}
          />
          <KpiCard
            title="Top Advisor Score"
            value={formatMetric(summary.top_advisor_score)}
            detail="Highest model-ranked score"
            icon={ArrowUpRight}
          />
        </div>
      )}

      {!isLoading && !errorMessage && (
        <div className="content-panel recommendation-panel">
          <div className="panel-heading-row">
            <div>
              <span className="eyebrow">Live API Data</span>
              <h2>Latest Recommendations</h2>
            </div>
          </div>
          <RecommendationTable recommendations={recommendations} />
        </div>
      )}
    </section>
  );
}
