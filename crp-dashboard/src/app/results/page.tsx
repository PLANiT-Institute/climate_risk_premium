import Link from "next/link";
import { getScenarioResults } from "@/lib/queries/scenarios";

export const revalidate = 3600;

export default async function ResultsPage() {
  const scenarios = await getScenarioResults();
  const baseline = scenarios.find((s) => s.scenario === "baseline");
  const enhanced = scenarios.find((s) => s.scenario === "enhanced_11th_plan");
  const worst = [...scenarios].sort((a, b) => a.npv_million - b.npv_million)[0];

  const baselineNpv = baseline?.npv_million ?? 0;
  const enhancedNpv = enhanced?.npv_million ?? 0;
  const valueSwing = baselineNpv - enhancedNpv;

  const physicalScenarios = scenarios.filter((s) =>
    ["moderate_physical", "high_physical", "severe_drought"].includes(s.scenario)
  );
  const avgPhysicalDelta =
    physicalScenarios.length > 0
      ? physicalScenarios.reduce((acc, s) => acc + (baselineNpv - s.npv_million), 0) /
        physicalScenarios.length
      : 0;

  return (
    <>
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-slate-900">Results Brief</h1>
        <p className="text-sm text-slate-500 mt-1">
          What the current model run says, and how to read it correctly
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
        <div className="bg-white rounded-lg shadow-sm p-5 border-l-4 border-teal-500">
          <p className="text-sm text-slate-500">Baseline NPV</p>
          <p className="text-2xl font-bold text-slate-900">${baselineNpv.toFixed(0)}M</p>
          <p className="text-xs text-slate-500 mt-1">Rating: {baseline?.overall_rating ?? "N/A"}</p>
        </div>
        <div className="bg-white rounded-lg shadow-sm p-5 border-l-4 border-rose-500">
          <p className="text-sm text-slate-500">Enhanced 11th Plan NPV</p>
          <p className="text-2xl font-bold text-rose-700">${enhancedNpv.toFixed(0)}M</p>
          <p className="text-xs text-slate-500 mt-1">Rating: {enhanced?.overall_rating ?? "N/A"}</p>
        </div>
        <div className="bg-white rounded-lg shadow-sm p-5 border-l-4 border-amber-500">
          <p className="text-sm text-slate-500">Value Swing</p>
          <p className="text-2xl font-bold text-slate-900">${valueSwing.toFixed(0)}M</p>
          <p className="text-xs text-slate-500 mt-1">Best-to-stress gap</p>
        </div>
      </div>

      <div className="bg-white rounded-lg shadow-sm p-6 mb-6">
        <h2 className="text-lg font-semibold text-slate-800 mb-3">Core Interpretation</h2>
        <div className="space-y-3 text-sm text-slate-700">
          <p>
            1. In this calibration, transition-policy stress is the dominant value driver. The enhanced policy
            scenario moves NPV deeply negative and pushes ratings into distressed territory.
          </p>
          <p>
            2. Physical-only scenarios are directionally negative but materially smaller in scale. Average NPV
            reduction across physical-only runs is about <span className="font-semibold">${avgPhysicalDelta.toFixed(1)}M</span>.
          </p>
          <p>
            3. Credit repricing is nonlinear: mild stress leaves ratings near investment-grade, but severe policy
            compression propagates to sharp spread/WACC jumps.
          </p>
        </div>
      </div>

      <div className="bg-white rounded-lg shadow-sm p-6 mb-6">
        <h2 className="text-lg font-semibold text-slate-800 mb-3">How To Read This Dashboard</h2>
        <ul className="text-sm text-slate-700 space-y-2 list-disc pl-5">
          <li>
            Use <span className="font-medium">Scenarios</span> for cross-sectional comparison of NPV, CRP, rating, and DSCR.
          </li>
          <li>
            Use <span className="font-medium">Cashflows</span> and <span className="font-medium">Credit Rating</span> pages to trace causality.
          </li>
          <li>
            Use <span className="font-medium">Model Pipeline</span> and <span className="font-medium">Methodology</span> pages for equation-level mapping.
          </li>
          <li>
            For paper-grade claims, rely on repository files under <code>results/</code> and frozen manifests.
          </li>
        </ul>
      </div>

      <div className="bg-slate-50 border border-slate-200 rounded-lg p-5">
        <h3 className="text-sm font-semibold text-slate-800 mb-2">Quick Links</h3>
        <div className="flex flex-wrap gap-2 text-sm">
          <Link className="px-3 py-1.5 rounded bg-white border border-slate-300 hover:bg-slate-100" href="/scenarios">
            Scenario Comparison
          </Link>
          <Link className="px-3 py-1.5 rounded bg-white border border-slate-300 hover:bg-slate-100" href="/model-pipeline">
            Model Pipeline
          </Link>
          <Link className="px-3 py-1.5 rounded bg-white border border-slate-300 hover:bg-slate-100" href="/methodology">
            Methodology
          </Link>
          <Link className="px-3 py-1.5 rounded bg-white border border-slate-300 hover:bg-slate-100" href="/credit">
            Credit Rating
          </Link>
        </div>
        <p className="text-xs text-slate-500 mt-3">
          Worst NPV scenario in current dataset: <span className="font-mono">{worst?.scenario ?? "N/A"}</span>
        </p>
      </div>
    </>
  );
}
