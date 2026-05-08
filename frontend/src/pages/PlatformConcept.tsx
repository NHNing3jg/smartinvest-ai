import {
  BarChart3,
  Brain,
  CheckCircle2,
  CircleAlert,
  Database,
  Gauge,
  GitBranch,
  Globe2,
  Layers3,
  LineChart,
  Network,
  PieChart,
  Route,
  Server,
  ShieldAlert,
  Sparkles,
} from "lucide-react";
import type { LucideIcon } from "lucide-react";

type ConceptCard = {
  icon: LucideIcon;
  title: string;
  text: string;
};

const platformLayers: ConceptCard[] = [
  {
    icon: BarChart3,
    title: "BI layer",
    text: "Market, macro, energy and performance dashboards organize the decision context before any signal is interpreted.",
  },
  {
    icon: Brain,
    title: "AI layer",
    text: "The advisor converts model outputs and engineered indicators into explainable BUY, HOLD and SELL recommendation views.",
  },
  {
    icon: Route,
    title: "Validation layer",
    text: "Backtesting and portfolio simulation help users inspect how recommendations behave historically and how allocations could be composed.",
  },
];

const architectureSteps = [
  { label: "Market, macro, energy and performance inputs", icon: Globe2 },
  { label: "Data preparation and feature logic", icon: GitBranch },
  { label: "PostgreSQL analytical warehouse", icon: Database },
  { label: "FastAPI service endpoints", icon: Server },
  { label: "React decision interface", icon: LineChart },
  { label: "Advisor, backtest and portfolio modules", icon: Sparkles },
];

const systemModules: ConceptCard[] = [
  {
    icon: Database,
    title: "PostgreSQL Data Warehouse",
    text: "Stores curated analytical tables and views so dashboards and AI workflows share a consistent data foundation.",
  },
  {
    icon: Server,
    title: "FastAPI backend",
    text: "Exposes structured API endpoints for market summaries, macro analysis, recommendations, backtesting and portfolio allocation.",
  },
  {
    icon: LineChart,
    title: "React frontend",
    text: "Presents the platform as an executive decision cockpit with module-level pages for exploration and interpretation.",
  },
  {
    icon: Brain,
    title: "AI Advisor",
    text: "Combines prediction direction, probabilities, confidence, advisor score and explanatory drivers into recommendation cards and tables.",
  },
  {
    icon: Gauge,
    title: "Backtesting",
    text: "Compares signal behavior against historical next-period outcomes without claiming future performance guarantees.",
  },
  {
    icon: PieChart,
    title: "Portfolio simulation",
    text: "Translates recommendation and risk context into allocation views that can be inspected rather than blindly accepted.",
  },
];

const crispDmSteps = [
  { title: "Business Understanding", text: "Frame investment decision support as the core objective." },
  { title: "Data Understanding", text: "Inspect market, macro, energy and performance data through BI dashboards." },
  { title: "Data Preparation", text: "Curate warehouse-ready datasets and model features." },
  { title: "Modeling", text: "Generate directional signals and advisor scoring logic." },
  { title: "Evaluation", text: "Use backtesting, explanations and portfolio simulation to review behavior." },
  { title: "Deployment", text: "Serve insights through FastAPI and React as an accessible platform." },
];

