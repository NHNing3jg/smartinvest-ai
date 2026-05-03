import { PieChart, Plus } from "lucide-react";

export default function Portfolio() {
  return (
    <section className="page-stack">
      <div className="page-hero hero-portfolio">
        <div className="hero-copy">
          <span className="eyebrow">Portfolio</span>
          <h1>Holdings Workspace</h1>
          <p>Track positions, allocation, and recommendation alignment for a focused investment view.</p>
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
        <button className="primary-button" type="button">
          <Plus size={18} />
          Add Position
        </button>
      </div>

      <div className="content-panel split-panel empty-panel">
        <PieChart className="panel-icon" size={32} />
        <div>
          <h2>Portfolio data placeholder</h2>
          <p>Position tables, allocation charts, and risk summaries can connect to FastAPI portfolio routes later.</p>
        </div>
      </div>
    </section>
  );
}
