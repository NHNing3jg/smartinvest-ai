import type { CSSProperties, PropsWithChildren } from "react";

type AnimatedSectionProps = PropsWithChildren<{
  className?: string;
  delay?: number;
}>;

export default function AnimatedSection({ children, className = "", delay = 0 }: AnimatedSectionProps) {
  const style = delay > 0 ? ({ "--motion-delay": `${delay}ms` } as CSSProperties) : undefined;

  return (
    <div className={`motion-fade-up ${className}`.trim()} style={style}>
      {children}
    </div>
  );
}