export default function PlatformConcept() {
  return (
    <section className="page-stack platform-concept-page">
      <div className="page-hero hero-platform-concept">
        <div className="hero-copy">
          <span className="eyebrow">Platform Concept</span>
          <h1>SmartInvest AI</h1>
          <p>
            A BI + AI investment decision-support platform that connects analytical dashboards, explainable
            recommendations, backtesting and portfolio simulation in one workflow.
          </p>
          <div className="platform-hero-tags">
            <span>PostgreSQL warehouse</span>
            <span>FastAPI backend</span>
            <span>React + Vite frontend</span>
            <span>Explainable AI logic</span>
          </div>
        </div>
        <div className="platform-hero-diagram" aria-label="SmartInvest AI platform modules">
          <div className="platform-orbit-card">
            <Database size={20} />
            <span>Warehouse</span>
          </div>
          <div className="platform-orbit-card">
            <Server size={20} />
            <span>API</span>
          </div>
          <div className="platform-orbit-card platform-orbit-card-focus">
            <Brain size={22} />
            <strong>Advisor</strong>
          </div>
          <div className="platform-orbit-card">
            <BarChart3 size={20} />
            <span>BI</span>
          </div>
        </div>
      </div>

      <div className="platform-summary-grid">
        <article className="content-panel platform-intro-card">
          <span className="eyebrow">What is SmartInvest AI?</span>
          <h2>Decision support, not automatic investing</h2>
          <p>
            SmartInvest AI brings together business intelligence dashboards and AI-assisted recommendation logic so a
            user can move from raw financial context to a more structured investment decision.
          </p>
          <p>
            The platform is designed for analysis, interpretation and comparison. It does not claim guaranteed returns
            or replace professional financial judgment.
          </p>
        </article>

        <article className="content-panel platform-problem-card">
          <span className="eyebrow">Problem addressed</span>
          <h2>Investment signals are hard to trust when context is fragmented</h2>
          <p>
            Market movement, economic indicators, energy exposure, portfolio risk and model recommendations often live
            in separate tools. That makes it difficult to understand why a signal appears and how it relates to broader
            conditions.
          </p>
        </article>
      </div>

      <div className="content-panel platform-solution-panel">
        <div className="panel-heading-row">
          <div>
            <span className="eyebrow">Proposed solution</span>
            <h2>A modular platform where BI explains the context and AI supports the decision</h2>
          </div>
          <Layers3 size={24} />
        </div>
        <div className="platform-layer-grid">
          {platformLayers.map((layer) => {
            const Icon = layer.icon;
            return (
              <article className="platform-layer-card" key={layer.title}>
                <span className="platform-layer-icon">
                  <Icon size={20} />
                </span>
                <strong>{layer.title}</strong>
                <p>{layer.text}</p>
              </article>
            );
          })}
        </div>
      </div>

      <div className="content-panel platform-pipeline-panel">
        <div className="panel-heading-row">
          <div>
            <span className="eyebrow">Data pipeline</span>
            <h2>From source context to decision interface</h2>
          </div>
          <Network size={24} />
        </div>
        <div className="platform-pipeline">
          {architectureSteps.map((step) => {
            const Icon = step.icon;
            return (
              <article className="platform-pipeline-node" key={step.label}>
                <span>
                  <Icon size={18} />
                </span>
                <strong>{step.label}</strong>
              </article>
            );
          })}
        </div>
      </div>

      <div className="platform-module-grid">
        {systemModules.map((module) => {
          const Icon = module.icon;
          return (
            <article className="content-panel platform-module-card" key={module.title}>
              <span className="platform-module-icon">
                <Icon size={21} />
              </span>
              <h2>{module.title}</h2>
              <p>{module.text}</p>
            </article>
          );
        })}
      </div>

      <div className="content-panel platform-workflow-panel">
        <div className="panel-heading-row">
          <div>
            <span className="eyebrow">How the modules work together</span>
            <h2>One analytical loop across BI, AI, validation and simulation</h2>
          </div>
          <CheckCircle2 size={24} />
        </div>
        <div className="platform-workflow">
          <article>
            <span>1</span>
            <strong>Explore context</strong>
            <p>Market, macro, energy and performance pages help identify the environment around an asset.</p>
          </article>
          <article>
            <span>2</span>
            <strong>Review recommendation logic</strong>
            <p>The AI Advisor exposes signal, probability, confidence, score and explanation together.</p>
          </article>
          <article>
            <span>3</span>
            <strong>Validate behavior</strong>
            <p>Backtesting summarizes historical signal behavior so the user can inspect strengths and limits.</p>
          </article>
          <article>
            <span>4</span>
            <strong>Simulate allocation</strong>
            <p>The portfolio module turns recommendation context into an allocation view for scenario analysis.</p>
          </article>
        </div>
      </div>

      <div className="content-panel platform-crisp-panel">
        <div className="panel-heading-row">
          <div>
            <span className="eyebrow">CRISP-DM alignment</span>
            <h2>The platform follows a practical analytics lifecycle</h2>
          </div>
          <GitBranch size={24} />
        </div>
        <div className="platform-crisp-grid">
          {crispDmSteps.map((step, index) => (
            <article className="platform-crisp-step" key={step.title}>
              <span>{String(index + 1).padStart(2, "0")}</span>
              <strong>{step.title}</strong>
              <p>{step.text}</p>
            </article>
          ))}
        </div>
      </div>

      <div className="content-panel split-panel platform-limitations-panel">
        <ShieldAlert className="panel-icon" size={32} />
        <div>
          <span className="eyebrow">Limitations and no financial advice</span>
          <h2>Transparent by design</h2>
          <p>
            SmartInvest AI is an educational and analytical decision-support system. Recommendations are generated from
            available data and model logic, and they can be incomplete when input data is missing, stale or noisy.
          </p>
          <p>
            Backtests are historical analysis tools, not promises of future returns. The platform does not provide
            personalized financial advice, and investment decisions should consider professional guidance and individual
            risk tolerance.
          </p>
        </div>
        <CircleAlert className="platform-limitations-mark" size={86} />
      </div>
    </section>
  );
}
