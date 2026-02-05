"use client";

import EquationBlock from "@/components/methodology/EquationBlock";

const LITERATURE = [
  { id: 1, authors: "Kim et al.", year: 2025, title: "Natural Hazards", doi: "10.1007/s11069-025-07169-4", finding: "451 fires/yr in Korea; Gangwon high-risk zone" },
  { id: 2, authors: "Kang & Lee", year: 2024, title: "Water", doi: "10.3390/w16202987", finding: "Coastal flood modeling for Korea; 2050/2100 projections" },
  { id: 3, authors: "Van Vliet et al.", year: 2016, title: "Nature Climate Change", doi: "10.1038/nclimate2903", finding: "61–74% plants face capacity loss by 2040–2069" },
  { id: 4, authors: "Lee et al.", year: 2025, title: "Scientific Reports", doi: "10.1038/s41598-025-15508-5", finding: "Year-round wildfire prediction for Gangwon" },
  { id: 5, authors: "Zscheischler et al.", year: 2018, title: "Nature Climate Change", doi: "10.1038/s41558-018-0156-3", finding: "Compound events are non-additive" },
  { id: 6, authors: "Bressan et al.", year: 2024, title: "Nature Communications", doi: "10.1038/s41467-024-48820-1", finding: "Asset-level climate physical risk assessment" },
  { id: 7, authors: "Bierkandt et al.", year: 2015, title: "Environ. Res. Lett.", doi: "10.1088/1748-9326/10/12/124022", finding: "US power plant sites at risk from SLR" },
  { id: 8, authors: "IPCC", year: 2021, title: "AR6 WGI Chapter 9", doi: "ipcc.ch", finding: "Ocean, cryosphere, and sea level change" },
  { id: 9, authors: "World Weather Attribution", year: 2025, title: "Korean Wildfire Attribution", doi: "worldweatherattribution.org", finding: "Korean wildfires 2x more likely from climate change" },
  { id: 10, authors: "FEMA", year: 2025, title: "HAZUS Technical Manual", doi: "fema.gov", finding: "Flood risk modeling methodology" },
];

