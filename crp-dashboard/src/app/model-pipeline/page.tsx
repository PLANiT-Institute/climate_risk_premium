"use client";

import { useState, useRef } from "react";
import EquationBlock from "@/components/methodology/EquationBlock";
import { RATING_COLORS, RATING_SPREADS } from "@/lib/constants";

type SectionKey =
  | "overview"
  | "input"
  | "physical"
  | "transition"
  | "cashflow"
  | "credit";

const SECTIONS: { key: SectionKey; title: string; color: string }[] = [
  { key: "overview", title: "1. Pipeline Overview", color: "#0ea5e9" },
  { key: "input", title: "2. Input Data", color: "#6366f1" },
  { key: "physical", title: "3. Physical Risk — PLANiT Integration", color: "#ef4444" },
  { key: "transition", title: "4. Transition Risk", color: "#8b5cf6" },
  { key: "cashflow", title: "5. Cashflow Computation", color: "#10b981" },
  { key: "credit", title: "6. Credit Rating & CRP", color: "#f59e0b" },
];

const PIPELINE_STEPS = [
  { label: "Input Data", section: "input", color: "#6366f1", bg: "#eef2ff" },
  { label: "Physical Risk", section: "physical", color: "#ef4444", bg: "#fef2f2" },
  { label: "Transition Risk", section: "transition", color: "#8b5cf6", bg: "#f5f3ff" },
  { label: "Cashflow Model", section: "cashflow", color: "#10b981", bg: "#ecfdf5" },
  { label: "Credit Rating & CRP", section: "credit", color: "#f59e0b", bg: "#fffbeb" },
];

const SCENARIO_DEFS = [
  { name: "baseline", type: "baseline", transition: "—", physical: "—", market: "—", ssp: "SSP1-2.6 / 2024" },
  { name: "moderate_transition", type: "transition", transition: "Moderate", physical: "—", market: "—", ssp: "—" },
  { name: "aggressive_transition", type: "transition", transition: "Aggressive", physical: "—", market: "—", ssp: "—" },
  { name: "moderate_physical", type: "physical", transition: "—", physical: "Moderate", market: "—", ssp: "SSP1-2.6 / 2040" },
  { name: "high_physical", type: "physical", transition: "—", physical: "High", market: "—", ssp: "SSP5-8.5 / 2040" },
  { name: "combined_moderate", type: "combined", transition: "Moderate", physical: "Moderate", market: "—", ssp: "SSP1-2.6 / 2040" },
  { name: "combined_aggressive", type: "combined", transition: "Aggressive", physical: "High", market: "—", ssp: "SSP5-8.5 / 2040" },
  { name: "low_demand", type: "market", transition: "—", physical: "—", market: "Low Demand", ssp: "—" },
  { name: "severe_drought", type: "physical", transition: "—", physical: "Drought", market: "—", ssp: "SSP5-8.5 / 2050" },
  { name: "enhanced_11th_plan", type: "transition", transition: "Enhanced 11th Plan", physical: "—", market: "—", ssp: "—" },
  { name: "enhanced_combined", type: "combined", transition: "Enhanced 11th Plan", physical: "High", market: "—", ssp: "SSP5-8.5 / 2040" },
];

const TYPE_BADGE: Record<string, { bg: string; text: string }> = {
  baseline: { bg: "#f1f5f9", text: "#475569" },
  transition: { bg: "#f3e8ff", text: "#7c3aed" },
  physical: { bg: "#dbeafe", text: "#2563eb" },
  combined: { bg: "#fff7ed", text: "#ea580c" },
  market: { bg: "#dcfce7", text: "#16a34a" },
};

const SSP_MAP = [
  { scenario: "baseline", ssp: "SSP1-2.6", year: 2024, desc: "Current conditions (near-term)" },
  { scenario: "moderate_physical", ssp: "SSP1-2.6", year: 2040, desc: "Low-emission pathway, mid-century" },
  { scenario: "high_physical", ssp: "SSP5-8.5", year: 2040, desc: "High-emission pathway, mid-century" },
  { scenario: "severe_drought", ssp: "SSP5-8.5", year: 2050, desc: "High-emission pathway, 2050 drought" },
];

