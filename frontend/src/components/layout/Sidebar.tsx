import {
  Activity,
  Brain,
  ChartNoAxesCombined,
  Droplets,
  Globe2,
  LayoutDashboard,
  Layers3,
  LineChart,
  WalletCards,
} from "lucide-react";
import { NavLink } from "react-router-dom";

import smartInvestLogo from "../../assets/smartinvest-logo.png";

const navItems = [
  { label: "Dashboard", path: "/", icon: LayoutDashboard },
  { label: "Platform Concept", path: "/platform-concept", icon: Layers3 },
  { label: "Market Overview", path: "/market-overview", icon: LineChart },
  { label: "Macro Analysis", path: "/macro-analysis", icon: Globe2 },
  { label: "Performance Analysis", path: "/performance-analysis", icon: Activity },
  { label: "Energy Market", path: "/energy-market", icon: Droplets },
  { label: "AI Advisor", path: "/ai-advisor", icon: Brain },
  { label: "Backtest", path: "/backtest", icon: ChartNoAxesCombined },
  { label: "Portfolio", path: "/portfolio", icon: WalletCards },
];

export default function Sidebar() {
  return (
    <aside className="sidebar">
      <div className="brand-block">
        <div className="brand-mark">
          <img src={smartInvestLogo} alt="SmartInvest AI logo" />
        </div>
        <div>
          <strong>SmartInvest</strong>
          <span>Trading Cockpit</span>
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
    </aside>
  );
}
