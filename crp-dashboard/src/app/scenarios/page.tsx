import { getScenarioResults } from "@/lib/queries/scenarios";
import ScenarioTable from "@/components/tables/ScenarioTable";
import CrpBarChart from "@/components/charts/CrpBarChart";

export const revalidate = 3600;

export default async function ScenariosPage() {
  const scenarios = await getScenarioResults();

  return (
    <>
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-slate-900">Scenario Comparison</h1>
        <p className="text-sm text-slate-500 mt-1">
          Detailed comparison across 9 climate/transition risk scenarios
        </p>
      </div>

      {/* NPV Chart */}
      <div className="bg-white rounded-lg shadow-sm p-6 mb-6">
        <h2 className="text-lg font-semibold text-slate-800 mb-4">NPV by Scenario ($M)</h2>
        <CrpBarChart data={scenarios} dataKey="npv_million" label="NPV" unit="M" />
      </div>

      {/* IRR Chart */}
      <div className="bg-white rounded-lg shadow-sm p-6 mb-6">
        <h2 className="text-lg font-semibold text-slate-800 mb-4">IRR by Scenario (%)</h2>
        <CrpBarChart data={scenarios} dataKey="irr_pct" label="IRR" unit="%" />
      </div>

      {/* DSCR Chart */}
      <div className="bg-white rounded-lg shadow-sm p-6 mb-6">
        <h2 className="text-lg font-semibold text-slate-800 mb-4">Average DSCR by Scenario</h2>
        <CrpBarChart data={scenarios} dataKey="avg_dscr" label="Avg DSCR" unit="x" />
      </div>

      {/* Full Table */}
      <div className="bg-white rounded-lg shadow-sm p-6">
        <h2 className="text-lg font-semibold text-slate-800 mb-4">Full Scenario Detail</h2>
        <ScenarioTable data={scenarios} />
      </div>
    </>
  );
}
