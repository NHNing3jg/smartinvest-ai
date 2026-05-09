import { useEffect, useMemo, useState } from "react";

type CountUpValueProps = {
  value: string | number;
  className?: string;
};

const numberPattern = /^([^\d+-]*)([+-]?(?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d+)?)(.*)$/;

const prefersReducedMotion = () =>
  typeof window !== "undefined" && window.matchMedia("(prefers-reduced-motion: reduce)").matches;

export default function CountUpValue({ value, className = "" }: CountUpValueProps) {
  const rawValue = String(value);
  const parsed = useMemo(() => {
    const match = rawValue.match(numberPattern);

    if (!match) {
      return null;
    }

    const numericText = match[2];
    const numericValue = Number(numericText.replace(/,/g, ""));

    if (!Number.isFinite(numericValue)) {
      return null;
    }

    const decimals = numericText.includes(".") ? numericText.split(".")[1]?.length ?? 0 : 0;

    return {
      decimals: Math.min(decimals, 4),
      number: numericValue,
      prefix: match[1] ?? "",
      suffix: match[3] ?? "",
      useGrouping: numericText.includes(",") || Math.abs(numericValue) >= 1000,
    };
  }, [rawValue]);

  const [displayValue, setDisplayValue] = useState(rawValue);

  useEffect(() => {
    if (!parsed || prefersReducedMotion()) {
      setDisplayValue(rawValue);
      return;
    }

    let frame = 0;
    let raf = 0;
    const totalFrames = 34;
    const formatter = new Intl.NumberFormat("en-US", {
      maximumFractionDigits: parsed.decimals,
      minimumFractionDigits: parsed.decimals,
      useGrouping: parsed.useGrouping,
    });

    const tick = () => {
      frame += 1;
      const progress = Math.min(frame / totalFrames, 1);
      const eased = 1 - Math.pow(1 - progress, 3);
      const nextValue = parsed.number * eased;

      setDisplayValue(`${parsed.prefix}${formatter.format(nextValue)}${parsed.suffix}`);

      if (progress < 1) {
        raf = window.requestAnimationFrame(tick);
      }
    };

    setDisplayValue(`${parsed.prefix}${formatter.format(0)}${parsed.suffix}`);
    raf = window.requestAnimationFrame(tick);

    return () => window.cancelAnimationFrame(raf);
  }, [parsed, rawValue]);

  return <span className={`rb-count-up-value ${className}`.trim()}>{displayValue}</span>;
}
