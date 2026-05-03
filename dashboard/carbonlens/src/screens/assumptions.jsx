/* Assumptions editor — inspector pattern, click to edit */
function ScreenAssumptions({ plant, pending, onEdit, onApplyAll, onResetAll }) {
  const groups = [
    { title: "Plant", rows: [
      ["plant_name", "Plant name", plant.name, "name"],
      ["capacity_mw", "Capacity", plant.capacity_mw, "MW"],
      ["capacity_factor", "Base capacity factor", plant.capacity_factor, "%", 0.01, 0, 1, true],
      ["operating_years", "Operating life", plant.operating_years, "years"],
      ["useful_life", "Useful life", plant.useful_life, "years"],
      ["depreciation_years", "Depreciation period", plant.depreciation_years, "years"],
    ]},
    { title: "Operations", rows: [
      ["heat_rate_mmbtu_per_mwh", "Heat rate", 8.8, "MMBtu/MWh", 0.1],
      ["emissions_tco2_per_mwh", "Emissions intensity", plant.emissions_tco2_per_mwh, "tCO₂/MWh", 0.01],
      ["power_price_per_mwh", "Power price", plant.power_price_per_mwh, "$/MWh"],
      ["fuel_cost_per_mwh", "Fuel cost", plant.fuel_cost_per_mwh, "$/MWh"],
      ["fixed_opex_per_kw", "Fixed O&M", plant.fixed_opex_per_kw, "$/kW-yr"],
      ["variable_opex_per_mwh", "Variable O&M", plant.variable_opex_per_mwh, "$/MWh", 0.1],
    ]},
    { title: "Capital", rows: [
      ["total_capex_million", "Total CAPEX", plant.total_capex_million, "$M"],
      ["debt_fraction", "Debt fraction", plant.debt_fraction, "%", 0.01, 0, 1, true],
      ["equity_fraction", "Equity fraction", plant.equity_fraction, "%", 0.01, 0, 1, true],
      ["debt_interest_rate", "Debt interest rate", plant.debt_interest_rate, "%", 0.001, 0, 0.15, true],
      ["debt_tenor_years", "Debt tenor", plant.debt_tenor_years, "years"],
    ]},
    { title: "Discounting · Tax", rows: [
      ["discount_rate", "Discount rate", plant.discount_rate, "%", 0.005, 0, 0.20, true],
      ["tax_rate", "Tax rate", plant.tax_rate, "%", 0.01, 0, 0.5, true],
      ["inflation_rate", "Inflation", plant.inflation_rate, "%", 0.005, 0, 0.10, true],
    ]},
  ];

  const numChanges = Object.keys(pending || {}).length;

  return (
    <div className="page" style={{ padding: 14 }}>
      <Panel title="Assumptions Editor" sub="click any value to edit · changes stage until you Run model"
        actions={
          <div style={{ display: "flex", gap: 6 }}>
            {numChanges > 0 && <span className="chip" style={{ borderColor: "var(--accent)", color: "var(--accent)" }}>{numChanges} pending</span>}
            <button className="btn sm ghost" onClick={onResetAll} disabled={!numChanges}>Discard</button>
            <button className="btn sm primary" onClick={onApplyAll} disabled={!numChanges}>Run model</button>
          </div>
        }>
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
          {groups.map(g => (
            <Panel key={g.title} title={g.title} sub={g.rows.length + " params"} style={{ background: "var(--bg-2)" }} body="flush">
              <table className="tbl">
                <tbody>
                  {g.rows.map(([k, lbl, v, unit, step, min, max, isPct]) => {
                    const pendV = pending?.[k];
                    const display = isPct
                      ? ((pendV !== undefined ? pendV : v) * 100).toFixed(2) + "%"
                      : (typeof v === "number" ? (pendV !== undefined ? pendV : v).toLocaleString() : (pendV !== undefined ? pendV : v));
                    return (
                      <tr key={k}>
                        <td className="muted" style={{ width: "60%" }}>{lbl}</td>
                        <td className="num" style={{ fontWeight: 600 }}>
                          <Editable onClick={() => onEdit({
                            key: k, label: lbl, section: g.title,
                            value: pendV !== undefined ? pendV : v,
                            unit: isPct ? "%" : (unit || ""),
                            step: step || 1,
                            min, max,
                            desc: descFor(k),
                          })}>
                            {display}
                            {pendV !== undefined && <span style={{ marginLeft: 6, color: "var(--accent)", fontSize: 9 }}>● pending</span>}
                          </Editable>
                          <span className="muted" style={{ marginLeft: 6, fontSize: 10 }}>{unit && !isPct ? unit : ""}</span>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </Panel>
          ))}
        </div>
      </Panel>

      <Panel title="Pending Changes" body="flush">
        {numChanges === 0 ? (
          <div style={{ padding: 20, textAlign: "center", color: "var(--tx-3)", fontFamily: "var(--font-mono)", fontSize: 11, letterSpacing: "0.1em", textTransform: "uppercase" }}>
            No staged changes
          </div>
        ) : (
          <table className="tbl">
            <thead><tr><th>Parameter</th><th className="num">From</th><th className="num">To</th><th className="num">Δ</th></tr></thead>
            <tbody>
              {Object.entries(pending).map(([k, v]) => {
                const original = plant[k];
                return (
                  <tr key={k}>
                    <td>{k}</td>
                    <td className="num muted">{typeof original === "number" ? original.toLocaleString() : original}</td>
                    <td className="num accent-c">{typeof v === "number" ? v.toLocaleString() : v}</td>
                    <td className={"num " + (typeof v === "number" && typeof original === "number" && v > original ? "pos" : "neg")}>
                      {typeof v === "number" && typeof original === "number" ? ((v - original > 0 ? "+" : "") + (v - original).toFixed(3)) : "—"}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        )}
      </Panel>
    </div>
  );
}

function descFor(k) {
  const d = {
    capacity_mw: "Plant nameplate capacity. Drives revenue, emissions, fuel.",
    capacity_factor: "Base load capacity factor before scenario adjustments.",
    total_capex_million: "Total project cost. Subtracted at year 0 for NPV.",
    emissions_tco2_per_mwh: "Carbon emission intensity. Multiplied by carbon price.",
    power_price_per_mwh: "Wholesale electricity price. Flat over operating life.",
    discount_rate: "Project WACC for NPV.",
    debt_fraction: "Debt share of capital structure.",
    equity_fraction: "Equity share of capital structure.",
    debt_interest_rate: "Coupon rate on project debt.",
    debt_tenor_years: "Years to fully repay project debt.",
    fuel_cost_per_mwh: "Coal cost per MWh dispatched.",
    fixed_opex_per_kw: "Fixed O&M per kW per year.",
    variable_opex_per_mwh: "Variable O&M per MWh dispatched.",
    tax_rate: "Effective corporate tax rate (Korea: 25%).",
    inflation_rate: "Long-term CPI assumption.",
    operating_years: "Total years of operation.",
    useful_life: "Economic life of the plant.",
    depreciation_years: "Straight-line depreciation period.",
    heat_rate_mmbtu_per_mwh: "MMBtu of fuel per MWh produced.",
  };
  return d[k] || "";
}

window.ScreenAssumptions = ScreenAssumptions;
