/* Physical risk — wildfire, tropical cyclone, drought, chronic heat + heatwave */
function ScreenPhysical({ model }) {
  const [view, setView] = uS("scenarios"); // scenarios | channels | combined
  const [sel, setSel] = uS(model.physicalDefs.map(p => p.id));

  const years = []; for (let y = 2025; y <= 2100; y++) years.push(y);

  // All individual impact channels
  const channels = [
    { key: "outage",     label: "Wildfire — Plant outage",          color: "#0ea5e9" },
    { key: "tx",         label: "Wildfire — Transmission outage",   color: "#38bdf8", dash: "4 3" },
    { key: "tc_outage",  label: "Tropical Cyclone — Plant outage",  color: "#7c3aed" },
    { key: "tc_tx",      label: "Tropical Cyclone — Transmission",  color: "#a78bfa", dash: "4 3" },
    { key: "derate",     label: "Drought — Capacity derate",        color: "#10b981", dash: "2 3" },
    { key: "efficiency", label: "Heat — Total efficiency loss",     color: "#ef4444" },
  ];

  // Heat breakdown sub-channels for the channels view
  const heatSubChannels = [
    { key: "chronicEff", label: "Heat — Chronic (ambient + SST)", color: "#f97316", dash: "3 2" },
    { key: "hwEff",      label: "Heat — Heatwave acute",          color: "#fbbf24", dash: "1 3" },
  ];

  const activeDefs = model.physicalDefs.filter(p => sel.includes(p.id));

  const dataFor = (chKey) => years.map(y => {
    const row = { x: y };
    model.physicalDefs.forEach(p => {
      row[p.id] = physicalAdjustment(p, y)[chKey] * 100;
    });
    return row;
  });

  // Combined outage CF impact (wildfire plant + TC plant + transmission + derate)
  const combinedCfData = years.map(y => {
    const row = { x: y };
    model.physicalDefs.forEach(p => {
      const adj = physicalAdjustment(p, y);
      row[p.id] = (adj.outage + adj.tc_outage + adj.tx + adj.tc_tx + adj.derate) * 100;
    });
    return row;
  });

  const seriesFor = () => activeDefs.map(p => ({ key: p.id, label: p.name, color: p.color }));

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
              {[["scenarios","Compare scenarios"],["channels","Per-scenario channels"],["combined","Combined CF impact"]].map(([k,l]) => (
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
              <LineChart data={dataFor(ch.key)} series={seriesFor()} height={220}
                yFormat={v => v.toFixed(4) + "%"} xFormat={v => v.toString()}
                xMin={2025} xMax={2100} />
            </Panel>
          ))}
        </div>
      )}

      {view === "channels" && (
        <div className="grid-2">
          {activeDefs.map(p => (
            <Panel key={p.id} title={p.name} sub="all impact channels · % / year">
              <LineChart
                data={years.map(y => {
                  const a = physicalAdjustment(p, y);
                  return {
                    x: y,
                    outage:     a.outage     * 100,
                    tx:         a.tx         * 100,
                    tc_outage:  a.tc_outage  * 100,
                    tc_tx:      a.tc_tx      * 100,
                    derate:     a.derate     * 100,
                    efficiency: a.efficiency * 100,
                    chronicEff: a.chronicEff * 100,
                    hwEff:      a.hwEff      * 100,
                  };
                })}
                series={[
                  { key: "outage",     label: "Wildfire — Plant",           color: "#0ea5e9" },
                  { key: "tx",         label: "Wildfire — Transmission",    color: "#38bdf8", dash: "4 3" },
                  { key: "tc_outage",  label: "TC — Plant",                 color: "#7c3aed" },
                  { key: "tc_tx",      label: "TC — Transmission",          color: "#a78bfa", dash: "4 3" },
                  { key: "derate",     label: "Drought derate",             color: "#10b981", dash: "2 3" },
                  { key: "chronicEff", label: "Heat — Chronic",             color: "#f97316", dash: "3 2" },
                  { key: "hwEff",      label: "Heat — Heatwave",            color: "#fbbf24", dash: "1 3" },
                  { key: "efficiency", label: "Heat — Total eff. loss",     color: "#ef4444" },
                ]}
                height={280} yFormat={v => v.toFixed(4) + "%"} xFormat={v => v.toString()}
                xMin={2025} xMax={2100} />
            </Panel>
          ))}
        </div>
      )}

      {view === "combined" && (
        <div className="grid-2">
          <Panel title="Combined Capacity-Factor Impact" sub="plant + transmission (wf + TC) + drought derate">
            <LineChart data={combinedCfData} series={seriesFor()} height={280}
              yFormat={v => v.toFixed(4) + "%"} xFormat={v => v.toString()}
              xMin={2025} xMax={2100} area />
          </Panel>
          <Panel title="Heat — Total Efficiency Loss" sub="chronic (ambient + SST) + heatwave acute · % / year">
            <LineChart
              data={years.map(y => {
                const row = { x: y };
                model.physicalDefs.forEach(p => {
                  const a = physicalAdjustment(p, y);
                  row[p.id + "_total"]   = a.efficiency * 100;
                  row[p.id + "_chronic"] = a.chronicEff * 100;
                  row[p.id + "_hw"]      = a.hwEff      * 100;
                });
                return row;
              })}
              series={activeDefs.flatMap(p => [
                { key: p.id + "_total",   label: p.name + " — Total",   color: p.color },
                { key: p.id + "_chronic", label: p.name + " — Chronic", color: p.color, dash: "4 3" },
                { key: p.id + "_hw",      label: p.name + " — Heatwave",color: p.color, dash: "1 3" },
              ])}
              height={280} yFormat={v => v.toFixed(4) + "%"} xFormat={v => v.toString()}
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
              <th className="num">WF Plant</th>
              <th className="num">WF Tx</th>
              <th className="num">TC Plant</th>
              <th className="num">TC Tx</th>
              <th className="num">Drought</th>
              <th className="num">Eff (total)</th>
              <th className="num">· Chronic</th>
              <th className="num">· Heatwave</th>
            </tr>
          </thead>
          <tbody>
            {model.physicalDefs.flatMap(p => anchors.map(y => {
              const a = physicalAdjustment(p, y);
              const pct = v => (v * 100).toFixed(4) + "%";
              return (
                <tr key={p.id + y}>
                  <td><span style={{ width: 8, height: 8, background: p.color, display: "inline-block", marginRight: 8 }} />{p.name}</td>
                  <td className="muted">{y}</td>
                  <td className="num">{pct(a.outage)}</td>
                  <td className="num">{pct(a.tx)}</td>
                  <td className="num">{pct(a.tc_outage)}</td>
                  <td className="num">{pct(a.tc_tx)}</td>
                  <td className="num">{pct(a.derate)}</td>
                  <td className="num">{pct(a.efficiency)}</td>
                  <td className="num muted">{pct(a.chronicEff)}</td>
                  <td className="num muted">{pct(a.hwEff)}</td>
                </tr>
              );
            }))}
          </tbody>
        </table>
      </Panel>

      <Panel title="Methodology · Data Sources">
        <div style={{ fontSize: 12, color: "var(--tx-2)", lineHeight: 1.7, display: "grid", gap: 8 }}>
          <p><strong>Wildfire frequency:</strong> NASA FIRMS MODIS active fire detections at Samcheok (37.44°N, 129.17°E) via CLIMADA — 6 events / 20 yr = 0.30/yr. Climate amplification: WWA (2025) — ~2× under current 1.3°C warming (2030/2050 anchor), ~4× end-of-century RCP 8.5 (2100).</p>
          <p><strong>Tropical cyclone frequency:</strong> IBTrACS (NOAA/WMO) via CLIMADA — 5 damaging TCs (wind &gt; 30 m/s) / 40 yr = 0.125/yr. Climate amplification: Knutson et al. (2020) — +5% intensity per ~1°C warming, plateauing at +10% beyond ~2°C (2050 anchor). Frequency increase is not modelled (evidence remains mixed per IPCC AR6).</p>
          <p><strong>Drought derate:</strong> Seawater-cooled plant; base derate 0.5% (auxiliary systems only). Climate factor from IPCC AR6 WG1 + archive — 1.12× (2030), 1.45× (2050), 2.0× (2100) at SSP5-8.5.</p>
          <p><strong>Chronic heat + SST efficiency loss:</strong> Korea temperature change from Kim et al. (2016) — +1.75°C by 2050, +4.73°C by 2100 (RCP8.5). Efficiency loss 0.08%/°C ambient (midpoint of gas-turbine literature) + 0.133%/°C cooling water derate (Kim &amp; Jeong 2013) × 0.80 SST-to-air ratio = 1.864e-3/°C total.</p>
          <p><strong>Heatwave acute efficiency loss:</strong> Korea heatwave days 5/yr (2024) → 17.4/yr (2100, SSP5-8.5, WWA 2025). Efficiency loss 4% per event day (modelling assumption). Applied proportionally by days / 365.</p>
          <p><strong>SSP scaling:</strong> All climate factors are scaled to the scenario SSP intensity — baseline (SSP1-2.6): 30% · moderate (SSP2-4.5): 60% · high/severe (SSP5-8.5): 100%. Severe drought applies an additional 2.4× multiplier to the drought channel only.</p>
        </div>
      </Panel>
    </div>
  );
}
window.ScreenPhysical = ScreenPhysical;
