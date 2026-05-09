import { Navigate, Route, Routes, useLocation } from "react-router-dom";

import Header from "./components/layout/Header";
import PageContainer from "./components/layout/PageContainer";
import Sidebar from "./components/layout/Sidebar";
import AnimatedReveal from "./components/reactbits/AnimatedReveal";
import AuroraBackground from "./components/reactbits/AuroraBackground";
import ClickSpark from "./components/reactbits/ClickSpark";
import AIAdvisor from "./pages/AIAdvisor";
import Backtest from "./pages/Backtest";
import Dashboard from "./pages/Dashboard";
import EnergyMarket from "./pages/EnergyMarket";
import MacroAnalysis from "./pages/MacroAnalysis";
import MarketOverview from "./pages/MarketOverview";
import PlatformConcept from "./pages/PlatformConcept";
import PerformanceAnalysis from "./pages/PerformanceAnalysis";
import Portfolio from "./pages/Portfolio";

export default function App() {
  const location = useLocation();

  return (
    <ClickSpark>
      <AuroraBackground className="rb-app-aurora" />
      <div className="app-shell">
        <Sidebar />
        <main className="main-shell">
          <Header />
          <PageContainer>
            <AnimatedReveal key={location.pathname} className="motion-route-shell">
              <Routes>
                <Route path="/" element={<Dashboard />} />
                <Route path="/platform-concept" element={<PlatformConcept />} />
                <Route path="/market-overview" element={<MarketOverview />} />
                <Route path="/macro-analysis" element={<MacroAnalysis />} />
                <Route path="/performance-analysis" element={<PerformanceAnalysis />} />
                <Route path="/energy-market" element={<EnergyMarket />} />
                <Route path="/ai-advisor" element={<AIAdvisor />} />
                <Route path="/backtest" element={<Backtest />} />
                <Route path="/portfolio" element={<Portfolio />} />
                <Route path="*" element={<Navigate to="/" replace />} />
              </Routes>
            </AnimatedReveal>
          </PageContainer>
        </main>
      </div>
    </ClickSpark>
  );
}
