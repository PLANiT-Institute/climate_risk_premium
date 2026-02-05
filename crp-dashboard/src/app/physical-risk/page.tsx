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
    baseline_rate: "0.055%",
    rcp45_2050: "0.082%",
    rcp85_2060: "0.220%",
    source: "Kim et al. (2025)",
    doi: "10.1007/s11069-025-07169-4",
    methodology:
      "15 fires/yr × 0.10 impact × 32h / 8,760h, climate multiplied 1.0–4.0x",
  },
  {
    hazard: "Flood",
    baseline_rate: "0.003%",
    rcp45_2050: "0.003%",
    rcp85_2060: "0.003%",
    source: "Kang & Lee (2024)",
    doi: "10.3390/w16202987",
    methodology:
      "0.3% surge prob × 0.70 impact × 120h / 8,760h, multiplied up to 2.64x",
  },
  {
    hazard: "Sea Level Rise",
    baseline_rate: "0.000%",
    rcp45_2050: "0.042%",
    rcp85_2060: "0.161%",
    source: "IPCC AR6 WGI Ch.9",
    doi: "ipcc.ch",
    methodology: "SLR (m) × 0.0022 derate + temp effect + storm surge amplification",
  },
];

const COMPOUND_RISK = {
  formula: "M_compound = 1 + (ρ × S), where ρ = 0.3, max 1.25x",
  source: "Zscheischler et al. (2018)",
  doi: "10.1038/s41558-018-0156-3",
};

export default function PhysicalRiskPage() {
  const [scenario, setScenario] = useState<RiskScenario>("rcp85_2060");

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
          Physical risk is minimal (~0.06–0.44% CF loss). Transition/policy risk
          is the dominant concern for Samcheok.
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
                <th className="p-3 text-right">Baseline Rate</th>
                <th className="p-3 text-right">RCP4.5 (2050)</th>
                <th className="p-3 text-right">RCP8.5 (2060)</th>
                <th className="p-3 text-left">Source</th>
                <th className="p-3 text-left">Methodology</th>
              </tr>
            </thead>
            <tbody>
              {HAZARD_DATA.map((h) => (
                <tr key={h.hazard} className="border-b border-slate-100">
                  <td className="p-3 font-medium">{h.hazard}</td>
                  <td className="p-3 text-right font-mono">{h.baseline_rate}</td>
                  <td className="p-3 text-right font-mono">{h.rcp45_2050}</td>
                  <td className="p-3 text-right font-mono text-red-600">
                    {h.rcp85_2060}
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
                <th className="p-3 text-left">Year</th>
                <th className="p-3 text-left">Scenario</th>
                <th className="p-3 text-right">Wildfire</th>
                <th className="p-3 text-right">Flood</th>
                <th className="p-3 text-right">SLR</th>
                <th className="p-3 text-right font-semibold">Total CF Loss</th>
              </tr>
            </thead>
            <tbody>
              {[
                { year: 2024, scenario: "Baseline", wf: "0.055%", fl: "0.003%", slr: "0.000%", total: "0.058%" },
                { year: 2050, scenario: "RCP4.5", wf: "0.082%", fl: "0.003%", slr: "0.042%", total: "0.127%" },
                { year: 2060, scenario: "RCP8.5", wf: "0.220%", fl: "0.003%", slr: "0.161%", total: "0.384%" },
              ].map((r) => (
                <tr key={`${r.year}-${r.scenario}`} className="border-b border-slate-100">
                  <td className="p-3">{r.year}</td>
                  <td className="p-3">{r.scenario}</td>
                  <td className="p-3 text-right font-mono">{r.wf}</td>
                  <td className="p-3 text-right font-mono">{r.fl}</td>
                  <td className="p-3 text-right font-mono">{r.slr}</td>
                  <td className="p-3 text-right font-mono font-bold">{r.total}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* CLIMADA Validation */}
      <div className="bg-white rounded-lg shadow-sm p-6">
        <h2 className="text-lg font-semibold text-slate-800 mb-4">
          CLIMADA vs Literature Validation
        </h2>
        <div className="grid grid-cols-2 gap-4">
          <div className="bg-blue-50 rounded-lg p-4">
            <p className="text-sm font-semibold text-blue-800">CLIMADA Total</p>
            <p className="text-2xl font-bold text-blue-600">0.029%</p>
          </div>
          <div className="bg-green-50 rounded-lg p-4">
            <p className="text-sm font-semibold text-green-800">Literature Total</p>
            <p className="text-2xl font-bold text-green-600">0.058%</p>
          </div>
        </div>
        <p className="text-xs text-slate-500 mt-3">
          CLIMADA estimates are ~0.50x of literature-based estimates. Literature approach
          adopted as conservative upper bound.
        </p>
      </div>
    </>
  );
}
