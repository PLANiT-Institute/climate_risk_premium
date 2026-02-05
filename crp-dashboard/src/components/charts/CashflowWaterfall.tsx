"use client";

import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from "recharts";
import { CHART_MARGIN } from "@/lib/constants";
import { CashflowRow } from "@/lib/supabase/types";

interface CashflowWaterfallProps {
  data: CashflowRow;
}

export default function CashflowWaterfall({ data }: CashflowWaterfallProps) {
  const items = [
    { name: "Revenue", value: data.revenue / 1e6, color: "#27ae60" },
    { name: "Fuel", value: -data.fuel_costs / 1e6, color: "#e74c3c" },
    { name: "Variable O&M", value: -data.variable_opex / 1e6, color: "#e67e22" },
    { name: "Fixed O&M", value: -data.fixed_opex / 1e6, color: "#f39c12" },
    { name: "Outages", value: -data.outage_costs / 1e6, color: "#c0392b" },
    { name: "EBITDA", value: data.ebitda / 1e6, color: "#1a5f7a" },
  ];

  // Compute waterfall offsets
  let running = 0;
  const chartData = items.map((item, i) => {
    if (i === items.length - 1) {
      // EBITDA is the result bar
      return { name: item.name, base: 0, value: item.value, fill: item.color };
    }
    const base = running;
    running += item.value;
    return {
      name: item.name,
      base: item.value >= 0 ? 0 : base + item.value,
      value: Math.abs(item.value),
      fill: item.color,
    };
  });

  // Simple stacked bar approach: invisible base + visible value
  return (
    <ResponsiveContainer width="100%" height={300}>
      <BarChart data={chartData} margin={CHART_MARGIN}>
        <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
        <XAxis dataKey="name" tick={{ fontSize: 11 }} />
        <YAxis
          tick={{ fontSize: 12 }}
          tickFormatter={(v) => `$${v.toFixed(0)}M`}
        />
        <Tooltip
          formatter={(value: number) => [`$${value.toFixed(1)}M`]}
          contentStyle={{ fontSize: 12 }}
        />
        <Bar dataKey="base" stackId="a" fill="transparent" />
        <Bar dataKey="value" stackId="a" radius={[4, 4, 0, 0]}>
          {chartData.map((entry, index) => (
            <Cell key={index} fill={entry.fill} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}
