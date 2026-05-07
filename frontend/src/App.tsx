import { Navigate, Route, Routes } from "react-router-dom";

import Header from "./components/layout/Header";
import PageContainer from "./components/layout/PageContainer";
import Sidebar from "./components/layout/Sidebar";
import AIAdvisor from "./pages/AIAdvisor";
import Backtest from "./pages/Backtest";
import Dashboard from "./pages/Dashboard";
import EnergyMarket from "./pages/EnergyMarket";
import MacroAnalysis from "./pages/MacroAnalysis";
import MarketOverview from "./pages/MarketOverview";
import PerformanceAnalysis from "./pages/PerformanceAnalysis";
import Portfolio from "./pages/Portfolio";

export default function App() {
  return (
    <div className="app-shell">
      <Sidebar />
      <main className="main-shell">
        <Header />
        <PageContainer>
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/market-overview" element={<MarketOverview />} />
            <Route path="/macro-analysis" element={<MacroAnalysis />} />
            <Route path="/performance-analysis" element={<PerformanceAnalysis />} />
            <Route path="/energy-market" element={<EnergyMarket />} />
            <Route path="/ai-advisor" element={<AIAdvisor />} />
            <Route path="/backtest" element={<Backtest />} />
            <Route path="/portfolio" element={<Portfolio />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </PageContainer>
      </main>
    </div>
  );
}
