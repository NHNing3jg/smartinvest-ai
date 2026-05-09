import type { PropsWithChildren } from "react";

type GlareCardProps = PropsWithChildren<{
  className?: string;
}>;

export default function GlareCard({ children, className = "" }: GlareCardProps) {
  return <article className={`rb-glare-card ${className}`.trim()}>{children}</article>;
}
