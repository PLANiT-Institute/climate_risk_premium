import { getScenarioResults } from "@/lib/queries/scenarios";
import ShapleyDecomposition from "@/components/charts/ShapleyDecomposition";
import { COLORS } from "@/lib/constants";

export const revalidate = 3600;

export default async function RiskDecompositionPage() {
  const scenarios = await getScenarioResults();

  const baseline = scenarios.find((s) => s.scenario === "baseline");
  const modPhys = scenarios.find((s) => s.scenario === "moderate_physical");
  const highPhys = scenarios.find((s) => s.scenario === "high_physical");
  const modTrans = scenarios.find((s) => s.scenario === "moderate_transition");

  return (
    <>
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-slate-900">
          Risk Decomposition
        </h1>
        <p className="text-sm text-slate-500 mt-1">
          Shapley value attribution of transition vs. physical risk contributions
        </p>
      </div>

      {/* Key Insight */}
      <div className="bg-blue-50 border-l-4 border-blue-400 rounded-lg p-4 mb-8">
        <p className="text-sm font-medium text-blue-800">
          Using Shapley values (Shapley, 1953) for two-player cooperative game decomposition,
          transition risk accounts for over 99% of the total CRP. Physical risk contributes
          marginally, confirming that policy/carbon pricing is the dominant risk driver for
          Samcheok Blue Power.
        </p>
      </div>

      {/* Comparison Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
        <div
          className="bg-white rounded-lg shadow-sm border-l-4 p-5"
          style={{ borderLeftColor: COLORS.transition }}
        >
          <p className="text-sm text-slate-500 font-medium">Transition Risk CRP</p>
          <p className="text-2xl font-bold mt-1 text-slate-900">
            {modTrans ? `${(modTrans.crp_bps - (baseline?.crp_bps ?? 0)).toFixed(0)} bps` : "N/A"}
          </p>
          <p className="text-xs text-slate-400 mt-1">
            Carbon pricing + coal phase-out
          </p>
        </div>
        <div
          className="bg-white rounded-lg shadow-sm border-l-4 p-5"
          style={{ borderLeftColor: COLORS.physical }}
        >
          <p className="text-sm text-slate-500 font-medium">Physical Risk CRP</p>
          <p className="text-2xl font-bold mt-1 text-slate-900">
            {highPhys && baseline
              ? `${(highPhys.crp_bps - baseline.crp_bps).toFixed(0)} bps`
              : "N/A"}
          </p>
          <p className="text-xs text-slate-400 mt-1">
            Wildfire + drought + water risk
          </p>
        </div>
        <div
          className="bg-white rounded-lg shadow-sm border-l-4 p-5"
          style={{ borderLeftColor: COLORS.credit }}
        >
          <p className="text-sm text-slate-500 font-medium">Rating Impact</p>
          <p className="text-2xl font-bold mt-1 text-slate-900">
            {modTrans && modPhys
              ? `${modTrans.overall_rating} vs ${modPhys.overall_rating}`
              : "N/A"}
          </p>
          <p className="text-xs text-slate-400 mt-1">
            Transition-only vs Physical-only
          </p>
        </div>
      </div>

      {/* Methodology */}
      <div className="bg-white rounded-lg shadow-sm p-6 mb-8">
        <h2 className="text-lg font-semibold text-slate-800 mb-4">
          Shapley Value Methodology
        </h2>
        <div className="bg-slate-50 rounded-lg p-4 font-mono text-sm leading-7">
          <p>For two risk factors (Transition T, Physical P):</p>
          <p className="mt-2 ml-4">
            {"phi(T) = 0.5 * [ (CRP_combined - CRP_physical) + (CRP_transition - CRP_baseline) ]"}
          </p>
          <p className="ml-4">
            {"phi(P) = 0.5 * [ (CRP_combined - CRP_transition) + (CRP_physical - CRP_baseline) ]"}
          </p>
          <p className="mt-2 ml-4 text-slate-500">
            {"Interaction = CRP_combined - CRP_transition - CRP_physical + CRP_baseline"}
          </p>
          <p className="mt-2 text-xs text-slate-500">
            Efficiency property: phi(T) + phi(P) = CRP_combined - CRP_baseline
          </p>
        </div>
      </div>

      {/* Shapley Charts and Table */}
      <div className="bg-white rounded-lg shadow-sm p-6">
        <h2 className="text-lg font-semibold text-slate-800 mb-4">
          Decomposition Results
        </h2>
        <ShapleyDecomposition scenarios={scenarios} />
      </div>
    </>
  );
}
