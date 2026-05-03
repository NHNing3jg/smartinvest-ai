import type { LucideIcon } from "lucide-react";

type KpiCardProps = {
  title: string;
  value: string;
  detail: string;
  icon: LucideIcon;
};

export default function KpiCard({ title, value, detail, icon: Icon }: KpiCardProps) {
  return (
    <article className="kpi-card">
      <div className="kpi-card-header">
        <span>{title}</span>
        <Icon size={18} />
      </div>
      <strong>{value}</strong>
      <p>{detail}</p>
    </article>
  );
}
