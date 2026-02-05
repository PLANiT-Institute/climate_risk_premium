"use client";

import { SCENARIO_LABELS, RATING_COLORS } from "@/lib/constants";
import { ScenarioResult } from "@/lib/supabase/types";

interface ScenarioTableProps {
  data: ScenarioResult[];
  compact?: boolean;
}

export default function ScenarioTable({ data, compact = false }: ScenarioTableProps) {
  const columns = compact
    ? [
        { key: "scenario", label: "Scenario", format: (v: string) => SCENARIO_LABELS[v] || v },
        { key: "overall_rating", label: "Rating" },
        { key: "crp_bps", label: "CRP (bps)", format: (v: number) => v.toFixed(0) },
        { key: "npv_million", label: "NPV ($M)", format: (v: number) => v.toFixed(0) },
        { key: "irr_pct", label: "IRR (%)", format: (v: number) => v.toFixed(1) },
        { key: "avg_dscr", label: "Avg DSCR", format: (v: number) => v.toFixed(2) },
      ]
    : [
        { key: "scenario", label: "Scenario", format: (v: string) => SCENARIO_LABELS[v] || v },
        { key: "overall_rating", label: "Rating" },
        { key: "crp_bps", label: "CRP (bps)", format: (v: number) => v.toFixed(0) },
        { key: "spread_bps", label: "Spread (bps)", format: (v: number) => v.toFixed(0) },
        { key: "npv_million", label: "NPV ($M)", format: (v: number) => v.toFixed(0) },
        { key: "irr_pct", label: "IRR (%)", format: (v: number) => v.toFixed(1) },
        { key: "avg_dscr", label: "Avg DSCR", format: (v: number) => v.toFixed(2) },
        { key: "min_dscr", label: "Min DSCR", format: (v: number) => v.toFixed(2) },
        { key: "llcr", label: "LLCR", format: (v: number) => v.toFixed(2) },
        { key: "expected_loss_pct", label: "Exp. Loss (%)", format: (v: number) => v.toFixed(1) },
        { key: "rating_migration", label: "Migration" },
        { key: "notch_change", label: "Notch Chg", format: (v: number) => (v > 0 ? `+${v}` : `${v}`) },
      ];

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b-2 border-slate-200">
            {columns.map((col) => (
              <th
                key={col.key}
                className="text-left p-3 font-semibold text-slate-600 whitespace-nowrap"
              >
                {col.label}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {data.map((row) => (
            <tr
              key={row.scenario}
              className="border-b border-slate-100 hover:bg-slate-50"
            >
              {columns.map((col) => {
                const value = (row as unknown as Record<string, unknown>)[col.key];
                const formatted = col.format
                  ? col.format(value as never)
                  : String(value);

                if (col.key === "overall_rating") {
                  return (
                    <td key={col.key} className="p-3">
                      <span
                        className="px-2 py-1 rounded text-xs font-bold text-white"
                        style={{
                          backgroundColor:
                            RATING_COLORS[value as string] || "#94a3b8",
                        }}
                      >
                        {String(value)}
                      </span>
                    </td>
                  );
                }

                return (
                  <td key={col.key} className="p-3 whitespace-nowrap">
                    {formatted}
                  </td>
                );
              })}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
