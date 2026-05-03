/* Cashflow analysis */
function ScreenCashflows({ model }) {
  const [sel, setSel] = uS("conservative");
  const s = model.scenarios.find(x => x.id === sel) || model.scenarios[0];
  const rows = s.rows.filter(r => r.year >= 2025 && r.year <= 2050);

  const totalRev = s.rows.reduce((a, r) => a + r.revenue, 0);
  const totalCarbon = s.rows.reduce((a, r) => a + r.carbon_cost, 0);
  const avgEbitda = s.rows.reduce((a, r) => a + r.ebitda, 0) / s.rows.length;
  const avgDscr = (() => {
    const v = s.rows.filter(r => isFinite(r.dscr));
    return v.length ? v.reduce((a, r) => a + r.dscr, 0) / v.length : 0;
  })();

  const debtPayoff = model.plant.start_year + model.plant.debt_tenor_years - 1;

  const flowSeries = [
    { key: "revenue", label: "Revenue", color: "var(--pos)" },
    { key: "total_costs", label: "Total Costs", color: "var(--neg)" },
    { key: "ebitda", label: "EBITDA", color: "var(--info)", width: 2.5 },
    { key: "free_cash_flow", label: "Free Cash Flow", color: "#a78bfa", width: 2.5, dash: "5 4" },
  ];
  const flowData = rows.map(r => ({
    x: r.year,
    revenue: r.revenue / 1e6,
    total_costs: r.total_costs / 1e6,
    ebitda: r.ebitda / 1e6,
    free_cash_flow: r.free_cash_flow / 1e6,
  }));

  const costStack = rows.map(r => ({
    x: r.year,
    fuel: r.fuel / 1e6, fixed: r.fixed_opex / 1e6,
    variable: r.variable_opex / 1e6, carbon: r.carbon_cost / 1e6,
  }));

  const dscrData = rows.map(r => ({ x: r.year, dscr: isFinite(r.dscr) ? r.dscr : null }));
  const cfData = rows.map(r => ({ x: r.year, cf: r.capacity_factor * 100 }));

  // Multi-scenario EBITDA
  const allYears = rows.map(r => r.year);
  const ebitdaMulti = allYears.map(y => {
    const row = { x: y };
    model.scenarios.forEach(sc => {
      const r = sc.rows.find(rr => rr.year === y);
      row[sc.id] = r ? r.ebitda / 1e6 : null;
    });
    return row;
  });

  return (
    <div className="page" style={{ padding: 14 }}>
      <Panel title="Cashflow · Scenario Selector"
        actions={
          <select className="select" style={{ width: 220, height: 22 }} value={sel} onChange={e => setSel(e.target.value)}>
            {model.scenarios.map(s => <option key={s.id} value={s.id}>{s.name}</option>)}
          </select>
        }>
        <div className="grid-4">
          <KPI label="Total Revenue" value={"$" + (totalRev/1e9).toFixed(2)} unit="B" />
          <KPI label="Total Carbon Cost" value={"$" + (totalCarbon/1e9).toFixed(2)} unit="B" />
          <KPI label="Avg EBITDA / yr" value={"$" + fmtNum(avgEbitda/1e6,{digits:0})} unit="M" deltaPos={avgEbitda > 0} />
          <KPI label="Avg DSCR" value={avgDscr.toFixed(2)} unit="×" deltaPos={avgDscr >= 1.25} />
        </div>
      </Panel>

      <div className="grid-2">
        <Panel title="Revenue & EBITDA" sub="USD M / year">
          <LineChart data={flowData} series={flowSeries} height={300}
            yFormat={v => "$" + v.toFixed(0) + "M"} xFormat={v => v.toString()}
            refLines={[{ y: 0, color: "var(--tx-3)", dash: "3 3" }]}
            xMin={2025} xMax={2050} />
        </Panel>
        <Panel title="Cost Breakdown" sub="stacked, USD M">
          <StackedAreaChart
            data={costStack}
            series={[
              { key: "fuel", label: "Fuel", color: "#f97316" },
              { key: "fixed", label: "Fixed O&M", color: "#6366f1" },
              { key: "variable", label: "Variable O&M", color: "#a78bfa" },
              { key: "carbon", label: "Carbon (K-ETS)", color: "#ef4444" },
            ]}
            height={300}
            yFormat={v => "$" + v.toFixed(0) + "M"} xFormat={v => v.toString()}
          />
          <div style={{ display: "flex", flexWrap: "wrap", gap: 14, marginTop: 4, paddingLeft: 56, fontFamily: "var(--font-mono)", fontSize: 10, color: "var(--tx-2)" }}>
            {[["Fuel","#f97316"],["Fixed O&M","#6366f1"],["Variable O&M","#a78bfa"],["Carbon (K-ETS)","#ef4444"]].map(([n,c]) => (
              <div key={n} style={{ display: "flex", alignItems: "center", gap: 6 }}>
                <span style={{ display: "inline-block", width: 12, height: 12, background: c }} />
                <span style={{ letterSpacing: "0.08em" }}>{n}</span>
              </div>
            ))}
          </div>
        </Panel>
      </div>

      <div className="grid-2">
        <Panel title="DSCR Trajectory" sub="× (cfads / debt service)">
          <LineChart data={dscrData} series={[{ key: "dscr", label: "DSCR", color: "var(--info)" }]}
            height={260} yFormat={v => v.toFixed(2) + "×"} xFormat={v => v.toString()}
            refLines={[
              { y: 1.0, label: "1.0×", color: "var(--neg)", dash: "4 3" },
              { y: 1.25, label: "1.25×", color: "var(--warn)", dash: "2 3" },
            ]}
            refLinesX={[{ x: debtPayoff, label: "Debt repaid", color: "var(--tx-3)" }]}
            xMin={2025} xMax={2050} area />
        </Panel>
        <Panel title="Capacity Factor" sub="effective % after dispatch + physical">
          <LineChart data={cfData} series={[{ key: "cf", label: "CF", color: "#a78bfa" }]}
            height={260} yFormat={v => v.toFixed(1) + "%"} xFormat={v => v.toString()}
            xMin={2025} xMax={2050} area />
        </Panel>
      </div>

      <Panel title="Multi-Scenario EBITDA" sub="all 8 climate scenarios overlaid">
        <LineChart
          data={ebitdaMulti}
          series={model.scenarios.map(s => ({ key: s.id, label: s.name, color: scenarioColor(s.id) }))}
          height={300}
          yFormat={v => "$" + v.toFixed(0) + "M"} xFormat={v => v.toString()}
          xMin={2025} xMax={2050}
          refLines={[{ y: 0, color: "var(--tx-3)", dash: "3 3" }]} />
      </Panel>
    </div>
  );
}
window.ScreenCashflows = ScreenCashflows;
