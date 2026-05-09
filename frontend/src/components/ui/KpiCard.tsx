import type { LucideIcon } from "lucide-react";

type KpiCardProps = {
  title: string;
  value: string;
  detail: string;
  icon: LucideIcon;
  tone?: "positive" | "negative" | "risk" | "neutral" | "purple";
};

export default function KpiCard({ title, value, detail, icon: Icon, tone = "neutral" }: KpiCardProps) {
  return (
    <article className={`kpi-card kpi-card-${tone}`}>
      <div className="kpi-card-header">
        <span>{title}</span>
        <span className="kpi-icon">
          <Icon size={18} />
        </span>
      </div>
      <strong>{value}</strong>
      <p>{detail}</p>
    </article>
  );
}