export default function MethodologyPage() {
  return (
    <>
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-slate-900">Methodology & Verification</h1>
        <p className="text-sm text-slate-500 mt-1">
          Model equations, parameter sources, and literature references
        </p>
      </div>

      {/* Model Architecture */}
      <div className="bg-white rounded-lg shadow-sm p-6 mb-6">
        <h2 className="text-lg font-semibold text-slate-800 mb-4">Model Architecture</h2>
        <div className="bg-slate-50 rounded-lg p-4 font-mono text-xs leading-6 overflow-x-auto">
          <pre>{`CLIMATE SCENARIOS
  │
  ├── PHYSICAL RISK PATH
  │     ├── WILDFIRE    → Outage Rate
  │     ├── FLOOD       → Outage Rate
  │     └── SEA LEVEL   → Derate Rate
  │           ↓
  │     COMPOUND RISK (ρ=0.3, max 1.25x)
  │
  └── TRANSITION RISK PATH
        ├── POLICY      → Dispatch Factor (CF reduction)
        └── CARBON      → K-ETS Cost ($/MWh)
              ↓
        CARBON COST + REVENUE LOSS
              ↓
COMBINED IMPACT → Effective CF → Revenue → EBITDA → DSCR
              ↓
CREDIT RATING → Spread → Climate Risk Premium (CRP)`}</pre>
        </div>
      </div>

      {/* Key Equations */}
      <div className="bg-white rounded-lg shadow-sm p-6 mb-6">
        <h2 className="text-lg font-semibold text-slate-800 mb-4">Key Equations</h2>

        <EquationBlock
          label="Wildfire Outage Rate"
          latex="R_{wild} = \frac{N_{fires} \times I_{impact} \times T_{outage}}{8760} \times M_{climate}(t)"
        />

        <EquationBlock
          label="Flood Outage Rate"
          latex="R_{flood} = P_{surge} \times I_{impact} \times \frac{T_{outage}}{8760} \times M_{climate}(t)"
        />

        <EquationBlock
          label="Sea Level Rise Derate"
          latex="D_{SLR} \approx SLR_{meters} \times 0.0022"
        />

        <EquationBlock
          label="Compound Risk Multiplier"
          latex="M_{compound} = 1 + \left(\rho \times \frac{R_{wild} + R_{flood} + D_{SLR}}{0.01}\right), \quad \rho = 0.3, \quad M \leq 1.25"
        />

        <EquationBlock
          label="Effective Capacity Factor"
          latex="CF_{eff} = CF_{base} \times (1 - R_{outage}) \times (1 - D_{capacity}) \times (1 - D_{efficiency})"
        />

        <div className="mt-6 mb-2 text-sm font-medium text-slate-700">Transition Risk</div>

        <EquationBlock
          label="Carbon Cost"
          latex="C_{carbon} = E \times EF \times P_{carbon}"
        />

        <EquationBlock
          label="Policy Capacity Factor"
          latex="CF_{policy} = CF_{base} \times \frac{Coal_{share}(t)}{Coal_{share}(2024)} \times M_{grid}"
        />

        <EquationBlock
          label="Transition Revenue Impact"
          latex="\Delta Rev = (CF_{base} - CF_{policy}) \times Cap \times 8760 \times P_{elec} + C_{carbon}"
        />

        <EquationBlock
          label="Debt Service Coverage Ratio"
          latex="DSCR = \frac{EBITDA}{Debt\ Service} = \frac{Revenue - OPEX - Fuel}{Interest + Principal}"
        />

        <EquationBlock
          label="Climate Risk Premium"
          latex="CRP = Spread_{scenario} - Spread_{counterfactual}"
        />
      </div>

      {/* Parameter Sources */}
      <div className="bg-white rounded-lg shadow-sm p-6 mb-6">
        <h2 className="text-lg font-semibold text-slate-800 mb-4">
          Parameter Sources
        </h2>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b-2 border-slate-200">
                <th className="p-3 text-left">Parameter</th>
                <th className="p-3 text-right">Value</th>
                <th className="p-3 text-left">Type</th>
                <th className="p-3 text-left">Source</th>
              </tr>
            </thead>
            <tbody>
              {[
                { param: "Wildfire base rate", value: "0.055%", type: "DERIVED", source: "Kim et al. (2025)" },
                { param: "Flood base rate", value: "0.003%", type: "DERIVED", source: "Kang & Lee (2024)" },
                { param: "SLR derate", value: "0.22%/m", type: "DERIVED", source: "Van Vliet et al. (2016)" },
                { param: "Compound multiplier", value: "1.0–1.25x", type: "CONSERVATIVE", source: "Zscheischler et al. (2018)" },
                { param: "Climate multipliers", value: "1.0–4.0x", type: "QUOTED", source: "IPCC AR6 Table 9.9" },
                { param: "Capacity", value: "2,100 MW", type: "ACTUAL", source: "Samcheok plant specs" },
                { param: "CAPEX", value: "$4,900M", type: "ACTUAL", source: "Samcheok plant specs" },
                { param: "Capacity Factor", value: "0.85", type: "ACTUAL", source: "Baseload assumption" },
              ].map((p) => (
                <tr key={p.param} className="border-b border-slate-100">
                  <td className="p-3">{p.param}</td>
                  <td className="p-3 text-right font-mono">{p.value}</td>
                  <td className="p-3">
                    <span
                      className={`px-2 py-0.5 rounded text-xs font-medium ${
                        p.type === "QUOTED"
                          ? "bg-green-100 text-green-700"
                          : p.type === "DERIVED"
                          ? "bg-blue-100 text-blue-700"
                          : p.type === "CONSERVATIVE"
                          ? "bg-yellow-100 text-yellow-700"
                          : "bg-slate-100 text-slate-700"
                      }`}
                    >
                      {p.type}
                    </span>
                  </td>
                  <td className="p-3 text-sm text-slate-600">{p.source}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Transition Risk Parameters */}
      <div className="bg-white rounded-lg shadow-sm p-6 mb-6">
        <h2 className="text-lg font-semibold text-slate-800 mb-4">
          Transition Risk Parameters
        </h2>
        <p className="text-sm text-slate-600 mb-4">
          Based on Korea 11th Basic Plan (제11차 전력수급기본계획, 2024-2038) and presidential
          pledge for coal phase-out by 2040.
        </p>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b-2 border-slate-200">
                <th className="p-3 text-left">Parameter</th>
                <th className="p-3 text-right">Value</th>
                <th className="p-3 text-left">Type</th>
                <th className="p-3 text-left">Source</th>
              </tr>
            </thead>
            <tbody>
              {[
                { param: "Coal phase-out year", value: "2040", type: "POLICY", source: "Presidential pledge (2040년 탈석탄)" },
                { param: "Initial coal capacity", value: "26.7 GW", type: "ACTUAL", source: "11th Basic Plan (2024)" },
                { param: "Annual reduction", value: "1.78 GW/yr", type: "DERIVED", source: "Linear phase-out" },
                { param: "K-ETS 2024 price", value: "~$7/ton", type: "ACTUAL", source: "KRX (9,465 KRW)" },
                { param: "K-ETS 2030 target", value: "~$23/ton", type: "POLICY", source: "NDC (30,000 KRW)" },
                { param: "K-ETS 2038 target", value: "~$45/ton", type: "POLICY", source: "Projection (58,000 KRW)" },
                { param: "Emission factor", value: "0.82 tCO2/MWh", type: "QUOTED", source: "IPCC (8.8 × 0.093)" },
                { param: "Carbon-free 2038", value: "73.2%", type: "DERIVED", source: "11th Plan (nuclear + renewable + H₂)" },
              ].map((p) => (
                <tr key={p.param} className="border-b border-slate-100">
                  <td className="p-3">{p.param}</td>
                  <td className="p-3 text-right font-mono">{p.value}</td>
                  <td className="p-3">
                    <span
                      className={`px-2 py-0.5 rounded text-xs font-medium ${
                        p.type === "QUOTED"
                          ? "bg-green-100 text-green-700"
                          : p.type === "DERIVED"
                          ? "bg-blue-100 text-blue-700"
                          : p.type === "POLICY"
                          ? "bg-purple-100 text-purple-700"
                          : "bg-slate-100 text-slate-700"
                      }`}
                    >
                      {p.type}
                    </span>
                  </td>
                  <td className="p-3 text-sm text-slate-600">{p.source}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* K-ETS Carbon Price Trajectory */}
      <div className="bg-white rounded-lg shadow-sm p-6 mb-6">
        <h2 className="text-lg font-semibold text-slate-800 mb-4">
          K-ETS Carbon Price Trajectory
        </h2>
        <div className="bg-slate-50 rounded-lg p-4 font-mono text-xs leading-6 overflow-x-auto">
          <pre>{`Year    KRW/ton     USD/ton   Phase
─────────────────────────────────────
2024     9,500        $7      Phase 1 (Market)
2025    11,000        $8      Phase 1
2030    30,000       $23      Phase 2 (NDC)
2038    58,000       $45      Phase 3 (Climate)
2050   150,000      $115      Phase 4 (Net-Zero)`}</pre>
        </div>
        <p className="text-xs text-slate-500 mt-2">
          Exchange rate: 1,300 KRW/USD. 2024 price validated against KRX 배출권시장 data.
        </p>
      </div>

      {/* Literature References */}
      <div className="bg-white rounded-lg shadow-sm p-6">
        <h2 className="text-lg font-semibold text-slate-800 mb-4">
          Verified Literature References
        </h2>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b-2 border-slate-200">
                <th className="p-3 text-left w-8">#</th>
                <th className="p-3 text-left">Authors</th>
                <th className="p-3 text-center">Year</th>
                <th className="p-3 text-left">Journal</th>
                <th className="p-3 text-left">Key Finding</th>
                <th className="p-3 text-center">DOI</th>
              </tr>
            </thead>
            <tbody>
              {LITERATURE.map((ref) => (
                <tr key={ref.id} className="border-b border-slate-100">
                  <td className="p-3 text-slate-400">{ref.id}</td>
                  <td className="p-3 font-medium">{ref.authors}</td>
                  <td className="p-3 text-center">{ref.year}</td>
                  <td className="p-3 text-slate-600">{ref.title}</td>
                  <td className="p-3 text-xs text-slate-500">{ref.finding}</td>
                  <td className="p-3 text-center">
                    <a
                      href={
                        ref.doi.includes(".")
                          ? ref.doi.startsWith("http")
                            ? ref.doi
                            : `https://doi.org/${ref.doi}`
                          : `https://${ref.doi}`
                      }
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-teal-600 hover:underline text-xs"
                    >
                      Link
                    </a>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </>
  );
}
