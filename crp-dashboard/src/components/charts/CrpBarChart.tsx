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
  ReferenceLine,
} from "recharts";
import { SCENARIO_LABELS, SCENARIO_COLORS, CHART_MARGIN } from "@/lib/constants";
import { ScenarioResult } from "@/lib/types";

interface CrpBarChartProps {
  data: ScenarioResult[];
  dataKey?: string;
  label?: string;
  unit?: string;
}

export default function CrpBarChart({
  data,
  dataKey = "crp_bps",
  label = "Climate Risk Premium (bps)",
  unit = " bps",
}: CrpBarChartProps) {
  const chartData = data.map((d) => ({
    name: SCENARIO_LABELS[d.scenario] || d.scenario,
    value: Number((d as unknown as Record<string, unknown>)[dataKey]),
    scenario: d.scenario,
  }));

  return (
    <ResponsiveContainer width="100%" height={350}>
      <BarChart data={chartData} margin={CHART_MARGIN}>
        <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
        <XAxis
          dataKey="name"
          tick={{ fontSize: 11 }}
          angle={-20}
          textAnchor="end"
          height={80}
        />
        <YAxis tick={{ fontSize: 12 }} />
        <Tooltip
          formatter={(value: number) => [`${value.toFixed(1)}${unit}`, label]}
          contentStyle={{ fontSize: 12 }}
        />
        <ReferenceLine y={0} stroke="#94a3b8" />
        <Bar dataKey="value" radius={[4, 4, 0, 0]}>
          {chartData.map((entry) => (
            <Cell
              key={entry.scenario}
              fill={SCENARIO_COLORS[entry.scenario] || "#64748b"}
            />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}
