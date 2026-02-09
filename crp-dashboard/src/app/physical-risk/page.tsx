"use client";

import { useState } from "react";
import dynamic from "next/dynamic";
import { COLORS } from "@/lib/constants";
import MapSkeleton from "@/components/maps/MapSkeleton";
import type { RiskScenario } from "@/lib/geo/types";

const PhysicalRiskMap = dynamic(
  () => import("@/components/maps/PhysicalRiskMap"),
  { ssr: false, loading: () => <MapSkeleton /> }
);

const HAZARD_DATA = [
  {
    hazard: "Wildfire",
    baseline: "0.001%",
    ssp126_2040: "0.005%",
    ssp585_2050: "0.001%",
    source: "CLIMADA / PLANiT",
    doi: "https://github.com/CLIMADA-project/climada_python",
    methodology:
      "AAI probabilistic: 20 events, KRW / 4.879T total asset value",
  },
  {
    hazard: "Drought",
    baseline: "0.094%",
    ssp126_2040: "0.257%",
    ssp585_2050: "0.101%",
    source: "PhysRisk / PLANiT",
    doi: "https://github.com/os-climate/physrisk",
    methodology:
      "Water stress impact_mean × 1.0 severity scale",
  },
  {
    hazard: "Water Risk",
    baseline: "0.000%",
    ssp126_2040: "0.559%",
    ssp585_2050: "0.546%",
    source: "PhysRisk / PLANiT",
    doi: "https://github.com/os-climate/physrisk",
    methodology: "Water availability: max(0, 1 - impact_mean) constraint",
  },
];

const COMPOUND_RISK = {
  formula: "M_compound = 1 + (ρ × S), where ρ = 0.3, max 1.25x",
  source: "Zscheischler et al. (2018)",
  doi: "10.1038/s41558-018-0156-3",
};

export default function PhysicalRiskPage() {
  const [scenario, setScenario] = useState<RiskScenario>("ssp585_2050");

  return (
    <>
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-slate-900">Physical Risk Analysis</h1>
        <p className="text-sm text-slate-500 mt-1">
          Hazard-level parameters and capacity factor impact for Samcheok site
        </p>
      </div>

      {/* Key Finding */}
      <div
        className="rounded-lg p-4 mb-6 border-l-4"
        style={{ borderLeftColor: COLORS.physical, backgroundColor: "#fef2f2" }}
      >
        <p className="text-sm font-medium text-red-800">
          Physical risk is modest (~0.10–0.82% CF loss). Transition/policy risk
          remains the dominant concern for Samcheok.
        </p>
      </div>

      {/* Interactive Map */}
      <div className="bg-white rounded-lg shadow-sm p-6 mb-6">
        <h2 className="text-lg font-semibold text-slate-800 mb-4">
          Samcheok Plant Location & Risk Zones
        </h2>
        <p className="text-sm text-slate-500 mb-4">
          Interactive map showing power infrastructure and climate hazard zones. Toggle scenarios
          to visualize risk changes under different climate pathways.
        </p>
        <PhysicalRiskMap
          scenario={scenario}
          onScenarioChange={setScenario}
          showControls={true}
        />
      </div>

      {/* Hazard Parameters Table */}
      <div className="bg-white rounded-lg shadow-sm p-6 mb-6">
        <h2 className="text-lg font-semibold text-slate-800 mb-4">
          Hazard Parameters
        </h2>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b-2 border-slate-200">
                <th className="p-3 text-left">Hazard</th>
                <th className="p-3 text-right">Baseline</th>
                <th className="p-3 text-right">SSP1-2.6 (2040)</th>
                <th className="p-3 text-right">SSP5-8.5 (2050)</th>
                <th className="p-3 text-left">Source</th>
                <th className="p-3 text-left">Methodology</th>
              </tr>
            </thead>
            <tbody>
              {HAZARD_DATA.map((h) => (
                <tr key={h.hazard} className="border-b border-slate-100">
                  <td className="p-3 font-medium">{h.hazard}</td>
                  <td className="p-3 text-right font-mono">{h.baseline}</td>
                  <td className="p-3 text-right font-mono">{h.ssp126_2040}</td>
                  <td className="p-3 text-right font-mono text-red-600">
                    {h.ssp585_2050}
                  </td>
                  <td className="p-3">
                    <a
                      href={
                        h.doi.startsWith("http")
                          ? h.doi
                          : `https://doi.org/${h.doi}`
                      }
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-teal-600 hover:underline"
                    >
                      {h.source}
                    </a>
                  </td>
                  <td className="p-3 text-xs text-slate-500">{h.methodology}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Compound Risk */}
      <div className="bg-white rounded-lg shadow-sm p-6 mb-6">
        <h2 className="text-lg font-semibold text-slate-800 mb-4">
          Compound Risk Multiplier
        </h2>
        <div className="bg-slate-50 rounded-lg p-4">
          <p className="font-mono text-sm mb-2">{COMPOUND_RISK.formula}</p>
          <p className="text-xs text-slate-500">
            Source:{" "}
            <a
              href={`https://doi.org/${COMPOUND_RISK.doi}`}
              target="_blank"
              rel="noopener noreferrer"
              className="text-teal-600 hover:underline"
            >
              {COMPOUND_RISK.source}
            </a>
          </p>
        </div>
      </div>

      {/* Total CF Impact */}
      <div className="bg-white rounded-lg shadow-sm p-6 mb-6">
        <h2 className="text-lg font-semibold text-slate-800 mb-4">
          Total Capacity Factor Reduction
        </h2>
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
              {[
                { scenario: "Baseline (2024)", wf: "0.001%", dr: "0.094%", wr: "0.000%", total: "0.095%" },
                { scenario: "SSP1-2.6 (2040)", wf: "0.005%", dr: "0.257%", wr: "0.559%", total: "0.820%" },
                { scenario: "SSP5-8.5 (2050)", wf: "0.001%", dr: "0.101%", wr: "0.546%", total: "0.648%" },
              ].map((r) => (
                <tr key={r.scenario} className="border-b border-slate-100">
                  <td className="p-3">{r.scenario}</td>
                  <td className="p-3 text-right font-mono">{r.wf}</td>
                  <td className="p-3 text-right font-mono">{r.dr}</td>
                  <td className="p-3 text-right font-mono">{r.wr}</td>
                  <td className="p-3 text-right font-mono font-bold">{r.total}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* PLANiT vs Literature Validation */}
      <div className="bg-white rounded-lg shadow-sm p-6">
        <h2 className="text-lg font-semibold text-slate-800 mb-4">
          PLANiT vs Literature Validation
        </h2>
        <div className="grid grid-cols-2 gap-4">
          <div className="bg-blue-50 rounded-lg p-4">
            <p className="text-sm font-semibold text-blue-800">PLANiT Wildfire AAI</p>
            <p className="text-2xl font-bold text-blue-600">67.9M KRW</p>
            <p className="text-xs text-blue-500 mt-1">→ 0.001% outage rate</p>
          </div>
          <div className="bg-green-50 rounded-lg p-4">
            <p className="text-sm font-semibold text-green-800">Literature Wildfire</p>
            <p className="text-2xl font-bold text-green-600">0.055%</p>
            <p className="text-xs text-green-500 mt-1">Kim et al. (2025)</p>
          </div>
        </div>
        <p className="text-xs text-slate-500 mt-3">
          PLANiT uses CLIMADA probabilistic modeling (AAI over 20 simulated events);
          literature uses incident-based estimation. PLANiT is lower but models actual
          probabilistic impact on asset value (67.9M KRW / 4.879T total asset).
        </p>
      </div>
    </>
  );
}
