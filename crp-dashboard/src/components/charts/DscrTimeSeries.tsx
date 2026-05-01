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
  ReferenceLine,
} from "recharts";
import { SCENARIO_COLORS, SCENARIO_LABELS, CHART_MARGIN } from "@/lib/constants";
import { CreditRatingRow } from "@/lib/types";

interface DscrTimeSeriesProps {
  data: CreditRatingRow[];
  scenarios: string[];
}

export default function DscrTimeSeries({ data, scenarios }: DscrTimeSeriesProps) {
  const yearMap: Record<number, Record<string, number>> = {};
  for (const row of data) {
    if (!scenarios.includes(row.scenario)) continue;
    if (!yearMap[row.year]) yearMap[row.year] = { year: row.year } as Record<string, number>;
    yearMap[row.year][row.scenario] = row.dscr;
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
          tickFormatter={(v) => `${v.toFixed(1)}x`}
          domain={[0, "auto"]}
        />
        <Tooltip
          formatter={(value: number, name: string) => [
            `${value.toFixed(2)}x`,
            SCENARIO_LABELS[name] || name,
          ]}
          contentStyle={{ fontSize: 12 }}
        />
        <Legend
          formatter={(value) => SCENARIO_LABELS[value] || value}
          wrapperStyle={{ fontSize: 11 }}
        />
        <ReferenceLine
          y={1.0}
          stroke="#e74c3c"
          strokeDasharray="5 5"
          label={{ value: "DSCR = 1.0x", position: "right", fontSize: 10, fill: "#e74c3c" }}
        />
        <ReferenceLine
          y={1.3}
          stroke="#f39c12"
          strokeDasharray="3 3"
          label={{ value: "1.3x (Min IG)", position: "right", fontSize: 10, fill: "#f39c12" }}
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
