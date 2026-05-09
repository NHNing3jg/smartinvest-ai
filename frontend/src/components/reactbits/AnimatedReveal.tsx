import type { CSSProperties, PropsWithChildren } from "react";

type AnimatedRevealProps = PropsWithChildren<{
  className?: string;
  delay?: number;
}>;

export default function AnimatedReveal({ children, className = "", delay = 0 }: AnimatedRevealProps) {
  const style = delay > 0 ? ({ "--rb-delay": `${delay}ms` } as CSSProperties) : undefined;

  return (
    <div className={`rb-animated-reveal ${className}`.trim()} style={style}>
      {children}
    </div>
  );
}
