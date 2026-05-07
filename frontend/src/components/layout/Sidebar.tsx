import { Activity, Brain, ChartNoAxesCombined, Globe2, LayoutDashboard, LineChart, WalletCards } from "lucide-react";
import { NavLink } from "react-router-dom";

const navItems = [
  { label: "Dashboard", path: "/", icon: LayoutDashboard },
  { label: "Market Overview", path: "/market-overview", icon: LineChart },
  { label: "Macro Analysis", path: "/macro-analysis", icon: Globe2 },
  { label: "Performance Analysis", path: "/performance-analysis", icon: Activity },
  { label: "AI Advisor", path: "/ai-advisor", icon: Brain },
  { label: "Backtest", path: "/backtest", icon: ChartNoAxesCombined },
  { label: "Portfolio", path: "/portfolio", icon: WalletCards },
];

export default function Sidebar() {
  return (
    <aside className="sidebar">
      <div className="brand-block">
        <div className="brand-mark">SI</div>
        <div>
          <strong>SmartInvest</strong>
          <span>AI Innovation Lab</span>
        </div>
      </div>

      <nav className="nav-list" aria-label="Primary navigation">
        {navItems.map((item) => {
          const Icon = item.icon;

          return (
            <NavLink
              key={item.path}
              to={item.path}
              className={({ isActive }) => (isActive ? "nav-link active" : "nav-link")}
            >
              <Icon size={18} />
              <span>{item.label}</span>
            </NavLink>
          );
        })}
      </nav>

      <div className="sidebar-note">
        <span>BI + AI</span>
        <strong>Student fintech studio</strong>
      </div>
    </aside>
  );
}
