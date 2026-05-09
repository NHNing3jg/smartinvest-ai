import { BarChart3, Brain, Database, LineChart, PieChart, Server, Sparkles } from "lucide-react";
import type { LucideIcon } from "lucide-react";
import type { CSSProperties } from "react";

type FlowNode = {
  icon: LucideIcon;
  label: string;
};

const flowNodes: FlowNode[] = [
  { icon: Sparkles, label: "Data Sources" },
  { icon: Database, label: "PostgreSQL DW" },
  { icon: Server, label: "FastAPI" },
  { icon: BarChart3, label: "React BI" },
  { icon: Brain, label: "AI Advisor" },
  { icon: LineChart, label: "Backtest" },
  { icon: PieChart, label: "Portfolio" },
];

export default function DecisionFlowAnimation() {
  return (
    <section className="content-panel platform-decision-flow platform-dark-card motion-fade-up">
      <div className="panel-heading-row">
        <div>
          <span className="eyebrow">Decision Flow</span>
          <h2>SmartInvest AI Decision Flow</h2>
          <p>From raw financial data to explainable decision support.</p>
        </div>
      </div>

      <div className="decision-flow-track" aria-label="Data Sources to Portfolio decision support flow">
        <span className="decision-flow-line" aria-hidden="true" />
        <span className="decision-flow-pulse" aria-hidden="true" />
        {flowNodes.map((node, index) => {
          const Icon = node.icon;

          return (
            <article
              className="decision-flow-node"
              key={node.label}
              style={{ "--motion-delay": `${index * 70}ms` } as CSSProperties}
            >
              <span className="decision-flow-icon">
                <Icon size={18} />
              </span>
              <strong>{node.label}</strong>
            </article>
          );
        })}
      </div>
    </section>
  );
}
