"use client";

import { useState, useEffect } from "react";
import ScenarioSelector from "@/components/dashboard/ScenarioSelector";
import DeathSpiralChart from "@/components/charts/DeathSpiralChart";
import { CreditRatingRow, CashflowRow } from "@/lib/supabase/types";
import { SCENARIO_LABELS, RATING_COLORS } from "@/lib/constants";

export default function DeathSpiralPage() {
  const [selected, setSelected] = useState(["severe_drought"]);
  const [ratings, setRatings] = useState<CreditRatingRow[]>([]);
  const [cashflows, setCashflows] = useState<Record<string, CashflowRow[]>>({});
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      const [ratingsModule, ...cashflowModules] = await Promise.all([
        import("@/data/yearly_ratings.json"),
        ...Object.keys(SCENARIO_LABELS).map(async (s) => {
          try {
            const mod = await import(`@/data/cashflows/${s}.json`);
            return { scenario: s, data: mod.default as CashflowRow[] };
          } catch {
            return { scenario: s, data: [] };
          }
        }),
      ]);
      setRatings(ratingsModule.default as CreditRatingRow[]);
      const cfMap: Record<string, CashflowRow[]> = {};
      for (const m of cashflowModules) {
        cfMap[m.scenario] = m.data;
      }
      setCashflows(cfMap);
      setLoading(false);
    }
    load();
  }, []);

  const scenario = selected[0] || "severe_drought";
  const scenarioRatings = ratings.filter((r) => r.scenario === scenario);
  const scenarioCashflows = cashflows[scenario] || [];

  return (
    <>
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-slate-900">Death Spiral Analysis</h1>
        <p className="text-sm text-slate-500 mt-1">
          Synchronized DSCR, EBITDA, and credit rating degradation visualization
        </p>
      </div>

      <div className="mb-6">
        <label className="text-sm font-medium text-slate-600 mr-3">Scenario:</label>
        <ScenarioSelector selected={selected} onChange={setSelected} />
      </div>

      {loading ? (
        <div className="text-slate-400 text-center py-12">Loading...</div>
      ) : (
        <>
          <div className="bg-white rounded-lg shadow-sm p-6 mb-6">
            <h2 className="text-lg font-semibold text-slate-800 mb-4">
              {SCENARIO_LABELS[scenario]} — DSCR & EBITDA
            </h2>
            <DeathSpiralChart ratings={scenarioRatings} cashflows={scenarioCashflows} />
          </div>

          {/* Feedback Loop Diagram */}
          <div className="bg-white rounded-lg shadow-sm p-6 mb-6">
            <h2 className="text-lg font-semibold text-slate-800 mb-4">
              Death Spiral Feedback Loop
            </h2>
            <div className="flex items-center justify-center gap-4 py-8 flex-wrap">
              {[
                { label: "Climate Risk ↑", color: "#e74c3c" },
                { label: "Capacity Factor ↓", color: "#e67e22" },
                { label: "Revenue ↓", color: "#f39c12" },
                { label: "EBITDA ↓", color: "#d35400" },
                { label: "DSCR ↓", color: "#c0392b" },
                { label: "Rating ↓", color: "#8e44ad" },
                { label: "Spread ↑", color: "#9b59b6" },
                { label: "Debt Cost ↑", color: "#e74c3c" },
              ].map((step, i) => (
                <div key={i} className="flex items-center gap-2">
                  <div
                    className="px-4 py-2 rounded-lg text-white text-sm font-medium"
                    style={{ backgroundColor: step.color }}
                  >
                    {step.label}
                  </div>
                  {i < 7 && (
                    <svg className="w-6 h-6 text-slate-400" fill="none" viewBox="0 0 24 24">
                      <path
                        stroke="currentColor"
                        strokeWidth={2}
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        d="M9 5l7 7-7 7"
                      />
                    </svg>
                  )}
                </div>
              ))}
            </div>
          </div>

          {/* Rating Timeline */}
          <div className="bg-white rounded-lg shadow-sm p-6">
            <h2 className="text-lg font-semibold text-slate-800 mb-4">
              Rating Timeline
            </h2>
            <div className="flex gap-1 overflow-x-auto pb-2">
              {scenarioRatings.map((r) => (
                <div
                  key={r.year}
                  className="flex flex-col items-center min-w-[48px]"
                >
                  <span
                    className="px-2 py-1 rounded text-[10px] font-bold text-white mb-1"
                    style={{
                      backgroundColor: RATING_COLORS[r.rating] || "#94a3b8",
                    }}
                  >
                    {r.rating}
                  </span>
                  <span className="text-[10px] text-slate-500">{r.year}</span>
                </div>
              ))}
            </div>
          </div>
        </>
      )}
    </>
  );
}
