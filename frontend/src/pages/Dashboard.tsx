import { Activity, Brain, ChartNoAxesCombined, WalletCards } from "lucide-react";

import KpiCard from "../components/ui/KpiCard";

export default function Dashboard() {
  return (
    <section className="page-stack">
      <div className="page-hero hero-dashboard">
        <div className="hero-copy">
          <span className="eyebrow">Overview</span>
          <h1>SmartInvest AI Dashboard</h1>
          <p>Monitor recommendations, portfolio posture, and backtest performance from one colorful workspace.</p>
        </div>
        <div className="hero-visual" aria-hidden="true">
          <div className="hero-card hero-card-primary">
            <span>AI Signal Flow</span>
            <strong>Ready</strong>
          </div>
          <div className="hero-card hero-card-secondary">
            <span>BI Layer</span>
            <strong>Live Shell</strong>
          </div>
        </div>
      </div>

      <div className="kpi-grid">
        <KpiCard title="Recommendations" value="Pending" detail="Backend connection planned" icon={Brain} />
        <KpiCard title="Advisor Score" value="--" detail="Awaiting latest model output" icon={Activity} />
        <KpiCard title="Backtest Return" value="--" detail="Historical strategy view" icon={ChartNoAxesCombined} />
        <KpiCard title="Portfolio Value" value="--" detail="Holdings snapshot placeholder" icon={WalletCards} />
      </div>

      <div className="content-panel feature-panel">
        <div>
          <span className="eyebrow">Market Workspace</span>
          <h2>Decision support with a competition-ready visual story</h2>
        </div>
        <p>
          This dashboard is ready for API-backed recommendation cards, portfolio metrics, and backtest charts once the
          FastAPI endpoints are connected.
        </p>
      </div>
    </section>
  );
}
