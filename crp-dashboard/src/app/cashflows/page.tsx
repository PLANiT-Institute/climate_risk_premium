"use client";

import { useState, useEffect, useMemo } from "react";
import ScenarioSelector from "@/components/dashboard/ScenarioSelector";
import CashflowWaterfall from "@/components/charts/CashflowWaterfall";
import EbitdaTimeSeries from "@/components/charts/EbitdaTimeSeries";
import FcfTimeSeries from "@/components/charts/FcfTimeSeries";
import { CashflowRow } from "@/lib/types";
import { SCENARIO_LABELS } from "@/lib/constants";
import { getAllCashflows } from "@/lib/queries/cashflows";

export default function CashflowsPage() {
  const [selected, setSelected] = useState(["baseline"]);
  const [yearIndex, setYearIndex] = useState(0);

  const allData = getAllCashflows();
  const loading = false;

  const primaryScenario = selected[0] || "baseline";
  const scenarioData = allData[primaryScenario] || [];
  const years = useMemo(() => scenarioData.map((r) => r.year), [scenarioData]);
  const selectedYear = scenarioData[yearIndex];

  // Reset year index when scenario changes
  useEffect(() => {
    setYearIndex(0);
  }, [primaryScenario]);

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
          {/* Waterfall with year slider */}
          {selectedYear && (
            <div className="bg-white rounded-lg shadow-sm p-6 mb-6">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-lg font-semibold text-slate-800">
                  Year {selectedYear.year} Cashflow Waterfall —{" "}
                  {SCENARIO_LABELS[primaryScenario]}
                </h2>
                <span className="text-sm font-mono text-slate-500">
                  EBITDA: ${(selectedYear.ebitda / 1e6).toFixed(0)}M
                </span>
              </div>

              <CashflowWaterfall data={selectedYear} />

              {/* Year slider */}
              {years.length > 1 && (
                <div className="mt-4 px-2">
                  <input
                    type="range"
                    min={0}
                    max={years.length - 1}
                    value={yearIndex}
                    onChange={(e) => setYearIndex(Number(e.target.value))}
                    className="w-full accent-teal-600"
                  />
                  <div className="flex justify-between text-xs text-slate-400 mt-1">
                    <span>{years[0]}</span>
                    <span>{years[Math.floor(years.length / 2)]}</span>
                    <span>{years[years.length - 1]}</span>
                  </div>
                </div>
              )}
            </div>
          )}

          {/* EBITDA Time Series */}
          <div className="bg-white rounded-lg shadow-sm p-6 mb-6">
            <h2 className="text-lg font-semibold text-slate-800 mb-4">
              EBITDA Trajectory
            </h2>
            <EbitdaTimeSeries data={allData} scenarios={selected} />
          </div>

          {/* Free Cash Flow Time Series */}
          <div className="bg-white rounded-lg shadow-sm p-6 mb-6">
            <h2 className="text-lg font-semibold text-slate-800 mb-4">
              Free Cash Flow Trajectory
            </h2>
            <FcfTimeSeries data={allData} scenarios={selected} />
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
                  {scenarioData.map((row) => (
                    <tr
                      key={row.year}
                      className={`border-b border-slate-100 hover:bg-slate-50 ${
                        row.year === selectedYear?.year
                          ? "bg-teal-50 font-medium"
                          : ""
                      }`}
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
