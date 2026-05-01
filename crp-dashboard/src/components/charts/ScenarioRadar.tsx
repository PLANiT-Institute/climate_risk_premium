"use client";

import {
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  Radar,
  ResponsiveContainer,
  Legend,
  Tooltip,
} from "recharts";
import { SCENARIO_COLORS, SCENARIO_LABELS } from "@/lib/constants";
import { ScenarioResult } from "@/lib/types";

interface ScenarioRadarProps {
  data: ScenarioResult[];
  selected?: string[];
}

export default function ScenarioRadar({ data, selected }: ScenarioRadarProps) {
  const scenarios = selected || data.map((d) => d.scenario);
  const filtered = data.filter((d) => scenarios.includes(d.scenario));

  // Normalize metrics to 0-100 scale for radar
  const maxNpv = Math.max(...data.map((d) => Math.abs(d.npv_million)));
  const maxCrp = Math.max(...data.map((d) => Math.abs(d.crp_bps)));
  const maxDscr = Math.max(...data.map((d) => d.avg_dscr));
  const maxIrr = Math.max(...data.map((d) => Math.abs(d.irr_pct)));

  const metrics = [
    { metric: "NPV", fullMark: 100 },
    { metric: "DSCR", fullMark: 100 },
    { metric: "IRR", fullMark: 100 },
    { metric: "Rating", fullMark: 100 },
    { metric: "CRP (inv)", fullMark: 100 },
  ];

  const chartData = metrics.map((m) => {
    const point: Record<string, string | number> = { metric: m.metric };
    for (const s of filtered) {
      let val: number;
      switch (m.metric) {
        case "NPV":
          val = ((s.npv_million + maxNpv) / (2 * maxNpv)) * 100;
          break;
        case "DSCR":
          val = (s.avg_dscr / maxDscr) * 100;
          break;
        case "IRR":
          val = ((s.irr_pct + maxIrr) / (2 * maxIrr)) * 100;
          break;
        case "Rating":
          val = ((10 - s.rating_numeric) / 9) * 100;
          break;
        case "CRP (inv)":
          val = ((maxCrp - Math.abs(s.crp_bps)) / maxCrp) * 100;
          break;
        default:
          val = 50;
      }
      point[s.scenario] = Math.max(0, Math.min(100, val));
    }
    return point;
  });

  return (
    <ResponsiveContainer width="100%" height={350}>
      <RadarChart data={chartData} outerRadius="70%">
        <PolarGrid stroke="#e2e8f0" />
        <PolarAngleAxis dataKey="metric" tick={{ fontSize: 12 }} />
        <PolarRadiusAxis
          angle={90}
          domain={[0, 100]}
          tick={false}
          axisLine={false}
        />
        <Tooltip
          formatter={(value: number, name: string) => [
            `${value.toFixed(0)}/100`,
            SCENARIO_LABELS[name] || name,
          ]}
          contentStyle={{ fontSize: 12 }}
        />
        <Legend
          formatter={(value) => SCENARIO_LABELS[value] || value}
          wrapperStyle={{ fontSize: 11 }}
        />
        {filtered.map((s) => (
          <Radar
            key={s.scenario}
            name={s.scenario}
            dataKey={s.scenario}
            stroke={SCENARIO_COLORS[s.scenario] || "#64748b"}
            fill={SCENARIO_COLORS[s.scenario] || "#64748b"}
            fillOpacity={0.15}
            strokeWidth={2}
          />
        ))}
      </RadarChart>
    </ResponsiveContainer>
  );
}