const KIS_CRITERIA = [
  { name: "Industry Risk", weight: "15%", desc: "Coal power market outlook, regulatory environment, competitive dynamics" },
  { name: "Business Risk", weight: "20%", desc: "Market position, diversification, operational efficiency" },
  { name: "Financial Risk", weight: "25%", desc: "Leverage, coverage ratios (DSCR), liquidity, cash flow stability" },
  { name: "Management", weight: "10%", desc: "Governance quality, strategic planning, risk management" },
  { name: "Cash Flow Adequacy", weight: "20%", desc: "Debt repayment capacity, capital expenditure coverage" },
  { name: "ESG / Climate", weight: "10%", desc: "Transition readiness, physical exposure, carbon intensity" },
];

export default function ModelPipelinePage() {
  const [open, setOpen] = useState<Record<SectionKey, boolean>>({
    overview: true,
    input: true,
    physical: true,
    transition: true,
    cashflow: true,
    credit: true,
  });

  const refs: Record<SectionKey, React.RefObject<HTMLDivElement | null>> = {
    overview: useRef<HTMLDivElement>(null),
    input: useRef<HTMLDivElement>(null),
    physical: useRef<HTMLDivElement>(null),
    transition: useRef<HTMLDivElement>(null),
    cashflow: useRef<HTMLDivElement>(null),
    credit: useRef<HTMLDivElement>(null),
  };

  const toggle = (key: SectionKey) =>
    setOpen((prev) => ({ ...prev, [key]: !prev[key] }));

  const scrollTo = (section: string) => {
    const ref = refs[section as SectionKey];
    if (ref?.current) {
      ref.current.scrollIntoView({ behavior: "smooth", block: "start" });
      setOpen((prev) => ({ ...prev, [section]: true }));
    }
  };

  return (
    <>
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-slate-900">Model Pipeline</h1>
        <p className="text-sm text-slate-500 mt-1">
          End-to-end data flow from input parameters to Climate Risk Premium
        </p>
      </div>

      {/* ── Section 1: Pipeline Overview ── */}
      <div ref={refs.overview} className="bg-white rounded-lg shadow-sm p-6 mb-6">
        <button
          onClick={() => toggle("overview")}
          className="flex items-center justify-between w-full text-left"
        >
          <h2 className="text-lg font-semibold text-slate-800">
            1. Pipeline Overview
          </h2>
          <svg
            className={`w-5 h-5 text-slate-400 transition-transform ${open.overview ? "rotate-180" : ""}`}
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
          </svg>
        </button>
        {open.overview && (
          <div className="mt-4">
            <div className="flex flex-col lg:flex-row items-center gap-2 lg:gap-0">
              {PIPELINE_STEPS.map((step, i) => (
                <div key={step.label} className="flex items-center flex-col lg:flex-row">
                  <button
                    onClick={() => scrollTo(step.section)}
                    className="rounded-lg px-5 py-3 text-sm font-medium transition-all hover:scale-105 cursor-pointer min-w-[140px] text-center"
                    style={{ backgroundColor: step.bg, color: step.color, border: `1.5px solid ${step.color}` }}
                  >
                    {step.label}
                  </button>
                  {i < PIPELINE_STEPS.length - 1 && (
                    <>
                      <svg className="hidden lg:block w-8 h-8 text-slate-300 mx-1 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                      </svg>
                      <svg className="lg:hidden w-6 h-6 text-slate-300 my-1 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 14l-7 7-7-7" />
                      </svg>
                    </>
                  )}
                </div>
              ))}
            </div>
            <p className="text-xs text-slate-400 mt-3 text-center">
              Click any stage to jump to its detailed section below
            </p>
          </div>
        )}
      </div>

      {/* ── Section 2: Input Data ── */}
      <div ref={refs.input} className="bg-white rounded-lg shadow-sm p-6 mb-6">
        <button
          onClick={() => toggle("input")}
          className="flex items-center justify-between w-full text-left"
        >
          <h2 className="text-lg font-semibold text-slate-800">
            2. Input Data
          </h2>
          <svg
            className={`w-5 h-5 text-slate-400 transition-transform ${open.input ? "rotate-180" : ""}`}
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
          </svg>
        </button>
        {open.input && (
          <div className="mt-4 space-y-6">
            {/* Plant Parameters */}
            <div>
              <h3 className="text-sm font-semibold text-slate-700 mb-3">Plant Parameters</h3>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                {[
                  { label: "Capacity", value: "2,100 MW" },
                  { label: "Capacity Factor", value: "85%" },
                  { label: "Plant Life", value: "40 years" },
                  { label: "CAPEX", value: "USD 4.9B" },
                  { label: "Fuel Cost", value: "$2.5/GJ" },
                  { label: "Heat Rate", value: "8.8 GJ/MWh" },
                  { label: "Emission Factor", value: "0.82 tCO₂/MWh" },
                  { label: "Discount Rate", value: "8%" },
                ].map((p) => (
                  <div
                    key={p.label}
                    className="bg-slate-50 rounded-lg p-3"
                  >
                    <p className="text-xs text-slate-500">{p.label}</p>
                    <p className="text-sm font-semibold text-slate-800 mt-0.5">{p.value}</p>
                  </div>
                ))}
              </div>
            </div>

            {/* Scenario Definitions */}
            <div>
              <h3 className="text-sm font-semibold text-slate-700 mb-3">Scenario Definitions (11 Scenarios)</h3>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b-2 border-slate-200">
                      <th className="p-2 text-left">Scenario</th>
                      <th className="p-2 text-center">Type</th>
                      <th className="p-2 text-left">Transition</th>
                      <th className="p-2 text-left">Physical</th>
                      <th className="p-2 text-left">Market</th>
                      <th className="p-2 text-left">SSP / Year</th>
                    </tr>
                  </thead>
                  <tbody>
                    {SCENARIO_DEFS.map((s) => {
                      const badge = TYPE_BADGE[s.type];
                      return (
                        <tr key={s.name} className="border-b border-slate-100">
                          <td className="p-2 font-mono text-xs">{s.name}</td>
                          <td className="p-2 text-center">
                            <span
                              className="px-2 py-0.5 rounded text-xs font-medium"
                              style={{ backgroundColor: badge.bg, color: badge.text }}
                            >
                              {s.type}
                            </span>
                          </td>
                          <td className="p-2 text-slate-600">{s.transition}</td>
                          <td className="p-2 text-slate-600">{s.physical}</td>
                          <td className="p-2 text-slate-600">{s.market}</td>
                          <td className="p-2 text-slate-600 text-xs">{s.ssp}</td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </div>

            {/* PLANiT Data Sources */}
            <div>
              <h3 className="text-sm font-semibold text-slate-700 mb-3">PLANiT Data Sources</h3>
              <div className="bg-slate-50 rounded-lg p-4 space-y-2 text-sm">
                <div className="flex items-start gap-2">
                  <span className="font-mono text-xs bg-red-100 text-red-700 px-2 py-0.5 rounded flex-shrink-0">Wildfire</span>
                  <span className="text-slate-600">
                    CLIMADA-computed Annual Average Impact (AAI) per SSP × year anchor.
                    CSV: <code className="text-xs bg-slate-200 px-1 rounded">wildfire_results_*.csv</code>
                  </span>
                </div>
                <div className="flex items-start gap-2">
                  <span className="font-mono text-xs bg-amber-100 text-amber-700 px-2 py-0.5 rounded flex-shrink-0">Drought</span>
                  <span className="text-slate-600">
                    PhysRisk drought impact_mean per SSP × year.
                    CSV: <code className="text-xs bg-slate-200 px-1 rounded">drought_results_*.csv</code>
                  </span>
                </div>
                <div className="flex items-start gap-2">
                  <span className="font-mono text-xs bg-blue-100 text-blue-700 px-2 py-0.5 rounded flex-shrink-0">Water Risk</span>
                  <span className="text-slate-600">
                    PhysRisk water_risk impact_mean per SSP × year.
                    CSV: <code className="text-xs bg-slate-200 px-1 rounded">water_risk_results_*.csv</code>
                  </span>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* ── Section 3: Physical Risk — PLANiT Integration ── */}
      <div ref={refs.physical} className="bg-white rounded-lg shadow-sm p-6 mb-6">
        <button
          onClick={() => toggle("physical")}
          className="flex items-center justify-between w-full text-left"
        >
          <h2 className="text-lg font-semibold text-slate-800">
            3. Physical Risk — PLANiT Integration
          </h2>
          <svg
            className={`w-5 h-5 text-slate-400 transition-transform ${open.physical ? "rotate-180" : ""}`}
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
          </svg>
        </button>
        {open.physical && (
          <div className="mt-4 space-y-6">
            {/* PLANiT Data Flow Diagram */}
            <div>
              <h3 className="text-sm font-semibold text-slate-700 mb-3">PLANiT Data Flow</h3>
              <div className="bg-slate-50 rounded-lg p-5">
                <div className="grid grid-cols-1 md:grid-cols-[1fr_auto_1fr_auto_1fr] items-center gap-3">
                  {/* Left column - sources */}
                  <div className="space-y-3">
                    <div className="bg-red-50 border border-red-200 rounded-lg p-3 text-center">
                      <p className="text-xs font-semibold text-red-700">CLIMADA</p>
                      <p className="text-xs text-red-600 mt-1">Wildfire AAI</p>
                    </div>
                    <div className="bg-amber-50 border border-amber-200 rounded-lg p-3 text-center">
                      <p className="text-xs font-semibold text-amber-700">PhysRisk</p>
                      <p className="text-xs text-amber-600 mt-1">Drought / Water Risk</p>
                    </div>
                  </div>

                  {/* Arrow */}
                  <div className="flex justify-center">
                    <svg className="w-8 h-8 text-slate-300 hidden md:block" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                    </svg>
                    <svg className="w-6 h-6 text-slate-300 md:hidden" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 14l-7 7-7-7" />
                    </svg>
                  </div>

                  {/* Middle - Adapter */}
                  <div className="bg-indigo-50 border border-indigo-200 rounded-lg p-3 text-center">
                    <p className="text-xs font-semibold text-indigo-700">PLANiT Adapter</p>
                    <p className="text-xs text-indigo-600 mt-1">Converts hazard data → model parameters</p>
                  </div>

                  {/* Arrow */}
                  <div className="flex justify-center">
                    <svg className="w-8 h-8 text-slate-300 hidden md:block" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                    </svg>
                    <svg className="w-6 h-6 text-slate-300 md:hidden" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 14l-7 7-7-7" />
                    </svg>
                  </div>

                  {/* Right - Output */}
                  <div className="bg-green-50 border border-green-200 rounded-lg p-3 text-center">
                    <p className="text-xs font-semibold text-green-700">PhysicalAdjustments</p>
                    <p className="text-xs text-green-600 mt-1">outage_rate, capacity_derate, water_cap</p>
                  </div>
                </div>
              </div>
            </div>

            {/* Conversion Formulas */}
            <div>
              <h3 className="text-sm font-semibold text-slate-700 mb-3">Conversion Formulas</h3>
              <EquationBlock
                label="Wildfire: AAI → Outage Rate"
                latex="\text{outage\_rate} = \frac{\text{AAI}}{4.879 \times 10^{12}} \quad \text{(asset-value normalization)}"
              />
              <EquationBlock
                label="Drought: Impact Mean → Capacity Derate"
                latex="\text{capacity\_derate} = \text{impact\_mean} \times 1.0"
              />
              <EquationBlock
                label="Water Risk: Impact Mean → Water Capacity"
                latex="\text{water\_cap} = \max(0,\; 1 - \text{impact\_mean})"
              />
            </div>

            {/* Year Interpolation */}
            <div>
              <h3 className="text-sm font-semibold text-slate-700 mb-3">Year Interpolation</h3>
              <p className="text-sm text-slate-600 mb-3">
                PLANiT provides data at anchor years. Values for intermediate years are linearly interpolated.
              </p>
              <div className="bg-slate-50 rounded-lg p-4">
                <div className="flex items-center justify-between max-w-lg mx-auto">
                  {[2030, 2040, 2050, 2060].map((year, i) => (
                    <div key={year} className="flex items-center">
                      <div className="flex flex-col items-center">
                        <div className="w-4 h-4 rounded-full bg-indigo-500" />
                        <p className="text-xs font-mono text-slate-600 mt-1">{year}</p>
                      </div>
                      {i < 3 && (
                        <div className="w-12 md:w-20 h-0.5 bg-indigo-200 mx-1" />
                      )}
                    </div>
                  ))}
                </div>
                <p className="text-xs text-slate-400 text-center mt-3">
                  Linear interpolation between anchor years
                </p>
              </div>
            </div>

            {/* SSP Mapping */}
            <div>
              <h3 className="text-sm font-semibold text-slate-700 mb-3">SSP Mapping</h3>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b-2 border-slate-200">
                      <th className="p-2 text-left">CRP Scenario</th>
                      <th className="p-2 text-left">SSP Pathway</th>
                      <th className="p-2 text-center">Year</th>
                      <th className="p-2 text-left">Description</th>
                    </tr>
                  </thead>
                  <tbody>
                    {SSP_MAP.map((m) => (
                      <tr key={m.scenario} className="border-b border-slate-100">
                        <td className="p-2 font-mono text-xs">{m.scenario}</td>
                        <td className="p-2">
                          <span
                            className="px-2 py-0.5 rounded text-xs font-medium"
                            style={{
                              backgroundColor: m.ssp === "SSP1-2.6" ? "#dbeafe" : "#fee2e2",
                              color: m.ssp === "SSP1-2.6" ? "#2563eb" : "#dc2626",
                            }}
                          >
                            {m.ssp}
                          </span>
                        </td>
                        <td className="p-2 text-center font-mono">{m.year}</td>
                        <td className="p-2 text-slate-600 text-xs">{m.desc}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* ── Section 4: Transition Risk ── */}
      <div ref={refs.transition} className="bg-white rounded-lg shadow-sm p-6 mb-6">
        <button
          onClick={() => toggle("transition")}
          className="flex items-center justify-between w-full text-left"
        >
          <h2 className="text-lg font-semibold text-slate-800">
            4. Transition Risk
          </h2>
          <svg
            className={`w-5 h-5 text-slate-400 transition-transform ${open.transition ? "rotate-180" : ""}`}
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
          </svg>
        </button>
        {open.transition && (
          <div className="mt-4 space-y-6">
            {/* Dispatch Priority Penalty */}
            <div>
              <h3 className="text-sm font-semibold text-slate-700 mb-3">Dispatch Priority Penalty</h3>
              <p className="text-sm text-slate-600 mb-3">
                As Korea transitions away from coal, coal plants lose dispatch priority in the merit order.
                The capacity factor is reduced based on the declining coal share in the energy mix.
              </p>
              <EquationBlock
                label="Policy-Adjusted Capacity Factor"
                latex="CF_{policy}(t) = CF_{base} \times \frac{\text{Coal}_{share}(t)}{\text{Coal}_{share}(2024)} \times M_{grid}"
              />
              <EquationBlock
                label="Dispatch Priority Penalty (Enhanced)"
                latex="\text{penalty}(t) = \text{base\_penalty} \times \text{severity\_factor}"
              />
            </div>

            {/* Korea 11th Basic Plan */}
            <div>
              <h3 className="text-sm font-semibold text-slate-700 mb-3">Korea 11th Basic Plan Integration</h3>
              <p className="text-sm text-slate-600 mb-3">
                The enhanced scenarios incorporate the 11th Basic Plan (제11차 전력수급기본계획) which
                mandates coal phase-out by 2040. This creates an accelerated dispatch penalty trajectory.
              </p>
              <div className="bg-purple-50 border border-purple-200 rounded-lg p-4 text-sm text-purple-800">
                <strong>Enhanced 11th Plan scenario</strong> applies full 11th Plan dispatch penalties
                with severity scaling, resulting in capacity factors approaching zero near 2038-2040.
              </div>
            </div>

            {/* K-ETS Carbon Price */}
            <div>
              <h3 className="text-sm font-semibold text-slate-700 mb-3">K-ETS Carbon Price Trajectory</h3>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b-2 border-slate-200">
                      <th className="p-2 text-left">Year</th>
                      <th className="p-2 text-right">KRW/ton</th>
                      <th className="p-2 text-right">USD/ton</th>
                      <th className="p-2 text-left">Phase</th>
                    </tr>
                  </thead>
                  <tbody>
                    {[
                      { year: 2024, krw: "9,500", usd: "$7", phase: "Phase 1 (Market)" },
                      { year: 2025, krw: "11,000", usd: "$8", phase: "Phase 1" },
                      { year: 2030, krw: "30,000", usd: "$23", phase: "Phase 2 (NDC)" },
                      { year: 2038, krw: "58,000", usd: "$45", phase: "Phase 3 (Climate)" },
                      { year: 2050, krw: "150,000", usd: "$115", phase: "Phase 4 (Net-Zero)" },
                    ].map((r) => (
                      <tr key={r.year} className="border-b border-slate-100">
                        <td className="p-2 font-mono">{r.year}</td>
                        <td className="p-2 text-right font-mono">{r.krw}</td>
                        <td className="p-2 text-right font-mono">{r.usd}</td>
                        <td className="p-2 text-slate-600">{r.phase}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              <EquationBlock
                label="Carbon Cost"
                latex="C_{carbon}(t) = \text{Generation}(t) \times EF \times P_{carbon}(t)"
              />
            </div>
          </div>
        )}
      </div>

      {/* ── Section 5: Cashflow Computation ── */}
      <div ref={refs.cashflow} className="bg-white rounded-lg shadow-sm p-6 mb-6">
        <button
          onClick={() => toggle("cashflow")}
          className="flex items-center justify-between w-full text-left"
        >
          <h2 className="text-lg font-semibold text-slate-800">
            5. Cashflow Computation
          </h2>
          <svg
            className={`w-5 h-5 text-slate-400 transition-transform ${open.cashflow ? "rotate-180" : ""}`}
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
          </svg>
        </button>
        {open.cashflow && (
          <div className="mt-4 space-y-6">
            {/* Revenue */}
            <div>
              <h3 className="text-sm font-semibold text-slate-700 mb-3">Revenue Calculation</h3>
              <EquationBlock
                label="Annual Revenue"
                latex="\text{Revenue} = \text{Capacity} \times CF_{eff} \times 8{,}760\text{h} \times P_{electricity}"
              />
            </div>

            {/* Cost Structure */}
            <div>
              <h3 className="text-sm font-semibold text-slate-700 mb-3">Cost Structure</h3>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b-2 border-slate-200">
                      <th className="p-2 text-left">Component</th>
                      <th className="p-2 text-left">Formula / Value</th>
                      <th className="p-2 text-left">Notes</th>
                    </tr>
                  </thead>
                  <tbody>
                    {[
                      { comp: "Fuel Cost", formula: "Generation × Heat Rate × Fuel Price", note: "8.8 GJ/MWh × $2.5/GJ" },
                      { comp: "Fixed O&M", formula: "$15/kW-yr", note: "Capacity-based, fixed" },
                      { comp: "Variable O&M", formula: "$3.5/MWh", note: "Generation-based" },
                      { comp: "Carbon Cost", formula: "Generation × EF × Carbon Price", note: "0.82 tCO₂/MWh × K-ETS price" },
                      { comp: "Insurance", formula: "0.5% of CAPEX", note: "Annual premium" },
                    ].map((c) => (
                      <tr key={c.comp} className="border-b border-slate-100">
                        <td className="p-2 font-medium">{c.comp}</td>
                        <td className="p-2 text-slate-600 font-mono text-xs">{c.formula}</td>
                        <td className="p-2 text-slate-500 text-xs">{c.note}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>

            {/* EBITDA → FCF Waterfall */}
            <div>
              <h3 className="text-sm font-semibold text-slate-700 mb-3">EBITDA → FCF Waterfall</h3>
              <div className="bg-slate-50 rounded-lg p-4">
                <div className="flex flex-col gap-2 max-w-md mx-auto">
                  {[
                    { label: "Revenue", color: "#10b981", sign: "" },
                    { label: "− Fuel Cost", color: "#ef4444", sign: "−" },
                    { label: "− O&M (Fixed + Variable)", color: "#ef4444", sign: "−" },
                    { label: "− Carbon Cost", color: "#ef4444", sign: "−" },
                    { label: "= EBITDA", color: "#3b82f6", sign: "=" },
                    { label: "− Depreciation", color: "#f59e0b", sign: "−" },
                    { label: "− Interest Expense", color: "#f59e0b", sign: "−" },
                    { label: "− Tax", color: "#f59e0b", sign: "−" },
                    { label: "= Free Cash Flow", color: "#8b5cf6", sign: "=" },
                  ].map((item) => (
                    <div
                      key={item.label}
                      className="rounded px-4 py-2 text-sm font-medium text-white"
                      style={{ backgroundColor: item.color }}
                    >
                      {item.label}
                    </div>
                  ))}
                </div>
              </div>
            </div>

            {/* Key Metrics */}
            <div>
              <h3 className="text-sm font-semibold text-slate-700 mb-3">Key Financial Metrics</h3>
              <EquationBlock
                label="Net Present Value"
                latex="NPV = \sum_{t=1}^{T} \frac{FCF_t}{(1+r)^t} - \text{CAPEX}"
              />
              <EquationBlock
                label="Internal Rate of Return"
                latex="\sum_{t=0}^{T} \frac{FCF_t}{(1+IRR)^t} = 0"
              />
              <EquationBlock
                label="Debt Service Coverage Ratio"
                latex="DSCR = \frac{EBITDA}{\text{Debt Service}} = \frac{EBITDA}{\text{Interest} + \text{Principal}}"
              />
            </div>
          </div>
        )}
      </div>

      {/* ── Section 6: Credit Rating & CRP ── */}
      <div ref={refs.credit} className="bg-white rounded-lg shadow-sm p-6 mb-6">
        <button
          onClick={() => toggle("credit")}
          className="flex items-center justify-between w-full text-left"
        >
          <h2 className="text-lg font-semibold text-slate-800">
            6. Credit Rating & Climate Risk Premium
          </h2>
          <svg
            className={`w-5 h-5 text-slate-400 transition-transform ${open.credit ? "rotate-180" : ""}`}
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
          </svg>
        </button>
        {open.credit && (
          <div className="mt-4 space-y-6">
            {/* KIS Methodology */}
            <div>
              <h3 className="text-sm font-semibold text-slate-700 mb-3">KIS Rating Methodology — 6 Assessment Criteria</h3>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b-2 border-slate-200">
                      <th className="p-2 text-left">Criterion</th>
                      <th className="p-2 text-center">Weight</th>
                      <th className="p-2 text-left">Description</th>
                    </tr>
                  </thead>
                  <tbody>
                    {KIS_CRITERIA.map((c) => (
                      <tr key={c.name} className="border-b border-slate-100">
                        <td className="p-2 font-medium">{c.name}</td>
                        <td className="p-2 text-center font-mono">{c.weight}</td>
                        <td className="p-2 text-slate-600 text-xs">{c.desc}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>

            {/* Rating Scale + Spread */}
            <div>
              <h3 className="text-sm font-semibold text-slate-700 mb-3">Rating Scale & Spread Mapping</h3>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b-2 border-slate-200">
                      <th className="p-2 text-left">Rating</th>
                      <th className="p-2 text-right">Spread (bps)</th>
                      <th className="p-2 text-left">Grade</th>
                      <th className="p-2 text-left">Visual</th>
                    </tr>
                  </thead>
                  <tbody>
                    {Object.entries(RATING_SPREADS).map(([rating, spread]) => (
                      <tr key={rating} className="border-b border-slate-100">
                        <td className="p-2 font-mono font-bold">{rating}</td>
                        <td className="p-2 text-right font-mono">{spread}</td>
                        <td className="p-2">
                          <span
                            className="px-2 py-0.5 rounded text-xs font-medium"
                            style={{
                              backgroundColor: ["AAA", "AA", "A", "BBB"].includes(rating)
                                ? "#dcfce7"
                                : "#fee2e2",
                              color: ["AAA", "AA", "A", "BBB"].includes(rating)
                                ? "#16a34a"
                                : "#dc2626",
                            }}
                          >
                            {["AAA", "AA", "A", "BBB"].includes(rating) ? "Investment" : "Speculative"}
                          </span>
                        </td>
                        <td className="p-2">
                          <div
                            className="h-3 rounded"
                            style={{
                              width: `${Math.min((spread / 50) * 10, 100)}%`,
                              backgroundColor: RATING_COLORS[rating],
                              minWidth: "8px",
                            }}
                          />
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>

            {/* Counterfactual Approach */}
            <div>
              <h3 className="text-sm font-semibold text-slate-700 mb-3">Counterfactual CRP Approach</h3>
              <p className="text-sm text-slate-600 mb-3">
                The production model computes CRP from the WACC gap between scenario and counterfactual
                (A-rated no-climate-risk reference).
              </p>
              <EquationBlock
                label="Climate Risk Premium"
                latex="CRP_{bps} = \left(WACC_{scenario} - WACC_{counterfactual}\right)\times 10^4"
              />
              <div className="bg-slate-50 rounded-lg p-4 mt-3">
                <div className="flex items-center gap-4 justify-center flex-wrap">
                  <div className="text-center">
                    <div className="text-xs text-slate-500 mb-1">Scenario Rating</div>
                    <div className="bg-white rounded-lg px-4 py-2 shadow-sm text-sm font-semibold">
                      e.g., CC (1500 bps)
                    </div>
                  </div>
                  <span className="text-xl text-slate-400">−</span>
                  <div className="text-center">
                    <div className="text-xs text-slate-500 mb-1">Counterfactual</div>
                    <div className="bg-white rounded-lg px-4 py-2 shadow-sm text-sm font-semibold">
                      A (150 bps)
                    </div>
                  </div>
                  <span className="text-xl text-slate-400">=</span>
                  <div className="text-center">
                    <div className="text-xs text-slate-500 mb-1">CRP</div>
                    <div className="bg-amber-50 border border-amber-200 rounded-lg px-4 py-2 text-sm font-bold text-amber-700">
                      1350 bps
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* Shapley Decomposition */}
            <div>
              <h3 className="text-sm font-semibold text-slate-700 mb-3">Shapley Value Decomposition</h3>
              <p className="text-sm text-slate-600">
                For combined scenarios, the CRP is decomposed into physical and transition risk contributions
                using Shapley values. This ensures fair attribution: each risk factor&apos;s marginal contribution
                is averaged over all possible orderings of factor inclusion.
              </p>
              <EquationBlock
                label="Shapley Attribution"
                latex="\phi_i = \sum_{S \subseteq N \setminus \{i\}} \frac{|S|!(|N|-|S|-1)!}{|N|!} \left[ v(S \cup \{i\}) - v(S) \right]"
              />
            </div>
          </div>
        )}
      </div>
    </>
  );
}
