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
  const aggTrans = scenarios.find((s) => s.scenario === "aggressive_transition");
  // Use the worst-case scenario as the final total
  const worstCase = scenarios.reduce((worst, s) =>
    s.npv_million < worst.npv_million ? s : worst
  );

  if (!baseline) return null;

  const baseNpv = baseline.npv_million;
  const physImpact = modPhys ? modPhys.npv_million - baseNpv : 0;
  const transImpact = aggTrans ? aggTrans.npv_million - baseNpv : 0;
  // Remaining impact from transition to worst-case
  const remainingImpact = worstCase.npv_million - (aggTrans?.npv_million ?? baseNpv);

  const items = [
    { name: "Baseline NPV", value: baseNpv, isTotal: true },
    { name: "Physical Risk", value: physImpact, isTotal: false },
    { name: "Transition Risk", value: transImpact - physImpact, isTotal: false },
  ];

  // Add enhanced policy step if the worst case is different from aggressive transition
  if (worstCase.scenario !== "aggressive_transition" && Math.abs(remainingImpact) > 1) {
    items.push({
      name: "Enhanced Policy",
      value: remainingImpact,
      isTotal: false,
    });
  }

  items.push({
    name: "Worst Case",
    value: worstCase.npv_million,
    isTotal: true,
  });

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
          tickFormatter={(v) => `$${v.toFixed(0)}M`}
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
