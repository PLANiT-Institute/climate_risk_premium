"use client";

import { RATING_COLORS, SCENARIO_LABELS } from "@/lib/constants";
import { ScenarioResult } from "@/lib/types";

interface RatingDistributionProps {
  data: ScenarioResult[];
}

export default function RatingDistribution({ data }: RatingDistributionProps) {
  const ratingGroups: Record<string, ScenarioResult[]> = {};
  for (const s of data) {
    const r = s.overall_rating;
    if (!ratingGroups[r]) ratingGroups[r] = [];
    ratingGroups[r].push(s);
  }

  return (
    <div className="space-y-3">
      {Object.entries(ratingGroups).map(([rating, scenarios]) => (
        <div key={rating} className="flex items-center gap-3">
          <span
            className="px-3 py-1 rounded text-sm font-bold text-white min-w-[48px] text-center"
            style={{ backgroundColor: RATING_COLORS[rating] || "#94a3b8" }}
          >
            {rating}
          </span>
          <div className="flex-1">
            <div
              className="h-8 rounded-md flex items-center px-3"
              style={{
                backgroundColor: (RATING_COLORS[rating] || "#94a3b8") + "20",
                width: `${Math.max(20, (scenarios.length / data.length) * 100)}%`,
              }}
            >
              <span className="text-xs text-slate-600 truncate">
                {scenarios
                  .map((s) => SCENARIO_LABELS[s.scenario] || s.scenario)
                  .join(", ")}
              </span>
            </div>
          </div>
          <span className="text-xs text-slate-400 font-mono min-w-[32px] text-right">
            {scenarios.length}
          </span>
        </div>
      ))}
    </div>
  );
}
