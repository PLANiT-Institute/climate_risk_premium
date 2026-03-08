"use client";

import EquationBlock from "@/components/methodology/EquationBlock";

const INPUT_TABLE = [
  { group: "Plant", item: "Capacity", value: "2,100 MW", source: "data/raw/plant_parameters.csv" },
  { group: "Plant", item: "Base CF", value: "0.85", source: "data/raw/plant_parameters.csv" },
  { group: "Plant", item: "CAPEX", value: "4,900M USD", source: "data/raw/plant_parameters.csv" },
  { group: "Transition", item: "Policy scenarios", value: "baseline/moderate/aggressive", source: "data/raw/policy.csv" },
  { group: "Transition", item: "Enhanced plan", value: "11th plan trajectory", source: "data/raw/enhanced_korea_power_plan.csv" },
  { group: "Physical", item: "Wildfire AAI", value: "CLIMADA output", source: "Physicalrisk_PLANiT/data/results/*.csv" },
  { group: "Physical", item: "Drought impact_mean", value: "PhysRisk output", source: "Physicalrisk_PLANiT/data/results/*.csv" },
  { group: "Physical", item: "Water impact_mean", value: "PhysRisk output", source: "Physicalrisk_PLANiT/data/results/*.csv" },
];

export default function MethodologyPage() {
  return (
    <>
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-slate-900">Methodology</h1>
        <p className="text-sm text-slate-500 mt-1">
          Production equations and data lineage used by the current CRP pipeline
        </p>
      </div>

      <div className="bg-white rounded-lg shadow-sm p-6 mb-6">
        <h2 className="text-lg font-semibold text-slate-800 mb-3">Current Pipeline Scope</h2>
        <div className="bg-slate-50 rounded-lg p-4 font-mono text-xs leading-6 overflow-x-auto">
          <pre>{`Inputs (Plant + Policy + PLANiT hazards)
    ↓
Transition Adjustments (capacity_factor, operating_years)
Physical Adjustments (outage_rate, capacity_derate, water_cap)
    ↓
Cashflow Engine (Revenue, EBITDA, FCF)
    ↓
Financial Metrics (NPV, IRR, DSCR, LLCR)
    ↓
Credit Rating (AAA~D) + Spread Mapping
    ↓
Counterfactual Financing Impact (CRP in bps)`}</pre>
        </div>
      </div>

      <div className="bg-white rounded-lg shadow-sm p-6 mb-6">
        <h2 className="text-lg font-semibold text-slate-800 mb-4">Physical Risk Conversion Equations</h2>
        <EquationBlock
          label="Wildfire (CLIMADA AAI → outage_rate)"
          latex="\text{outage\_rate} = \frac{AAI_{KRW}}{\text{total\_asset\_value}_{KRW}}"
        />
        <EquationBlock
          label="Drought (PhysRisk impact_mean → derate)"
          latex="\text{capacity\_derate} = \text{impact\_mean} \times \text{drought\_severity\_scale}"
        />
        <EquationBlock
          label="Water Risk (PhysRisk impact_mean → hard cap)"
          latex="\text{water\_constrained\_capacity} = \max(0,\;1-\text{impact\_mean})"
        />
        <p className="text-xs text-slate-500 mt-3">
          Note: interpolation between anchor years is linear; pre-anchor years blend from baseline.
        </p>
      </div>

      <div className="bg-white rounded-lg shadow-sm p-6 mb-6">
        <h2 className="text-lg font-semibold text-slate-800 mb-4">Operational & Financial Equations</h2>
        <EquationBlock
          label="Generation"
          latex="\text{actual\_mwh} = (capacity\times8760\times cf)\times(1-\text{outage\_rate})"
        />
        <EquationBlock
          label="Revenue"
          latex="\text{revenue} = \text{actual\_mwh}\times \text{power\_price}"
        />
        <EquationBlock
          label="Fuel cost with efficiency penalty"
          latex="\text{fuel\_cost} = \text{actual\_mwh}\times \text{heat\_rate}\times(1+\text{efficiency\_loss})\times\text{fuel\_price}"
        />
        <EquationBlock
          label="Free cash flow"
          latex="FCF = NOPAT + Depreciation - Capex"
        />
        <EquationBlock
          label="NPV"
          latex="NPV = \sum_{t=1}^{T} \frac{FCF_t}{(1+r)^t} - CAPEX_0"
        />
      </div>

      <div className="bg-white rounded-lg shadow-sm p-6 mb-6">
        <h2 className="text-lg font-semibold text-slate-800 mb-4">Credit & CRP Equations</h2>
        <EquationBlock
          label="Rating spread mapping"
          latex="r_d = r_f + \frac{\text{spread(rating)}}{10000}"
        />
        <EquationBlock
          label="Counterfactual CRP"
          latex="CRP_{bps}=\left(WACC_{scenario}-WACC_{counterfactual}\right)\times10000"
        />
        <p className="text-xs text-slate-500 mt-3">
          Counterfactual baseline is A-rated in the current code path.
        </p>
      </div>

      <div className="bg-white rounded-lg shadow-sm p-6 mb-6">
        <h2 className="text-lg font-semibold text-slate-800 mb-4">Input Lineage</h2>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b-2 border-slate-200">
                <th className="p-3 text-left">Group</th>
                <th className="p-3 text-left">Item</th>
                <th className="p-3 text-left">Value Type</th>
                <th className="p-3 text-left">Source</th>
              </tr>
            </thead>
            <tbody>
              {INPUT_TABLE.map((row) => (
                <tr key={`${row.group}-${row.item}`} className="border-b border-slate-100">
                  <td className="p-3">{row.group}</td>
                  <td className="p-3">{row.item}</td>
                  <td className="p-3 font-mono text-xs">{row.value}</td>
                  <td className="p-3 text-xs text-slate-600">{row.source}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      <div className="bg-amber-50 border border-amber-200 rounded-lg p-5">
        <h3 className="text-sm font-semibold text-amber-800 mb-2">Interpretation Guardrails</h3>
        <ul className="text-sm text-amber-900 space-y-1 list-disc pl-5">
          <li>Use `results/` CSV files as the authoritative project outputs.</li>
          <li>Dashboard visualizations are explanation-first views of those outputs.</li>
          <li>For full code-level process detail, refer to `docs/MODEL_PROCESS_FULL.md` in the repository.</li>
        </ul>
      </div>
    </>
  );
}
