/* Credit rating + DSCR + spread + migration heatmap */
function ScreenCredit({ model }) {
  const [selScens, setSelScens] = uS(model.scenarios.map(s => s.id));

  const rows = model.scenarios.flatMap(s => s.yearly_ratings.map(yr => ({ ...yr, scenario: s.id, scenario_name: s.name })));
  const filtered = rows.filter(r => selScens.includes(r.scenario));
  const debtPayoff = model.plant.start_year + model.plant.debt_tenor_years - 1;
  const years = uM(() => Array.from(new Set(filtered.map(r => r.year))).sort(), [filtered]);

  // DSCR per scenario over time
  const dscrData = years.map(y => {
    const row = { x: y };
    model.scenarios.forEach(s => {
      const r = s.yearly_ratings.find(rr => rr.year === y);
      row[s.id] = r && isFinite(r.dscr) ? r.dscr : null;
    });
    return row;
  });
  const spreadData = years.map(y => {
    const row = { x: y };
    model.scenarios.forEach(s => {
      const r = s.yearly_ratings.find(rr => rr.year === y);
      row[s.id] = r ? r.spread_bps : null;
    });
    return row;
  });

  const seriesAll = model.scenarios
    .filter(s => selScens.includes(s.id))
    .map(s => ({ key: s.id, label: s.name, color: scenarioColor(s.id) }));

  // Migration heatmap (year-by-year rating)
  const heatRows = model.scenarios.map(s => s.name);
  const heatScens = model.scenarios.map(s => s.id);
  const heatYears = years.filter(y => y >= 2025 && y <= 2050);
  const heatVals = heatScens.map((sid) => {
    const sc = model.scenarios.find(s => s.id === sid);
    return heatYears.map(y => {
      const r = sc.yearly_ratings.find(rr => rr.year === y);
      return r ? r.rating : "";
    });
  });
  const ratingColor = (r) => {
    const map = { AAA:"#16a34a", AA:"#22c55e", A:"#65a30d", BBB:"#ca8a04", BB:"#ea580c", B:"#dc2626", CCC:"#b91c1c", CC:"#991b1b", C:"#7f1d1d", D:"#450a0a" };
    return map[r] || "var(--bg-3)";
  };

  return (
    <div className="page" style={{ padding: 14 }}>
      <Panel title="Scenario Selector" body="tight">
        <div style={{ display: "flex", flexWrap: "wrap", gap: 6 }}>
          {model.scenarios.map(s => {
            const on = selScens.includes(s.id);
            return (
              <button key={s.id} className={"chip " + (on ? "active" : "")}
                style={on ? { borderColor: scenarioColor(s.id), color: scenarioColor(s.id), background: scenarioColor(s.id)+"22" } : {}}
                onClick={() => setSelScens(on ? selScens.filter(x => x !== s.id) : [...selScens, s.id])}>
                <span style={{ width: 6, height: 6, background: scenarioColor(s.id), display: "inline-block", borderRadius: 1 }} />
                {s.name}
              </button>
            );
          })}
        </div>
      </Panel>

      <div className="grid-2">
        <Panel title="DSCR · Trajectories" sub="× cfads/debt service">
          <LineChart data={dscrData} series={seriesAll} height={300}
            yFormat={v => v.toFixed(2) + "×"} xFormat={v => v.toString()}
            refLines={[
              { y: 1.0, label: "1.0×", color: "var(--neg)", dash: "4 3" },
              { y: 1.25, label: "1.25×", color: "var(--warn)", dash: "2 3" },
            ]}
            refLinesX={[{ x: debtPayoff, label: "Debt repaid", color: "var(--tx-3)" }]}
            xMin={2025} xMax={2050} />
        </Panel>
        <Panel title="Credit Spread · Trajectories" sub="bps">
          <LineChart data={spreadData} series={seriesAll} height={300}
            yFormat={v => v.toFixed(0) + " bps"} xFormat={v => v.toString()}
            xMin={2025} xMax={2050} />
        </Panel>
      </div>

      <Panel title="Rating Component Summary" body="flush">
        <table className="tbl">
          <thead>
            <tr>
              <th>Scenario</th>
              <th>Overall</th>
              <th className="num">Avg DSCR</th>
              <th className="num">EBITDA / Interest</th>
              <th className="num">Debt / Equity</th>
              <th className="num">Spread (bps)</th>
              <th className="num">Cost of Debt</th>
              <th className="num">CRP (bps)</th>
            </tr>
          </thead>
          <tbody>
            {model.scenarios.map(s => (
              <tr key={s.id}>
                <td>
                  <span style={{ display: "inline-block", width: 8, height: 8, background: scenarioColor(s.id), marginRight: 8 }}/>
                  {s.name}
                </td>
                <td><Rating value={s.overall_rating} /></td>
                <td className="num">{s.avg_dscr.toFixed(2)}×</td>
                <td className="num">{s.ebitda_to_interest.toFixed(1)}×</td>
                <td className="num">{s.debt_to_equity_pct.toFixed(0)}%</td>
                <td className="num">{s.spread_bps}</td>
                <td className="num">{(0.0675 + s.spread_bps/1e4).toFixed(4) * 100 ? ((0.0675 + s.spread_bps/1e4) * 100).toFixed(2) + "%" : "—"}</td>
                <td className="num" style={{ color: s.crp_bps > 1000 ? "var(--neg)" : "var(--tx-1)", fontWeight: 600 }}>{s.crp_bps.toFixed(0)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </Panel>

      <Panel title="Rating Migration · Heatmap" sub="year × scenario · 2025 – 2050">
        <HeatmapChart
          rows={heatRows} cols={heatYears.map(String)}
          values={heatVals}
          cellLabel={(i,j) => heatVals[i][j]}
          cellColor={(v) => ratingColor(v)}
          cellTip={(i,j) => `${heatRows[i]} · ${heatYears[j]}: ${heatVals[i][j]}`}
          height={Math.max(220, heatRows.length * 30 + 40)}
          padding={{ top: 8, right: 12, bottom: 28, left: 180 }}
        />
        <div style={{ display: "flex", flexWrap: "wrap", gap: 8, marginTop: 12, paddingLeft: 180, fontFamily: "var(--font-mono)", fontSize: 10 }}>
          {RATING_ORDER.map(r => (
            <div key={r} style={{ display: "flex", alignItems: "center", gap: 4 }}>
              <span style={{ width: 12, height: 12, background: ratingColor(r), display: "inline-block" }} />
              <span style={{ color: "var(--tx-2)" }}>{r}</span>
            </div>
          ))}
        </div>
      </Panel>
    </div>
  );
}
window.ScreenCredit = ScreenCredit;
