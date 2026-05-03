/* Risk decomposition */
function ScreenDecomp({ model }) {
  const noRisk = model.scenarios.find(s => s.id === "no_risk_baseline");
  const ss = model.scenarios.filter(s => s.id !== "no_risk_baseline");
  const noRiskNpv = noRisk ? noRisk.npv_million : 0;

  const decomp = [...ss].sort((a,b) => a.npv_million - b.npv_million).map(s => {
    const npvLoss = noRiskNpv - s.npv_million;
    const carbon = s.total_carbon_cost_million;
    const other = Math.max(0, npvLoss - carbon);
    return {
      label: s.name,
      carbon, other,
      total: npvLoss,
      id: s.id,
    };
  });

  const worst = ss.reduce((a, s) => s.npv_million < a.npv_million ? s : a, ss[0]);

  const allYears = ss[0].rows.map(r => r.year).filter(y => y >= 2025 && y <= 2050);
  const carbonOverTime = allYears.map(y => {
    const row = { x: y };
    ss.forEach(s => {
      const r = s.rows.find(rr => rr.year === y);
      row[s.id] = r ? r.carbon_cost / 1e6 : null;
    });
    return row;
  });

  const onset = ss.map(s => {
    const first = s.rows.find(r => r.ebitda < 0);
    return {
      ...s,
      first_neg: first ? first.year : null,
    };
  }).sort((a,b) => (a.first_neg || 9999) - (b.first_neg || 9999));

  return (
    <div className="page" style={{ padding: 14 }}>
      <Panel title="Why ratings collapse to D · context">
        <div style={{ fontSize: 12, color: "var(--tx-2)", lineHeight: 1.6 }}>
          The KIS rating model floors at <strong style={{ color: "var(--neg)" }}>D</strong> when cumulative EBITDA goes negative — regardless of severity.
          Multiple carbon scenarios hit this floor, making CRP identical for all of them.
          The economically meaningful differentiation is in <strong className="accent-c">NPV destruction</strong> and <strong className="accent-c">cumulative carbon cost</strong>.
        </div>
      </Panel>

      <div className="grid-4">
        <KPI label="No-risk NPV" value={"$" + fmtNum(noRiskNpv,{digits:0})} unit="M" />
        <KPI label="No-risk rating" value={<Rating value={noRisk?.overall_rating || "—"} />} />
        <KPI label="Worst NPV" value={"$" + fmtNum(worst.npv_million,{digits:0})} unit="M"
          delta={worst.name} deltaPos={false} />
        <KPI label="Max NPV destruction"
          value={"$" + fmtNum(noRiskNpv - worst.npv_million,{digits:0})} unit="M"
          delta="vs no-risk baseline" deltaPos={false} />
      </div>

      <div className="grid-2">
        <Panel title="NPV Loss · vs No-Risk" sub="USD M · stacked decomposition">
          <BarChart
            data={decomp.map(d => ({ label: d.label, carbon: d.carbon, other: d.other }))}
            stacked
            series={[
              { key: "carbon", label: "Carbon cost (K-ETS)", color: "var(--neg)" },
              { key: "other",  label: "Dispatch / CF loss",  color: "#a78bfa" },
            ]}
            valueFormat={v => "$" + v.toFixed(0) + "M"}
            height={300}
            padding={{ top: 8, right: 80, bottom: 28, left: 170 }}
            xLabel="NPV loss ($M)"
          />
          <div style={{ display: "flex", gap: 14, paddingLeft: 170, marginTop: 6, fontFamily: "var(--font-mono)", fontSize: 10, color: "var(--tx-2)" }}>
            <span><span style={{ display: "inline-block", width: 12, height: 12, background: "var(--neg)", marginRight: 4 }}/> Carbon cost</span>
            <span><span style={{ display: "inline-block", width: 12, height: 12, background: "#a78bfa", marginRight: 4 }}/> Dispatch/CF</span>
          </div>
        </Panel>

        <Panel title="Carbon vs. Dispatch · Loss Plane" sub="$M cumulative">
          <ScatterChart
            data={decomp.map(d => ({ x: d.carbon, y: d.other, label: d.label, color: scenarioColor(d.id) }))}
            xLabel="Carbon cost ($M)" yLabel="Dispatch loss ($M)"
            xFormat={v => "$" + v.toFixed(0)} yFormat={v => "$" + v.toFixed(0)}
            height={300}
          />
        </Panel>
      </div>

      <Panel title="Annual Carbon Cost · By Scenario" sub="$M / year">
        <LineChart data={carbonOverTime}
          series={ss.map(s => ({ key: s.id, label: s.name, color: scenarioColor(s.id) }))}
          height={280}
          yFormat={v => "$" + v.toFixed(0) + "M"} xFormat={v => v.toString()}
          xMin={2025} xMax={2050} />
      </Panel>

      <Panel title="Stress Onset · Year EBITDA First Goes Negative" body="flush">
        <table className="tbl">
          <thead>
            <tr>
              <th>Scenario</th>
              <th>EBITDA → negative</th>
              <th className="num">Dispatch penalty</th>
              <th className="num">NPV ($M)</th>
              <th className="num">Carbon cost ($M)</th>
              <th className="num">CRP (bps)</th>
              <th>Rating</th>
            </tr>
          </thead>
          <tbody>
            {onset.map(s => (
              <tr key={s.id}>
                <td><span style={{ width: 8, height: 8, background: scenarioColor(s.id), display: "inline-block", marginRight: 8 }}/>{s.name}</td>
                <td className={s.first_neg ? "neg" : "muted"} style={{ fontWeight: 600 }}>{s.first_neg || "Never"}</td>
                <td className="num">{s.dispatch_pct.toFixed(0)}%</td>
                <td className={"num " + (s.npv_million < 0 ? "neg" : "")}>{"$" + fmtNum(s.npv_million,{digits:0})}</td>
                <td className="num">{"$" + fmtNum(s.total_carbon_cost_million,{digits:0})}</td>
                <td className="num" style={{ fontWeight: 600 }}>{s.crp_bps.toFixed(0)}</td>
                <td><Rating value={s.overall_rating} /></td>
              </tr>
            ))}
          </tbody>
        </table>
      </Panel>
    </div>
  );
}
window.ScreenDecomp = ScreenDecomp;
