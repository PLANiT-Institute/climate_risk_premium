"use client";

import {
  ComposedChart,
  Line,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
  ReferenceLine,
} from "recharts";
import { RATING_COLORS, CHART_MARGIN } from "@/lib/constants";
import { CreditRatingRow } from "@/lib/supabase/types";
import { CashflowRow } from "@/lib/supabase/types";

const RATING_NUMERIC: Record<string, number> = {
  AAA: 1, AA: 2, A: 3, BBB: 4, BB: 5, B: 6, CCC: 7, CC: 8, C: 9, D: 10,
};

interface DeathSpiralChartProps {
  ratings: CreditRatingRow[];
  cashflows: CashflowRow[];
}

export default function DeathSpiralChart({ ratings, cashflows }: DeathSpiralChartProps) {
  const chartData = ratings.map((r) => {
    const cf = cashflows.find((c) => c.year === r.year);
    return {
      year: r.year,
      dscr: r.dscr,
      ebitda: cf ? cf.ebitda / 1e6 : 0,
      rating: r.rating,
      ratingNum: RATING_NUMERIC[r.rating] || 5,
      spread: r.spread_bps,
      ratingColor: RATING_COLORS[r.rating] || "#94a3b8",
    };
  });

  return (
    <ResponsiveContainer width="100%" height={400}>
      <ComposedChart data={chartData} margin={{ ...CHART_MARGIN, right: 60 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
        <XAxis dataKey="year" tick={{ fontSize: 12 }} />
        <YAxis
          yAxisId="dscr"
          tick={{ fontSize: 12 }}
          tickFormatter={(v) => `${v.toFixed(1)}x`}
          domain={[0, "auto"]}
          label={{ value: "DSCR", angle: -90, position: "insideLeft", fontSize: 11 }}
        />
        <YAxis
          yAxisId="ebitda"
          orientation="right"
          tick={{ fontSize: 12 }}
          tickFormatter={(v) => `$${v.toFixed(0)}M`}
          label={{ value: "EBITDA", angle: 90, position: "insideRight", fontSize: 11 }}
        />
        <Tooltip
          formatter={(value: number, name: string) => {
            if (name === "dscr") return [`${value.toFixed(2)}x`, "DSCR"];
            if (name === "ebitda") return [`$${value.toFixed(1)}M`, "EBITDA"];
            if (name === "spread") return [`${value.toFixed(0)} bps`, "Spread"];
            return [value, name];
          }}
          contentStyle={{ fontSize: 12 }}
          labelFormatter={(label) => {
            const item = chartData.find((d) => d.year === label);
            return `${label} — Rating: ${item?.rating || "N/A"}`;
          }}
        />
        <Legend wrapperStyle={{ fontSize: 11 }} />
        <ReferenceLine
          yAxisId="dscr"
          y={1.0}
          stroke="#e74c3c"
          strokeDasharray="5 5"
          label={{ value: "DSCR=1.0x", fontSize: 9, fill: "#e74c3c" }}
        />
        <Bar
          yAxisId="ebitda"
          dataKey="ebitda"
          fill="#57c5b6"
          opacity={0.3}
          name="ebitda"
        />
        <Line
          yAxisId="dscr"
          type="monotone"
          dataKey="dscr"
          stroke="#1a5f7a"
          strokeWidth={2.5}
          dot={false}
          name="dscr"
        />
        <Line
          yAxisId="dscr"
          type="monotone"
          dataKey="spread"
          stroke="#e74c3c"
          strokeWidth={1.5}
          strokeDasharray="4 4"
          dot={false}
          name="spread"
          hide
        />
      </ComposedChart>
    </ResponsiveContainer>
  );
}
