"use client";

import EquationBlock from "@/components/methodology/EquationBlock";
import { PLANT } from "@/lib/generated/data";

const INPUT_TABLE = [
  { group: "Plant", item: "Capacity", value: `${PLANT.capacity_mw.toLocaleString()} MW`, source: "data/raw/plant_parameters.csv" },
  { group: "Plant", item: "Base CF", value: PLANT.capacity_factor.toFixed(2), source: "data/raw/plant_parameters.csv" },
  { group: "Plant", item: "CAPEX", value: `${PLANT.total_capex_million.toLocaleString()}M USD`, source: "data/raw/plant_parameters.csv" },
  { group: "Transition", item: "Policy scenarios", value: "baseline/moderate/aggressive", source: "data/raw/policy.csv" },
  { group: "Transition", item: "Enhanced plan", value: "11th plan trajectory", source: "data/raw/enhanced_korea_power_plan.csv" },
  { group: "Physical", item: "Hazard baselines (7 hazards)", value: "freq, outage, derate, eff_loss, damage_ratio", source: "data/physical/hazard_baselines.csv" },
  { group: "Physical", item: "Climate factors", value: "5 scenarios × 4 anchor years", source: "data/physical/climate_factors.csv" },
  { group: "Physical", item: "Transmission line params", value: "30km line, 345kV, $2M/km, fragility", source: "data/raw/transmission.csv" },
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
          <pre>{`Inputs (Plant + Transmission + Policy + PLANiT/CLIMADA hazards)
    ↓
Transition Adjustments (capacity_factor, operating_years, carbon price)
Physical Adjustments (6 channels):
  • plant_outage         (wildfire + tropical cyclone)
  • capacity_derate      (drought reduces cooling water)
  • efficiency_loss      (drought + heat stress raise heat rate)
  • transmission_outage  (line damage from wildfire/typhoon/heat + substation flood)
  • asset_capex_loss     (annual fraction of plant + line replacement value destroyed)
  • combined_unavail     = 1 − (1 − plant)(1 − line)
    ↓
Cashflow Engine (Revenue, EBITDA, FCF, with capex destruction)
    ↓
Financial Metrics (NPV, IRR, DSCR, LLCR)
    ↓
Credit Rating (AAA~D) + Spread Mapping
    ↓
Counterfactual Financing Impact (CRP in bps)`}</pre>
        </div>
      </div>

      <div className="bg-white rounded-lg shadow-sm p-6 mb-6">
        <h2 className="text-lg font-semibold text-slate-800 mb-4">Physical Risk Channels</h2>
        <p className="text-xs text-slate-600 mb-4">
          The pipeline composes six independent hazard channels per scenario × year. All
          values come from <code className="bg-slate-100 px-1 rounded">data/physical/hazard_baselines.csv</code>{" "}
          × <code className="bg-slate-100 px-1 rounded">climate_factors.csv</code>{" "}
          (and <code className="bg-slate-100 px-1 rounded">data/raw/transmission.csv</code> for grid).
        </p>
        <EquationBlock
          label="1. Plant outage (wildfire + tropical cyclone direct hits)"
          latex="\text{plant\_outage} = f_{\text{wf}}\,p_{\text{wf}}\frac{h_{\text{wf}}}{8760} + r_{\text{TC}}^{\text{base}}\,c_{\text{TC}}"
        />
        <EquationBlock
          label="2. Capacity derate (drought reduces cooling water availability)"
          latex="\text{capacity\_derate} = d_{\text{drought}}^{\text{base}} \times c_{\text{drought}}(y)"
        />
        <EquationBlock
          label="3. Efficiency loss (drought + heat stress raise heat rate)"
          latex="\text{eff\_loss} = e_{\text{dr}}^{\text{base}}c_{\text{dr}}(y) + e_{\text{hs}}^{\text{base}}c_{\text{hs}}(y)"
        />
        <EquationBlock
          label="4. Transmission outage (line + substation, composes with plant outage)"
          latex="\text{line\_outage} = \sum_{h\in\{wf,tc,heat\}} f_h p_h^{\text{line}} \frac{h_h^{\text{line}}}{8760} + f_{\text{flood}} p_{\text{sub}}\frac{h_{\text{sub}}}{8760}"
        />
        <EquationBlock
          label="5. Combined unavailability (plant + line independent failure)"
          latex="\text{outage} = 1 - (1-\text{plant\_outage})(1-\text{line\_outage})"
        />
        <EquationBlock
          label="6. Asset capex loss (annual replacement-value destruction)"
          latex="\text{capex\_loss\_rate} = \sum_h \text{damage}_h\,f_h\,c_h(y) + L^{\text{line}}_{\text{annual}}\,c_{\text{wf}}(y)"
        />
        <p className="text-xs text-slate-500 mt-3">
          Where <em>f<sub>h</sub></em> is hazard frequency, <em>p<sub>h</sub></em> is conditional
          outage probability, <em>h<sub>h</sub></em> is mean outage duration, and{" "}
          <em>c<sub>h</sub>(y)</em> is the scenario-specific climate factor in year y. Annual
          interpolation is linear between IPCC anchor years (2024/2030/2050/2100).
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
