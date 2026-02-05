interface KpiCardProps {
  title: string;
  value: string;
  subtitle?: string;
  color?: string;
  trend?: "up" | "down" | "neutral";
}

export default function KpiCard({ title, value, subtitle, color, trend }: KpiCardProps) {
  const borderColor = color || "#1a5f7a";
  return (
    <div
      className="bg-white rounded-lg shadow-sm border-l-4 p-5"
      style={{ borderLeftColor: borderColor }}
    >
      <p className="text-sm text-slate-500 font-medium">{title}</p>
      <p className="text-2xl font-bold mt-1 text-slate-900">{value}</p>
      {subtitle && (
        <p className="text-xs text-slate-400 mt-1 flex items-center gap-1">
          {trend === "up" && <span className="text-red-500">&#9650;</span>}
          {trend === "down" && <span className="text-green-500">&#9660;</span>}
          {subtitle}
        </p>
      )}
    </div>
  );
}
