import { BarChart3, CalendarRange } from "lucide-react";

export default function Backtest() {
  return (
    <section className="page-stack">
      <div className="page-heading">
        <span className="eyebrow">Backtest</span>
        <h1>Strategy Performance</h1>
        <p>Compare historical signals, drawdowns, and portfolio growth across model windows.</p>
      </div>

      <div className="content-panel split-panel">
        <BarChart3 className="panel-icon" size={32} />
        <div>
          <h2>Backtest analytics placeholder</h2>
          <p>Charts and metrics can be wired to backend backtest endpoints when the API contract is finalized.</p>
        </div>
      </div>

      <div className="compact-panel">
        <CalendarRange size={20} />
        <span>Historical ranges and benchmark selectors are ready to be added.</span>
      </div>
    </section>
  );
}
