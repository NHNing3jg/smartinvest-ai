import { Activity, Brain, ChartNoAxesCombined, WalletCards } from "lucide-react";

import KpiCard from "../components/ui/KpiCard";

export default function Dashboard() {
  return (
    <section className="page-stack">
      <div className="page-heading">
        <span className="eyebrow">Overview</span>
        <h1>SmartInvest AI Dashboard</h1>
        <p>Monitor recommendations, portfolio posture, and backtest performance from one workspace.</p>
      </div>

      <div className="kpi-grid">
        <KpiCard title="Recommendations" value="Pending" detail="Backend connection planned" icon={Brain} />
        <KpiCard title="Advisor Score" value="--" detail="Latest model output" icon={Activity} />
        <KpiCard title="Backtest Return" value="--" detail="Historical strategy view" icon={ChartNoAxesCombined} />
        <KpiCard title="Portfolio Value" value="--" detail="Holdings snapshot" icon={WalletCards} />
      </div>

      <div className="content-panel">
        <div>
          <span className="eyebrow">Market Workspace</span>
          <h2>Decision support without noise</h2>
        </div>
        <p>
          This dashboard is ready for API-backed recommendation cards, portfolio metrics, and backtest charts once the
          FastAPI endpoints are connected.
        </p>
      </div>
    </section>
  );
}
