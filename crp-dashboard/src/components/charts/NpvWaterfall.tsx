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
import { CHART_MARGIN } from "@/lib/constants";
import { ScenarioResult } from "@/lib/supabase/types";

interface NpvWaterfallProps {
  scenarios: ScenarioResult[];
}

export default function NpvWaterfall({ scenarios }: NpvWaterfallProps) {
  const baseline = scenarios.find((s) => s.scenario === "baseline");
  const modPhys = scenarios.find((s) => s.scenario === "moderate_physical");
  const highPhys = scenarios.find((s) => s.scenario === "high_physical");
  const modTrans = scenarios.find((s) => s.scenario === "moderate_transition");
  const combinedAgg = scenarios.find((s) => s.scenario === "combined_aggressive");

  if (!baseline) return null;

  const baseNpv = baseline.npv_million;
  const physImpact = modPhys ? modPhys.npv_million - baseNpv : 0;
  const highPhysImpact = highPhys ? highPhys.npv_million - baseNpv : 0;
  const transImpact = modTrans ? modTrans.npv_million - baseNpv : 0;
  const combinedTotal = combinedAgg ? combinedAgg.npv_million : 0;

  const items = [
    { name: "Baseline NPV", value: baseNpv, isTotal: true },
    { name: "Moderate Physical", value: physImpact, isTotal: false },
    { name: "High Physical", value: highPhysImpact - physImpact, isTotal: false },
    { name: "Transition Risk", value: transImpact, isTotal: false },
    { name: "Combined Aggressive", value: combinedTotal, isTotal: true },
  ];

  let running = 0;
  const chartData = items.map((item) => {
    if (item.isTotal) {
      const result = {
        name: item.name,
        base: Math.min(0, item.value),
        value: Math.abs(item.value),
        fill: item.value >= 0 ? "#27ae60" : "#e74c3c",
        actual: item.value,
      };
      running = item.value;
      return result;
    }
    const base = running;
    running += item.value;
    return {
      name: item.name,
      base: item.value >= 0 ? base : base + item.value,
      value: Math.abs(item.value),
      fill: item.value >= 0 ? "#27ae60" : "#e74c3c",
      actual: item.value,
    };
  });

  return (
    <ResponsiveContainer width="100%" height={350}>
      <BarChart data={chartData} margin={{ ...CHART_MARGIN, bottom: 20 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
        <XAxis
          dataKey="name"
          tick={{ fontSize: 11 }}
          angle={-15}
          textAnchor="end"
          height={60}
        />
        <YAxis
          tick={{ fontSize: 12 }}
          tickFormatter={(v) => `$${(v / 1).toFixed(0)}M`}
        />
        <Tooltip
          formatter={(value: number, _name: string, item) => {
            const actual = (item?.payload as { actual?: number })?.actual;
            return [
              actual != null ? `$${actual.toFixed(0)}M` : `$${value.toFixed(0)}M`,
              "NPV Impact",
            ];
          }}
          contentStyle={{ fontSize: 12 }}
        />
        <ReferenceLine y={0} stroke="#94a3b8" strokeWidth={1.5} />
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
