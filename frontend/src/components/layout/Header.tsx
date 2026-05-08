import { Bell, Search } from "lucide-react";

export default function Header() {
  return (
    <header className="topbar">
      <div className="search-shell">
        <Search size={18} />
        <span>Search tickers, signals, or portfolios</span>
      </div>

      <div className="topbar-actions">
        <div className="topbar-context" aria-label="SmartInvest AI workspace">
          <span className="market-status-dot" />
          <span>Trading Intelligence Cockpit</span>
        </div>
        <button className="icon-button" type="button" aria-label="Notifications">
          <Bell size={18} />
        </button>
      </div>
    </header>
  );
}
