import type { PropsWithChildren } from "react";

type SpotlightPanelProps = PropsWithChildren<{
  className?: string;
}>;

export default function SpotlightPanel({ children, className = "" }: SpotlightPanelProps) {
  return <article className={`rb-spotlight-panel ${className}`.trim()}>{children}</article>;
}
