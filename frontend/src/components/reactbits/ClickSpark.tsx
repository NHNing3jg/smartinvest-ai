import { useCallback, useEffect, useState } from "react";
import type { MouseEvent, PropsWithChildren } from "react";

type Spark = {
  id: number;
  x: number;
  y: number;
};

const ignoredSparkTargets =
  "input, select, textarea, table, th, td, button, .recommendation-table-wrap, .recharts-wrapper, .recharts-surface, .market-recharts-card, .macro-recharts-card, .performance-recharts-card, .energy-recharts-card";

export default function ClickSpark({ children }: PropsWithChildren) {
  const [sparks, setSparks] = useState<Spark[]>([]);

  const handleClick = useCallback((event: MouseEvent<HTMLDivElement>) => {
    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
      return;
    }

    const target = event.target as HTMLElement | null;
    if (target?.closest(ignoredSparkTargets)) {
      return;
    }

    const id = Date.now() + Math.round(Math.random() * 1000);
    setSparks((current) => [...current.slice(-5), { id, x: event.clientX, y: event.clientY }]);
  }, []);

  useEffect(() => {
    if (sparks.length === 0) {
      return undefined;
    }

    const timeout = window.setTimeout(() => {
      setSparks((current) => current.slice(1));
    }, 760);

    return () => window.clearTimeout(timeout);
  }, [sparks]);

  return (
    <div className="rb-click-spark-root" onClickCapture={handleClick}>
      {children}
      <div className="rb-click-spark-layer" aria-hidden="true">
        {sparks.map((spark) => (
          <span
            className="rb-click-spark"
            key={spark.id}
            style={{ left: spark.x, top: spark.y }}
          />
        ))}
      </div>
    </div>
  );
}
