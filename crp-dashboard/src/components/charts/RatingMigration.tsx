"use client";

import { RATING_COLORS, SCENARIO_LABELS } from "@/lib/constants";
import { CreditRatingRow } from "@/lib/supabase/types";

interface RatingMigrationProps {
  data: CreditRatingRow[];
  scenarios: string[];
}

const RATINGS_ORDER = ["AAA", "AA", "A", "BBB", "BB", "B", "CCC", "CC", "C", "D"];

export default function RatingMigration({ data, scenarios }: RatingMigrationProps) {
  // Get unique years
  const years = [...new Set(data.map((d) => d.year))].sort();
  // Sample every 3rd year for readability
  const displayYears = years.filter((_, i) => i % 3 === 0 || i === years.length - 1);

  return (
    <div className="overflow-x-auto">
      <table className="text-xs w-full">
        <thead>
          <tr>
            <th className="text-left p-2 bg-slate-50 sticky left-0">Scenario</th>
            {displayYears.map((y) => (
              <th key={y} className="p-2 bg-slate-50 text-center min-w-[50px]">
                {y}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {scenarios.map((s) => {
            const rows = data.filter((d) => d.scenario === s);
            return (
              <tr key={s} className="border-t border-slate-100">
                <td className="p-2 font-medium sticky left-0 bg-white whitespace-nowrap">
                  {SCENARIO_LABELS[s] || s}
                </td>
                {displayYears.map((y) => {
                  const row = rows.find((r) => r.year === y);
                  const rating = row?.rating || "-";
                  const color = RATING_COLORS[rating] || "#94a3b8";
                  return (
                    <td
                      key={y}
                      className="p-2 text-center font-bold text-white"
                      style={{ backgroundColor: color }}
                    >
                      {rating}
                    </td>
                  );
                })}
              </tr>
            );
          })}
        </tbody>
      </table>
      <div className="flex gap-2 mt-3 flex-wrap">
        {RATINGS_ORDER.filter((r) =>
          data.some((d) => d.rating === r)
        ).map((r) => (
          <span
            key={r}
            className="px-2 py-0.5 rounded text-xs font-bold text-white"
            style={{ backgroundColor: RATING_COLORS[r] }}
          >
            {r}
          </span>
        ))}
      </div>
    </div>
  );
}
