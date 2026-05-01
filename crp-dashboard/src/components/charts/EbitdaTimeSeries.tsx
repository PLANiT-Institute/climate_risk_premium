"use client";

import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from "recharts";
import { SCENARIO_COLORS, SCENARIO_LABELS, CHART_MARGIN } from "@/lib/constants";
import { CashflowRow } from "@/lib/types";

interface EbitdaTimeSeriesProps {
  data: Record<string, CashflowRow[]>;
  scenarios: string[];
}

export default function EbitdaTimeSeries({ data, scenarios }: EbitdaTimeSeriesProps) {
  // Build year-indexed data
  const yearMap: Record<number, Record<string, number>> = {};
  for (const s of scenarios) {
    for (const row of data[s] || []) {
      if (!yearMap[row.year]) yearMap[row.year] = { year: row.year } as Record<string, number>;
      yearMap[row.year][s] = row.ebitda / 1e6;
    }
  }
  const chartData = Object.values(yearMap).sort(
    (a, b) => (a.year as number) - (b.year as number)
  );

  return (
    <ResponsiveContainer width="100%" height={350}>
      <LineChart data={chartData} margin={CHART_MARGIN}>
        <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
        <XAxis dataKey="year" tick={{ fontSize: 12 }} />
        <YAxis
          tick={{ fontSize: 12 }}
          tickFormatter={(v) => `$${v.toFixed(0)}M`}
        />
        <Tooltip
          formatter={(value: number, name: string) => [
            `$${value.toFixed(1)}M`,
            SCENARIO_LABELS[name] || name,
          ]}
          contentStyle={{ fontSize: 12 }}
        />
        <Legend
          formatter={(value) => SCENARIO_LABELS[value] || value}
          wrapperStyle={{ fontSize: 11 }}
        />
        {scenarios.map((s) => (
          <Line
            key={s}
            type="monotone"
            dataKey={s}
            stroke={SCENARIO_COLORS[s] || "#64748b"}
            strokeWidth={2}
            dot={false}
          />
        ))}
      </LineChart>
    </ResponsiveContainer>
  );
}
