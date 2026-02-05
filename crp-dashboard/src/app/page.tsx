import { getScenarioResults } from "@/lib/queries/scenarios";
import KpiCard from "@/components/dashboard/KpiCard";
import CrpBarChart from "@/components/charts/CrpBarChart";
import ScenarioTable from "@/components/tables/ScenarioTable";
import { COLORS, RATING_COLORS } from "@/lib/constants";

export const revalidate = 3600;

export default async function ExecutiveSummary() {
  const scenarios = await getScenarioResults();

  const baseline = scenarios.find((s) => s.scenario === "baseline");
  const maxCrp = scenarios.reduce((max, s) =>
    s.crp_bps > max.crp_bps ? s : max
  );
  const ratings = scenarios.map((s) => s.overall_rating);
  const npvs = scenarios.map((s) => s.npv_million);

  return (
    <>
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-slate-900">Executive Summary</h1>
        <p className="text-sm text-slate-500 mt-1">
          Climate Risk Premium analysis for Samcheok Blue Power (2,100 MW)
        </p>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        <KpiCard
          title="Baseline CRP"
          value={`${baseline?.crp_bps.toFixed(0) ?? "N/A"} bps`}
          subtitle={`Rating: ${baseline?.overall_rating}`}
          color={COLORS.primary}
        />
        <KpiCard
          title="Maximum CRP"
          value={`${maxCrp.crp_bps.toFixed(0)} bps`}
          subtitle={`${maxCrp.scenario.replace(/_/g, " ")}`}
          color={COLORS.danger}
          trend="up"
        />
        <KpiCard
          title="Rating Range"
          value={`${ratings[0]} — ${ratings[ratings.length - 1]}`}
          subtitle={`${scenarios.filter((s) => s.is_investment_grade).length}/${scenarios.length} investment grade`}
          color={RATING_COLORS[ratings[0]] || COLORS.success}
        />
        <KpiCard
          title="NPV Range"
          value={`$${Math.min(...npvs).toFixed(0)}M — $${Math.max(...npvs).toFixed(0)}M`}
          subtitle={`Baseline: $${baseline?.npv_million.toFixed(0)}M`}
          color={COLORS.cashflow}
        />
      </div>

      {/* CRP Bar Chart */}
      <div className="bg-white rounded-lg shadow-sm p-6 mb-8">
        <h2 className="text-lg font-semibold text-slate-800 mb-4">
          Climate Risk Premium by Scenario
        </h2>
        <CrpBarChart data={scenarios} />
      </div>

      {/* Scenario Table */}
      <div className="bg-white rounded-lg shadow-sm p-6">
        <h2 className="text-lg font-semibold text-slate-800 mb-4">
          Scenario Overview
        </h2>
        <ScenarioTable data={scenarios} compact />
      </div>
    </>
  );
}
