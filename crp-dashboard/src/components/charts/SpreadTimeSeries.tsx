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
import { CreditRatingRow } from "@/lib/supabase/types";

interface SpreadTimeSeriesProps {
  data: CreditRatingRow[];
  scenarios: string[];
}

export default function SpreadTimeSeries({ data, scenarios }: SpreadTimeSeriesProps) {
  const yearMap: Record<number, Record<string, number>> = {};
  for (const row of data) {
    if (!scenarios.includes(row.scenario)) continue;
    if (!row.spread_bps) continue;
    if (!yearMap[row.year]) yearMap[row.year] = { year: row.year } as Record<string, number>;
    yearMap[row.year][row.scenario] = row.spread_bps;
  }
  const chartData = Object.values(yearMap).sort(
    (a, b) => (a.year as number) - (b.year as number)
  );

  if (chartData.length === 0) return null;

  return (
    <ResponsiveContainer width="100%" height={350}>
      <LineChart data={chartData} margin={CHART_MARGIN}>
        <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
        <XAxis dataKey="year" tick={{ fontSize: 12 }} />
        <YAxis
          tick={{ fontSize: 12 }}
          tickFormatter={(v) => `${v} bps`}
        />
        <Tooltip
          formatter={(value: number, name: string) => [
            `${value.toFixed(0)} bps`,
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
            type="stepAfter"
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
