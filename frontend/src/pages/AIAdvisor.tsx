import { Brain, Filter, Sparkles } from "lucide-react";

export default function AIAdvisor() {
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
        <button className="icon-button" type="button" aria-label="Filter recommendations">
          <Filter size={18} />
        </button>
        <button className="primary-button" type="button">
          <Sparkles size={18} />
          Refresh View
        </button>
      </div>

      <div className="content-panel split-panel empty-panel">
        <Brain className="panel-icon" size={32} />
        <div>
          <h2>Latest recommendations will appear here</h2>
          <p>
            The page is structured for the future `/api/recommendations/latest` and `/api/recommendations/summary`
            responses, with no API data loaded yet.
          </p>
        </div>
      </div>
    </section>
  );
}
