import type { LucideIcon } from "lucide-react";
import CountUpValue from "../reactbits/CountUpValue";
import SpotlightPanel from "../reactbits/SpotlightPanel";

type KpiCardProps = {
  title: string;
  value: string;
  detail: string;
  icon: LucideIcon;
  tone?: "positive" | "negative" | "risk" | "neutral" | "purple";
};

export default function KpiCard({ title, value, detail, icon: Icon, tone = "neutral" }: KpiCardProps) {
  return (
    <SpotlightPanel className={`kpi-card kpi-card-${tone}`}>
      <div className="kpi-card-header">
        <span>{title}</span>
        <span className="kpi-icon">
          <Icon size={18} />
        </span>
      </div>
      <strong>
        <CountUpValue value={value} />
      </strong>
      <p>{detail}</p>
    </SpotlightPanel>
  );
}
