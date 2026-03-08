"use client";

import { useState } from "react";
import dynamic from "next/dynamic";
import { COLORS } from "@/lib/constants";
import MapSkeleton from "@/components/maps/MapSkeleton";
import type { RiskScenario } from "@/lib/geo/types";
import { SCENARIO_RISKS } from "@/lib/geo/types";

const PhysicalRiskMap = dynamic(
  () => import("@/components/maps/PhysicalRiskMap"),
  { ssr: false, loading: () => <MapSkeleton /> }
);

const HAZARD_NOTES = [
  {
    hazard: "Wildfire",
    source: "CLIMADA via PLANiT",
    formula: "outage_rate = AAI_KRW / total_asset_value_krw",
  },
  {
    hazard: "Drought",
    source: "PhysRisk via PLANiT",
    formula: "capacity_derate = impact_mean × drought_severity_scale",
  },
  {
    hazard: "Water Risk",
    source: "PhysRisk via PLANiT",
    formula: "water_constrained_capacity = max(0, 1 - impact_mean)",
  },
];

const scenarioRows: Array<{ scenario: string; key: RiskScenario }> = [
  { scenario: "Baseline (2024)", key: "baseline" },
  { scenario: "SSP1-2.6 (2040)", key: "ssp126_2040" },
  { scenario: "SSP5-8.5 (2050)", key: "ssp585_2050" },
];

function pct(x: number): string {
  return `${(x * 100).toFixed(3)}%`;
}

export default function PhysicalRiskPage() {
  const [scenario, setScenario] = useState<RiskScenario>("ssp585_2050");

  return (
    <>
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-slate-900">Physical Risk Analysis</h1>
        <p className="text-sm text-slate-500 mt-1">
          PLANiT hazard conversion and site-level physical-risk interpretation
        </p>
      </div>

      <div
        className="rounded-lg p-4 mb-6 border-l-4"
        style={{ borderLeftColor: COLORS.physical, backgroundColor: "#fef2f2" }}
      >
        <p className="text-sm font-medium text-red-800">
          In the current canonical run, physical-only effects are negative but modest relative to
          severe transition-policy stress.
        </p>
      </div>

      <div className="bg-white rounded-lg shadow-sm p-6 mb-6">
        <h2 className="text-lg font-semibold text-slate-800 mb-4">
          Samcheok Plant Location & Risk Zones
        </h2>
        <p className="text-sm text-slate-500 mb-4">
          Interactive map for the Samcheok asset cluster. Scenario toggle changes hazard overlay severity.
        </p>
        <PhysicalRiskMap scenario={scenario} onScenarioChange={setScenario} showControls={true} />
      </div>

      <div className="bg-white rounded-lg shadow-sm p-6 mb-6">
        <h2 className="text-lg font-semibold text-slate-800 mb-4">Conversion Logic (Production)</h2>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b-2 border-slate-200">
                <th className="p-3 text-left">Hazard</th>
                <th className="p-3 text-left">Source</th>
                <th className="p-3 text-left">Formula</th>
              </tr>
            </thead>
            <tbody>
              {HAZARD_NOTES.map((h) => (
                <tr key={h.hazard} className="border-b border-slate-100">
                  <td className="p-3 font-medium">{h.hazard}</td>
                  <td className="p-3 text-slate-600">{h.source}</td>
                  <td className="p-3 font-mono text-xs text-slate-700">{h.formula}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      <div className="bg-white rounded-lg shadow-sm p-6 mb-6">
        <h2 className="text-lg font-semibold text-slate-800 mb-4">Scenario Hazard Magnitudes</h2>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b-2 border-slate-200">
                <th className="p-3 text-left">Scenario</th>
                <th className="p-3 text-right">Wildfire</th>
                <th className="p-3 text-right">Drought</th>
                <th className="p-3 text-right">Water Risk</th>
                <th className="p-3 text-right font-semibold">Total CF Loss</th>
              </tr>
            </thead>
            <tbody>
              {scenarioRows.map((row) => {
                const r = SCENARIO_RISKS[row.key];
                return (
                  <tr key={row.scenario} className="border-b border-slate-100">
                    <td className="p-3">{row.scenario}</td>
                    <td className="p-3 text-right font-mono">{pct(r.wildfire)}</td>
                    <td className="p-3 text-right font-mono">{pct(r.drought)}</td>
                    <td className="p-3 text-right font-mono">{pct(r.waterRisk)}</td>
                    <td className="p-3 text-right font-mono font-bold">{pct(r.total)}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
        <p className="text-xs text-slate-500 mt-3">
          Compound multiplier is fixed at 1.0 in the current production-style path shown here.
        </p>
      </div>

      <div className="bg-slate-50 border border-slate-200 rounded-lg p-5">
        <h3 className="text-sm font-semibold text-slate-800 mb-2">Data Provenance</h3>
        <ul className="text-sm text-slate-700 space-y-1 list-disc pl-5">
          <li>Frozen CSV snapshots: `Physicalrisk_PLANiT/data/results/`</li>
          <li>Pipeline conversion: `src/planit/adapter.py`</li>
          <li>Operational application: `src/financials/cashflow.py`</li>
        </ul>
      </div>
    </>
  );
}
