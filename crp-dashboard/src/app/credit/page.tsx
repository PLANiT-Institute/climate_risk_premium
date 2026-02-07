import { getScenarioResults } from "@/lib/queries/scenarios";
import { getRatingTrajectories } from "@/lib/queries/ratings";
import RatingMigration from "@/components/charts/RatingMigration";
import DscrTimeSeries from "@/components/charts/DscrTimeSeries";
import SpreadTimeSeries from "@/components/charts/SpreadTimeSeries";
import { RATING_COLORS, SCENARIO_LABELS } from "@/lib/constants";

export const revalidate = 3600;

export default async function CreditPage() {
  const [scenarios, ratings] = await Promise.all([
    getScenarioResults(),
    getRatingTrajectories(),
  ]);

  const allScenarios = scenarios.map((s) => s.scenario);

  return (
    <>
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-slate-900">Credit Rating Analysis</h1>
        <p className="text-sm text-slate-500 mt-1">
          KIS-methodology credit rating trajectories and DSCR analysis
        </p>
      </div>

      {/* Rating Migration Heatmap */}
      <div className="bg-white rounded-lg shadow-sm p-6 mb-6">
        <h2 className="text-lg font-semibold text-slate-800 mb-4">
          Rating Migration Heatmap
        </h2>
        <RatingMigration data={ratings} scenarios={allScenarios} />
      </div>

      {/* DSCR Time Series */}
      <div className="bg-white rounded-lg shadow-sm p-6 mb-6">
        <h2 className="text-lg font-semibold text-slate-800 mb-4">
          DSCR Trajectories
        </h2>
        <DscrTimeSeries data={ratings} scenarios={allScenarios} />
      </div>

      {/* Spread Time Series */}
      <div className="bg-white rounded-lg shadow-sm p-6 mb-6">
        <h2 className="text-lg font-semibold text-slate-800 mb-4">
          Credit Spread Trajectories
        </h2>
        <p className="text-xs text-slate-500 mb-4">
          Credit spread (bps) evolution by scenario, reflecting rating-driven cost of debt changes
        </p>
        <SpreadTimeSeries data={ratings} scenarios={allScenarios} />
      </div>

      {/* Rating Component Table */}
      <div className="bg-white rounded-lg shadow-sm p-6">
        <h2 className="text-lg font-semibold text-slate-800 mb-4">
          Rating Component Analysis
        </h2>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b-2 border-slate-200">
                <th className="p-3 text-left">Scenario</th>
                <th className="p-3 text-center">Overall</th>
                <th className="p-3 text-center">DSCR</th>
                <th className="p-3 text-center">Coverage</th>
                <th className="p-3 text-center">Profitability</th>
                <th className="p-3 text-center">Capacity</th>
                <th className="p-3 text-center">Debt/Equity</th>
                <th className="p-3 text-right">Spread (bps)</th>
              </tr>
            </thead>
            <tbody>
              {scenarios.map((s) => (
                <tr key={s.scenario} className="border-b border-slate-100">
                  <td className="p-3 font-medium">
                    {SCENARIO_LABELS[s.scenario] || s.scenario}
                  </td>
                  {[
                    s.overall_rating,
                    s.dscr_rating,
                    s.coverage_rating,
                    s.profitability_rating,
                    s.capacity_rating,
                    s.equity_leverage_rating,
                  ].map((rating, i) => (
                    <td key={i} className="p-3 text-center">
                      <span
                        className="px-2 py-0.5 rounded text-xs font-bold text-white"
                        style={{
                          backgroundColor: RATING_COLORS[rating] || "#94a3b8",
                        }}
                      >
                        {rating}
                      </span>
                    </td>
                  ))}
                  <td className="p-3 text-right font-mono">
                    {s.spread_bps.toFixed(0)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </>
  );
}
