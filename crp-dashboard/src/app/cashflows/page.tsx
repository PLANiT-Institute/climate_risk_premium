"use client";

import { useState, useEffect } from "react";
import ScenarioSelector from "@/components/dashboard/ScenarioSelector";
import CashflowWaterfall from "@/components/charts/CashflowWaterfall";
import EbitdaTimeSeries from "@/components/charts/EbitdaTimeSeries";
import { CashflowRow } from "@/lib/supabase/types";
import { SCENARIO_LABELS } from "@/lib/constants";

export default function CashflowsPage() {
  const [selected, setSelected] = useState(["baseline"]);
  const [allData, setAllData] = useState<Record<string, CashflowRow[]>>({});
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      const scenarios = Object.keys(SCENARIO_LABELS);
      const result: Record<string, CashflowRow[]> = {};
      await Promise.all(
        scenarios.map(async (s) => {
          try {
            const mod = await import(`@/data/cashflows/${s}.json`);
            result[s] = (mod.default as CashflowRow[]).map((r) => ({
              ...r,
              scenario: s,
            }));
          } catch {
            result[s] = [];
          }
        })
      );
      setAllData(result);
      setLoading(false);
    }
    load();
  }, []);

  const primaryScenario = selected[0] || "baseline";
  const firstYear = allData[primaryScenario]?.[0];

  return (
    <>
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-slate-900">Cashflow Analysis</h1>
        <p className="text-sm text-slate-500 mt-1">
          Revenue, costs, and EBITDA breakdown by scenario
        </p>
      </div>

      <div className="mb-6">
        <label className="text-sm font-medium text-slate-600 mr-3">
          Select Scenarios:
        </label>
        <ScenarioSelector selected={selected} onChange={setSelected} multiple />
      </div>

      {loading ? (
        <div className="text-slate-400 text-center py-12">Loading cashflow data...</div>
      ) : (
        <>
          {/* Waterfall for first year */}
          {firstYear && (
            <div className="bg-white rounded-lg shadow-sm p-6 mb-6">
              <h2 className="text-lg font-semibold text-slate-800 mb-4">
                Year {firstYear.year} Cashflow Waterfall —{" "}
                {SCENARIO_LABELS[primaryScenario]}
              </h2>
              <CashflowWaterfall data={firstYear} />
            </div>
          )}

          {/* EBITDA Time Series */}
          <div className="bg-white rounded-lg shadow-sm p-6 mb-6">
            <h2 className="text-lg font-semibold text-slate-800 mb-4">
              EBITDA Trajectory
            </h2>
            <EbitdaTimeSeries data={allData} scenarios={selected} />
          </div>

          {/* Cashflow Table */}
          <div className="bg-white rounded-lg shadow-sm p-6">
            <h2 className="text-lg font-semibold text-slate-800 mb-4">
              {SCENARIO_LABELS[primaryScenario]} — Annual Cashflows
            </h2>
            <div className="overflow-x-auto">
              <table className="w-full text-xs">
                <thead>
                  <tr className="border-b-2 border-slate-200">
                    <th className="p-2 text-left">Year</th>
                    <th className="p-2 text-right">Revenue ($M)</th>
                    <th className="p-2 text-right">Fuel ($M)</th>
                    <th className="p-2 text-right">Fixed O&M ($M)</th>
                    <th className="p-2 text-right">EBITDA ($M)</th>
                    <th className="p-2 text-right">Net Income ($M)</th>
                    <th className="p-2 text-right">FCF ($M)</th>
                    <th className="p-2 text-right">CF</th>
                  </tr>
                </thead>
                <tbody>
                  {(allData[primaryScenario] || []).map((row) => (
                    <tr
                      key={row.year}
                      className="border-b border-slate-100 hover:bg-slate-50"
                    >
                      <td className="p-2">{row.year}</td>
                      <td className="p-2 text-right">
                        {(row.revenue / 1e6).toFixed(1)}
                      </td>
                      <td className="p-2 text-right text-red-600">
                        {(row.fuel_costs / 1e6).toFixed(1)}
                      </td>
                      <td className="p-2 text-right">
                        {(row.fixed_opex / 1e6).toFixed(1)}
                      </td>
                      <td
                        className={`p-2 text-right font-medium ${
                          row.ebitda < 0 ? "text-red-600" : "text-green-700"
                        }`}
                      >
                        {(row.ebitda / 1e6).toFixed(1)}
                      </td>
                      <td
                        className={`p-2 text-right ${
                          row.net_income < 0 ? "text-red-600" : ""
                        }`}
                      >
                        {(row.net_income / 1e6).toFixed(1)}
                      </td>
                      <td
                        className={`p-2 text-right ${
                          row.free_cash_flow < 0 ? "text-red-600" : ""
                        }`}
                      >
                        {(row.free_cash_flow / 1e6).toFixed(1)}
                      </td>
                      <td className="p-2 text-right">
                        {(row.capacity_factor * 100).toFixed(1)}%
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </>
      )}
    </>
  );
}
