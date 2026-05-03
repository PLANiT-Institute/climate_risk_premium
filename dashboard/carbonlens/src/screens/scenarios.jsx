/* Scenario comparison table — primary mode + A/B compare mode */
function ScreenScenarios({ model }) {
  const [mode, setMode] = uS("table"); // table | compare
  const [a, setA] = uS("conservative");
  const [b, setB] = uS("net_zero_high");
  const [sortKey, setSortKey] = uS("crp_bps");
  const [sortAsc, setSortAsc] = uS(true);

  const ss = model.scenarios;
  const rows = uM(() => {
    const sorted = [...ss].sort((x, y) => {
      const dx = x[sortKey] ?? 0, dy = y[sortKey] ?? 0;
      return sortAsc ? dx - dy : dy - dx;
    });
    return sorted;
  }, [ss, sortKey, sortAsc]);

  const setSort = (k) => {
    if (k === sortKey) setSortAsc(!sortAsc);
    else { setSortKey(k); setSortAsc(true); }
  };
  const Th = ({ k, label, num }) => (
    <th className={num ? "num" : ""} onClick={() => setSort(k)} style={{ cursor: "pointer" }}>
      {label} {sortKey === k && <span style={{ color: "var(--accent)" }}>{sortAsc ? "↑" : "↓"}</span>}
    </th>
  );

  const aS = ss.find(s => s.id === a);
  const bS = ss.find(s => s.id === b);

  return (
    <div className="page" style={{ padding: 14 }}>
      <Panel title="All Scenarios" sub={`${ss.length} scenarios · sorted by ${sortKey}`}
        actions={
          <div style={{ display: "flex", gap: 4 }}>
            <button className={"btn sm " + (mode === "table" ? "primary" : "ghost")} onClick={() => setMode("table")}>Table</button>
            <button className={"btn sm " + (mode === "compare" ? "primary" : "ghost")} onClick={() => setMode("compare")}>A/B Compare</button>
          </div>
        }
        body="flush">
        {mode === "table" ? (
          <div style={{ overflow: "auto" }}>
            <table className="tbl">
              <thead>
                <tr>
                  <Th k="name" label="Scenario" />
                  <Th k="overall_rating" label="Rating" />
                  <Th k="crp_bps" label="CRP" num />
                  <Th k="npv_million" label="NPV" num />
                  <Th k="irr_pct" label="IRR" num />
                  <Th k="avg_dscr" label="Avg DSCR" num />
                  <Th k="min_dscr" label="Min DSCR" num />
                  <Th k="llcr" label="LLCR" num />
                  <Th k="dispatch_pct" label="Dispatch" num />
                  <Th k="total_carbon_cost_million" label="Carbon $" num />
                  <Th k="avg_ebitda_million" label="EBITDA avg" num />
                  <Th k="wacc_adjusted_pct" label="WACC" num />
                </tr>
              </thead>
              <tbody>
                {rows.map(s => (
                  <tr key={s.id}>
                    <td>
                      <span style={{ display: "inline-block", width: 8, height: 8, background: scenarioColor(s.id), borderRadius: 1, marginRight: 8, verticalAlign: "middle" }} />
                      <span style={{ fontWeight: 600 }}>{s.name}</span>
                      <span className="muted" style={{ marginLeft: 6, fontSize: 10 }}>{s.transition_name}</span>
                    </td>
                    <td><Rating value={s.overall_rating} /></td>
                    <td className="num" style={{ color: s.crp_bps > 1000 ? "var(--neg)" : s.crp_bps > 500 ? "var(--warn)" : "var(--tx-1)", fontWeight: 600 }}>{fmtNum(s.crp_bps, { digits: 0 })}</td>
                    <td className={"num " + (s.npv_million < 0 ? "neg" : "")}>{"$" + fmtNum(s.npv_million, { digits: 0 }) + "M"}</td>
                    <td className="num">{s.irr_pct == null ? "N/A" : fmtPct(s.irr_pct, 2)}</td>
                    <td className="num">{s.avg_dscr.toFixed(2) + "×"}</td>
                    <td className="num">{s.min_dscr.toFixed(2) + "×"}</td>
                    <td className="num">{s.llcr.toFixed(2)}</td>
                    <td className="num muted">{s.dispatch_pct.toFixed(0) + "%"}</td>
                    <td className="num">{"$" + fmtNum(s.total_carbon_cost_million, { digits: 0 }) + "M"}</td>
                    <td className={"num " + (s.avg_ebitda_million < 0 ? "neg" : "")}>{"$" + fmtNum(s.avg_ebitda_million, { digits: 0 }) + "M"}</td>
                    <td className="num">{fmtPct(s.wacc_adjusted_pct, 2)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div style={{ padding: 14 }}>
            <div style={{ display: "flex", gap: 8, marginBottom: 12 }}>
              <div style={{ flex: 1 }}>
                <div className="label-mono" style={{ marginBottom: 4 }}>Scenario A</div>
                <select className="select" value={a} onChange={e => setA(e.target.value)}>
                  {ss.map(s => <option key={s.id} value={s.id}>{s.name}</option>)}
                </select>
              </div>
              <div style={{ width: 24 }} />
              <div style={{ flex: 1 }}>
                <div className="label-mono" style={{ marginBottom: 4 }}>Scenario B</div>
                <select className="select" value={b} onChange={e => setB(e.target.value)}>
                  {ss.map(s => <option key={s.id} value={s.id}>{s.name}</option>)}
                </select>
              </div>
            </div>
            <CompareTable a={aS} b={bS} />
          </div>
        )}
      </Panel>

      <div className="grid-2">
        <Panel title="WACC · Baseline vs. Scenario">
          <ScatterChart
            data={ss.map(s => ({ x: s.wacc_baseline_pct, y: s.wacc_adjusted_pct, label: s.name, color: scenarioColor(s.id) }))}
            xLabel="Baseline WACC (%)" yLabel="Scenario WACC (%)"
            xFormat={v => v.toFixed(1) + "%"} yFormat={v => v.toFixed(1) + "%"}
            refDiagonal height={300}
          />
        </Panel>
        <Panel title="DSCR vs. CRP">
          <ScatterChart
            data={ss.map(s => ({ x: s.avg_dscr, y: s.crp_bps, label: s.name, color: scenarioColor(s.id) }))}
            xLabel="Avg DSCR (×)" yLabel="CRP (bps)"
            xFormat={v => v.toFixed(2)} yFormat={v => v.toFixed(0) + " bps"}
            height={300}
          />
        </Panel>
      </div>
    </div>
  );
}

function CompareTable({ a, b }) {
  if (!a || !b) return null;
  const rows = [
    ["Rating", <Rating value={a.overall_rating}/>, <Rating value={b.overall_rating}/>],
    ["NPV ($M)", "$" + fmtNum(a.npv_million,{digits:0}), "$" + fmtNum(b.npv_million,{digits:0}), a.npv_million - b.npv_million, "$M"],
    ["IRR (%)", a.irr_pct == null ? "N/A" : a.irr_pct.toFixed(2), b.irr_pct == null ? "N/A" : b.irr_pct.toFixed(2)],
    ["CRP (bps)", a.crp_bps.toFixed(0), b.crp_bps.toFixed(0), a.crp_bps - b.crp_bps, "bps", true],
    ["Avg DSCR", a.avg_dscr.toFixed(2)+"×", b.avg_dscr.toFixed(2)+"×"],
    ["Min DSCR", a.min_dscr.toFixed(2)+"×", b.min_dscr.toFixed(2)+"×"],
    ["LLCR", a.llcr.toFixed(2), b.llcr.toFixed(2)],
    ["WACC (%)", a.wacc_adjusted_pct.toFixed(2), b.wacc_adjusted_pct.toFixed(2)],
    ["Dispatch penalty", a.dispatch_pct.toFixed(0)+"%", b.dispatch_pct.toFixed(0)+"%"],
    ["Total carbon cost ($M)", fmtNum(a.total_carbon_cost_million,{digits:0}), fmtNum(b.total_carbon_cost_million,{digits:0})],
    ["Avg EBITDA ($M)", fmtNum(a.avg_ebitda_million,{digits:0}), fmtNum(b.avg_ebitda_million,{digits:0})],
  ];
  return (
    <table className="tbl" style={{ width: "100%" }}>
      <thead>
        <tr>
          <th>Metric</th>
          <th className="num"><span style={{ display: "inline-block", width: 8, height: 8, background: scenarioColor(a.id), marginRight: 6 }} />{a.name}</th>
          <th className="num"><span style={{ display: "inline-block", width: 8, height: 8, background: scenarioColor(b.id), marginRight: 6 }} />{b.name}</th>
          <th className="num">Δ A − B</th>
        </tr>
      </thead>
      <tbody>
        {rows.map((r,i) => (
          <tr key={i}>
            <td className="muted">{r[0]}</td>
            <td className="num" style={{ fontWeight: 600 }}>{r[1]}</td>
            <td className="num" style={{ fontWeight: 600 }}>{r[2]}</td>
            <td className="num" style={{ color: r[3] == null ? "var(--tx-3)" : (r[5] ? (r[3] > 0 ? "var(--neg)" : "var(--pos)") : (r[3] > 0 ? "var(--pos)" : "var(--neg)")) }}>
              {r[3] == null ? "—" : (r[3] > 0 ? "+" : "") + (typeof r[3] === "number" ? r[3].toFixed(0) : r[3]) + (r[4] ? " " + r[4] : "")}
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}

window.ScreenScenarios = ScreenScenarios;
