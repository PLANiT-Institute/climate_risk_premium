/* Model pipeline / formulas */
function ScreenPipeline({ model }) {
  const [tab, setTab] = uS("inputs");
  const tabs = [
    ["inputs", "01 · Input Data"],
    ["transition", "02 · Transition Risk"],
    ["cashflow", "03 · Cashflow Model"],
    ["credit", "04 · Credit & CRP"],
  ];

  return (
    <div className="page" style={{ padding: 14 }}>
      <Panel title="Pipeline · Stages" body="tight">
        <div style={{ display: "flex", gap: 4 }}>
          {tabs.map(([k,l]) => (
            <button key={k} className={"btn sm " + (tab === k ? "primary" : "ghost")} onClick={() => setTab(k)}>{l}</button>
          ))}
        </div>
      </Panel>

      {tab === "inputs" && (
        <>
          <Panel title="Plant Parameters">
            <div className="grid-3">
              {[
                ["Plant", model.plant.name],
                ["Capacity", model.plant.capacity_mw + " MW"],
                ["Base CF", (model.plant.capacity_factor*100).toFixed(0) + "%"],
                ["Emissions", model.plant.emissions_tco2_per_mwh.toFixed(2) + " tCO₂/MWh"],
                ["CAPEX", "$" + (model.plant.total_capex_million/1000).toFixed(2) + "B"],
                ["Discount rate", (model.plant.discount_rate*100).toFixed(0) + "%"],
              ].map(([k,v]) => (
                <Stat key={k} label={k} value={v} />
              ))}
            </div>
          </Panel>
          <Panel title="Transition Scenario Definitions" body="flush">
            <table className="tbl">
              <thead><tr>
                <th>Scenario</th><th>Description</th>
                <th className="num">Dispatch</th><th className="num">Life</th>
                <th className="num">CP 2025</th><th className="num">CP 2030</th>
                <th className="num">CP 2040</th><th className="num">CP 2050</th>
              </tr></thead>
              <tbody>
                {model.transitions.map(t => (
                  <tr key={t.id}>
                    <td style={{ fontWeight: 600 }}>{t.name}</td>
                    <td className="muted">{t.desc}</td>
                    <td className="num">{(t.dispatch*100).toFixed(0)}%</td>
                    <td className="num">{t.retire}</td>
                    <td className="num">${t.cp[0]}</td>
                    <td className="num">${t.cp[1]}</td>
                    <td className="num">${t.cp[2]}</td>
                    <td className="num">${t.cp[3]}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </Panel>
        </>
      )}

      {tab === "transition" && (
        <>
          <Panel title="Capacity-Factor Adjustment">
            <Formula tex="CF_eff(t) = CF_base × (1 − dispatch_penalty) × (1 − physical_loss(t))" />
            <div style={{ color: "var(--tx-2)", fontSize: 12, marginTop: 8 }}>
              Dispatch penalty is fixed per transition scenario. Physical loss adds wildfire outage,
              transmission outage, and drought derate (multiplied independently for small values).
            </div>
          </Panel>
          <Panel title="K-ETS Carbon Price · Trajectory">
            <Formula tex="P_carbon(t) = linear_interp(P_2025, P_2030, P_2040, P_2050)" />
            <Formula tex="C_carbon(t) = MWh(t) × emission_factor × P_carbon(t)" />
            <div style={{ marginTop: 12 }}>
              <LineChart
                data={Array.from({length: 26}, (_, i) => {
                  const y = 2025 + i;
                  const row = { x: y };
                  model.transitions.forEach(t => row[t.id] = carbonPrice(t.cp, y));
                  return row;
                })}
                series={model.transitions.map(t => ({ key: t.id, label: t.name, color: scenarioColor(t.id === "baseline" ? "conservative" : t.id) || "#94a3b8" }))}
                height={280}
                yFormat={v => "$" + v.toFixed(0) + "/t"} xFormat={v => v.toString()}
                xMin={2025} xMax={2050}
              />
            </div>
          </Panel>
        </>
      )}

      {tab === "cashflow" && (
        <>
          <Panel title="Revenue">
            <Formula tex="Revenue(t) = Capacity_MW × CF_eff(t) × 8760 × P_electricity" />
          </Panel>
          <Panel title="Cost Components" body="flush">
            <table className="tbl">
              <thead><tr><th>Component</th><th>Formula</th></tr></thead>
              <tbody>
                <tr><td>Fuel</td><td className="mono">MWh × heat_rate × fuel_price</td></tr>
                <tr><td>Fixed O&M</td><td className="mono">capacity_kW × $35 / kW-yr</td></tr>
                <tr><td>Variable O&M</td><td className="mono">MWh × $4.5 / MWh</td></tr>
                <tr><td>Carbon (K-ETS)</td><td className="mono">MWh × emission_factor × P_carbon(t)</td></tr>
              </tbody>
            </table>
          </Panel>
          <Panel title="EBITDA → Free Cash Flow → NPV">
            <Formula tex="EBITDA = Revenue − Fuel − O&M_fixed − O&M_var − C_carbon" />
            <Formula tex="FCF = EBIT × (1 − τ) + Depreciation" />
            <Formula tex="DSCR = CFADS / Debt_Service" />
            <Formula tex="NPV = Σ FCF_t / (1 + r)^t  −  CAPEX" />
          </Panel>
        </>
      )}

      {tab === "credit" && (
        <>
          <Panel title="KIS Rating · Methodology" body="flush">
            <table className="tbl">
              <thead><tr><th>Criterion</th><th className="num">Weight</th><th>Key metric</th></tr></thead>
              <tbody>
                <tr><td>Capacity / scale</td><td className="num">15%</td><td className="mono">capacity_mw → AAA at 2,100 MW</td></tr>
                <tr><td>Profitability</td><td className="num">10%</td><td className="mono">EBITDA / fixed_assets</td></tr>
                <tr><td>Coverage</td><td className="num">12%</td><td className="mono">EBITDA / interest_expense</td></tr>
                <tr><td>DSCR</td><td className="num">28%</td><td className="mono">CFADS / debt_service</td></tr>
                <tr><td>Net debt leverage</td><td className="num">15%</td><td className="mono">net_debt / EBITDA</td></tr>
                <tr><td>Equity leverage</td><td className="num">20%</td><td className="mono">debt / equity</td></tr>
              </tbody>
            </table>
          </Panel>
          <Panel title="Climate Risk Premium">
            <Formula tex="CRP_bps = (WACC_scenario − WACC_counterfactual) × 10⁴" />
            <Formula tex="WACC = d × k_d(rating) + e × k_e(notch_premium)" />
            <div style={{ marginTop: 8, color: "var(--tx-2)", fontSize: 12 }}>
              Counterfactual = A-rated entity (no climate risk). Each notch downgrade adds ~0.5% equity premium and re-prices the debt spread.
            </div>
          </Panel>
          <Panel title="Rating → Spread Mapping" body="flush">
            <table className="tbl">
              <thead><tr><th>Rating</th><th className="num">Spread (bps)</th><th>Grade</th></tr></thead>
              <tbody>
                {Object.entries(RATING_SPREADS).map(([r, s]) => (
                  <tr key={r}>
                    <td><Rating value={r} /></td>
                    <td className="num">{s}</td>
                    <td className="muted">{["AAA","AA","A","BBB"].includes(r) ? "Investment" : "Speculative / Default"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </Panel>
        </>
      )}
    </div>
  );
}
function Formula({ tex }) {
  return (
    <div style={{ background: "var(--bg-inset)", border: "1px solid var(--line-2)", padding: "10px 14px", borderRadius: 4, fontFamily: "var(--font-mono)", fontSize: 13, color: "var(--tx-1)", marginBottom: 6 }}>
      {tex}
    </div>
  );
}
function Stat({ label, value }) {
  return (
    <div style={{ display: "flex", justifyContent: "space-between", borderBottom: "1px solid var(--line-1)", padding: "6px 0" }}>
      <span className="label-mono">{label}</span>
      <span className="mono" style={{ fontWeight: 600 }}>{value}</span>
    </div>
  );
}
window.ScreenPipeline = ScreenPipeline;
