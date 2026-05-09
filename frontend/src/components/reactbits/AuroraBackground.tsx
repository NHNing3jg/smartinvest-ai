type AuroraBackgroundProps = {
  className?: string;
};

export default function AuroraBackground({ className = "" }: AuroraBackgroundProps) {
  return <span className={`rb-aurora-background ${className}`.trim()} aria-hidden="true" />;
}
