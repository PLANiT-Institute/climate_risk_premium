/* Physical risk — wildfire, drought, heat */
function ScreenPhysical({ model }) {
  const [view, setView] = uS("scenarios"); // scenarios | channels | combined
  const [sel, setSel] = uS(model.physicalDefs.map(p => p.id));

  const years = []; for (let y = 2025; y <= 2100; y++) years.push(y);
  const channels = [
    { key: "outage",     label: "Wildfire — Plant outage" },
    { key: "tx",         label: "Wildfire — Transmission outage" },
    { key: "derate",     label: "Drought — Capacity derate" },
    { key: "efficiency", label: "Heat/SST — Efficiency loss" },
  ];

  const series = (chKey) => model.physicalDefs.filter(p => sel.includes(p.id)).map(p => ({
    key: p.id, label: p.name, color: p.color,
  }));

  const dataFor = (chKey) => years.map(y => {
    const row = { x: y };
    model.physicalDefs.forEach(p => {
      row[p.id] = physicalAdjustment(p, y)[chKey] * 100;
    });
    return row;
  });

  // Combined CF impact: outage + tx + derate
  const combinedCfData = years.map(y => {
    const row = { x: y };
    model.physicalDefs.forEach(p => {
      const adj = physicalAdjustment(p, y);
      row[p.id] = (adj.outage + adj.tx + adj.derate) * 100;
    });
    return row;
  });

  // Snapshot table at anchor years
  const anchors = [2025, 2030, 2050, 2100];

  return (
    <div className="page" style={{ padding: 14 }}>
      <Panel title="Controls" body="tight">
        <div style={{ display: "flex", gap: 16, flexWrap: "wrap", alignItems: "center" }}>
          <div>
            <div className="label-mono" style={{ marginBottom: 6 }}>Physical scenarios</div>
            <div style={{ display: "flex", gap: 6, flexWrap: "wrap" }}>
              {model.physicalDefs.map(p => {
                const on = sel.includes(p.id);
                return (
                  <button key={p.id} className={"chip " + (on ? "active" : "")}
                    style={on ? { borderColor: p.color, color: p.color, background: p.color + "22" } : {}}
                    onClick={() => setSel(on ? sel.filter(x => x !== p.id) : [...sel, p.id])}>
                    <span style={{ width: 6, height: 6, background: p.color, display: "inline-block" }} />
                    {p.name}
                  </button>
                );
              })}
            </div>
          </div>
          <div>
            <div className="label-mono" style={{ marginBottom: 6 }}>View</div>
            <div style={{ display: "flex", gap: 4 }}>
              {[["scenarios","Compare scenarios"],["channels","Compare channels"],["combined","Combined CF impact"]].map(([k,l]) => (
                <button key={k} className={"btn sm " + (view === k ? "primary" : "ghost")} onClick={() => setView(k)}>{l}</button>
              ))}
            </div>
          </div>
        </div>
      </Panel>

      {view === "scenarios" && (
        <div className="grid-2">
          {channels.map(ch => (
            <Panel key={ch.key} title={ch.label} sub="% / year">
              <LineChart data={dataFor(ch.key)} series={series(ch.key)} height={240}
                yFormat={v => v.toFixed(3) + "%"} xFormat={v => v.toString()}
                xMin={2025} xMax={2100} />
            </Panel>
          ))}
        </div>
      )}

      {view === "channels" && (
        <div className="grid-2">
          {model.physicalDefs.filter(p => sel.includes(p.id)).map(p => (
            <Panel key={p.id} title={p.name} sub="all impact channels">
              <LineChart
                data={years.map(y => {
                  const a = physicalAdjustment(p, y);
                  return { x: y, outage: a.outage*100, tx: a.tx*100, derate: a.derate*100, efficiency: a.efficiency*100 };
                })}
                series={[
                  { key: "outage", label: "Plant outage", color: "#0ea5e9" },
                  { key: "tx", label: "Transmission outage", color: "#f59e0b", dash: "4 3" },
                  { key: "derate", label: "Capacity derate", color: "#10b981", dash: "2 3" },
                  { key: "efficiency", label: "Efficiency loss", color: "#ef4444", dash: "1 3" },
                ]}
                height={240} yFormat={v => v.toFixed(3) + "%"} xFormat={v => v.toString()}
                xMin={2025} xMax={2100} />
            </Panel>
          ))}
        </div>
      )}

      {view === "combined" && (
        <div className="grid-2">
          <Panel title="Combined Capacity-Factor Impact" sub="outage + transmission + derate · stacked">
            <LineChart data={combinedCfData} series={series("outage")} height={300}
              yFormat={v => v.toFixed(3) + "%"} xFormat={v => v.toString()}
              xMin={2025} xMax={2100} area />
          </Panel>
          <Panel title="Heat-Rate Efficiency Loss" sub="% per year">
            <LineChart data={dataFor("efficiency")} series={series("efficiency")} height={300}
              yFormat={v => v.toFixed(3) + "%"} xFormat={v => v.toString()}
              xMin={2025} xMax={2100} />
          </Panel>
        </div>
      )}

      <Panel title="Impact at Key Years" body="flush">
        <table className="tbl">
          <thead>
            <tr>
              <th>Scenario</th>
              <th>Year</th>
              {channels.map(c => <th key={c.key} className="num">{c.label}</th>)}
            </tr>
          </thead>
          <tbody>
            {model.physicalDefs.flatMap(p => anchors.map(y => {
              const a = physicalAdjustment(p, y);
              return (
                <tr key={p.id + y}>
                  <td><span style={{ width: 8, height: 8, background: p.color, display: "inline-block", marginRight: 8 }} />{p.name}</td>
                  <td className="muted">{y}</td>
                  <td className="num">{(a.outage*100).toFixed(4)}%</td>
                  <td className="num">{(a.tx*100).toFixed(4)}%</td>
                  <td className="num">{(a.derate*100).toFixed(4)}%</td>
                  <td className="num">{(a.efficiency*100).toFixed(4)}%</td>
                </tr>
              );
            }))}
          </tbody>
        </table>
      </Panel>

      <Panel title="Methodology · Data Sources">
        <div style={{ fontSize: 12, color: "var(--tx-2)", lineHeight: 1.6 }}>
          <p><strong>Hazard frequency:</strong> NASA FIRMS MODIS active fire detections at Samcheok (37.44°N, 129.17°E) via CLIMADA — 6 wildfire events over 2001–2020 → 0.30 events/yr.</p>
          <p><strong>Climate amplification:</strong> WWA (2025) South Korea wildfire likelihood — ~2× under current 1.3°C warming, ~4× under end-of-century RCP 8.5.</p>
          <p><strong>SSP scaling vs RCP 8.5 full intensity:</strong> baseline (SSP1-2.6) 30% · moderate (SSP2-4.5) 60% · high (SSP5-8.5) 100% · severe drought (SSP5-8.5) 100% with 2.4× drought multiplier.</p>
        </div>
      </Panel>
    </div>
  );
}
window.ScreenPhysical = ScreenPhysical;
