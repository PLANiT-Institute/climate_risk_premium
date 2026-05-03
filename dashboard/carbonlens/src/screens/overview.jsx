/* Overview / KPI dashboard */
function ScreenOverview({ model, onEdit }) {
  const ss = model.scenarios;
  const baseline = ss.find(s => s.id === "conservative") || ss[0];
  const noRisk = ss.find(s => s.id === "no_risk_baseline");
  const worst = ss.reduce((a, s) => s.npv_million < a.npv_million ? s : a, ss[0]);
  const maxCRP = ss.reduce((a, s) => s.crp_bps > a.crp_bps ? s : a, ss[0]);
  const investmentGrade = ss.filter(s => ["AAA","AA","A","BBB"].includes(s.overall_rating)).length;

  // KPI sparks: per-scenario NPV across all 8
  const npvSpark = ss.map(s => s.npv_million);

  // Per-scenario summary rows for hero
  const sortedByCrp = [...ss].sort((a, b) => a.crp_bps - b.crp_bps);

  // EBITDA trajectory chart
  const ebitdaData = [];
  const allYears = baseline.rows.map(r => r.year);
  for (const y of allYears) {
    const row = { x: y };
    ss.forEach(s => {
      const r = s.rows.find(rr => rr.year === y);
      row[s.id] = r ? r.ebitda / 1e6 : null;
    });
    ebitdaData.push(row);
  }
  const ebitdaSeries = ss.map(s => ({
    key: s.id, label: s.name, color: scenarioColor(s.id),
  }));

  return (
    <div className="page" style={{ padding: 14 }}>
      {/* KPI strip */}
      <div className="grid-4">
        <KPI label="Baseline NPV" accent
          value={fmtNum(baseline.npv_million, { digits: 0 })}
          unit="USD M"
          delta={<>Rating: <Rating value={baseline.overall_rating} /></>}
          spark={baseline.rows.map(r => r.ebitda / 1e6)}
          sparkColor={scenarioColor(baseline.id)} />
        <KPI label="No-Carbon NPV"
          value={noRisk ? fmtNum(noRisk.npv_million, { digits: 0 }) : "—"} unit="USD M"
          delta={noRisk ? <>Rating: <Rating value={noRisk.overall_rating} /></> : null}
          spark={noRisk?.rows.map(r => r.ebitda / 1e6)}
          sparkColor="var(--pos)" />
        <KPI label="Worst Scenario NPV"
          value={fmtNum(worst.npv_million, { digits: 0 })} unit="USD M"
          delta={<><span className="muted">{worst.name}</span></>}
          deltaPos={false}
          spark={worst.rows.map(r => r.ebitda / 1e6)}
          sparkColor="var(--neg)" />
        <KPI label="Max CRP"
          value={fmtNum(maxCRP.crp_bps, { digits: 0 })} unit="bps"
          delta={<><span className="muted">{maxCRP.name}</span></>}
          deltaPos={false}
          spark={maxCRP.rows.map(r => -r.ebitda / 1e6)}
          sparkColor="var(--warn)" />
      </div>

      <div className="grid-2">
        <Panel title="Climate Risk Premium · By Scenario" sub="basis points · vs A counterfactual">
          <BarChart
            data={sortedByCrp.map(s => ({
              label: s.name, value: s.crp_bps,
              color: scenarioColor(s.id),
            }))}
            valueFormat={v => v.toFixed(0) + " bps"}
            height={300}
            padding={{ top: 8, right: 80, bottom: 28, left: 170 }}
            xLabel="CRP (bps)"
          />
        </Panel>

        <Panel title="NPV · By Scenario" sub="USD millions">
          <BarChart
            data={[...ss].sort((a,b) => a.npv_million - b.npv_million).map(s => ({
              label: s.name, value: s.npv_million,
              color: scenarioColor(s.id),
            }))}
            valueFormat={v => "$" + v.toFixed(0) + "M"}
            height={300}
            padding={{ top: 8, right: 80, bottom: 28, left: 170 }}
            xLabel="NPV ($M)"
          />
        </Panel>
      </div>

      <Panel title="EBITDA Trajectory · All Scenarios"
        sub="USD M / year · 2025 – 2050">
        <LineChart
          data={ebitdaData}
          series={ebitdaSeries}
          height={280}
          xMin={2025} xMax={2050}
          xFormat={v => v.toString()}
          yFormat={v => "$" + v.toFixed(0) + "M"}
          refLines={[{ y: 0, label: "Break-even", color: "var(--tx-3)", dash: "3 3" }]}
        />
      </Panel>

      <div className="grid-3">
        <Panel title="Plant Parameters" sub="click any value to edit" body="flush">
          <table className="tbl">
            <tbody>
              <PlantRow plant={model.plant} k="capacity_mw" label="Capacity" suffix=" MW" onEdit={onEdit} />
              <PlantRow plant={model.plant} k="capacity_factor" label="Base CF" pct onEdit={onEdit} />
              <PlantRow plant={model.plant} k="total_capex_million" label="CAPEX" prefix="$" suffix="M" onEdit={onEdit} />
              <PlantRow plant={model.plant} k="emissions_tco2_per_mwh" label="Emissions" suffix=" tCO₂/MWh" digits={2} onEdit={onEdit} />
              <PlantRow plant={model.plant} k="power_price_per_mwh" label="Power Price" prefix="$" suffix="/MWh" onEdit={onEdit} />
              <PlantRow plant={model.plant} k="discount_rate" label="Discount Rate" pct onEdit={onEdit} />
              <PlantRow plant={model.plant} k="debt_fraction" label="Debt Fraction" pct onEdit={onEdit} />
              <PlantRow plant={model.plant} k="debt_interest_rate" label="Debt Rate" pct onEdit={onEdit} />
            </tbody>
          </table>
        </Panel>

        <Panel title="Rating Distribution" sub="across 8 scenarios">
          <RatingDistribution scenarios={ss} />
        </Panel>

        <Panel title="At a Glance">
          <div style={{ display: "grid", gap: 14 }}>
            <Stat label="Scenarios modelled" value={ss.length} />
            <Stat label="Investment-grade" value={`${investmentGrade} / ${ss.length}`} pos={investmentGrade > ss.length/2}/>
            <Stat label="Plant" value={model.plant.name} />
            <Stat label="Operating life" value={`${model.plant.operating_years} yrs`} />
            <Stat label="Counterfactual rating" value={<Rating value="A" />} />
            <Stat label="Risk-free rate" value="3.50%" />
          </div>
        </Panel>
      </div>
    </div>
  );
}

function PlantRow({ plant, k, label, prefix = "", suffix = "", pct, digits = 0, onEdit }) {
  const v = plant[k];
  const display = pct ? (v * 100).toFixed(0) + "%" :
    prefix + (digits ? v.toFixed(digits) : v.toLocaleString()) + suffix;
  return (
    <tr>
      <td className="muted" style={{ width: "60%" }}>{label}</td>
      <td className="num" style={{ fontWeight: 600 }}>
        <Editable onClick={() => onEdit({
          key: "plant." + k, label, section: "Plant", value: v,
          step: pct ? 0.01 : 1,
          unit: suffix.trim() || (pct ? "%" : ""),
          desc: descFor(k),
        })}>
          {display}
        </Editable>
      </td>
    </tr>
  );
}

function descFor(k) {
  const d = {
    capacity_mw: "Plant nameplate capacity. Drives revenue, emissions, fuel.",
    capacity_factor: "Base load capacity factor before scenario adjustments.",
    total_capex_million: "Total project cost. Subtracted at year 0 for NPV.",
    emissions_tco2_per_mwh: "Carbon emission intensity, multiplied by carbon price.",
    power_price_per_mwh: "Wholesale electricity price assumed flat over operating life.",
    discount_rate: "Project WACC used for NPV.",
    debt_fraction: "Debt share of capital structure.",
    debt_interest_rate: "Coupon rate on project debt.",
  };
  return d[k] || "";
}

function Stat({ label, value, pos }) {
  return (
    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline", borderBottom: "1px solid var(--line-1)", paddingBottom: 8 }}>
      <span className="label-mono">{label}</span>
      <span className="mono" style={{ fontWeight: 600, color: pos === true ? "var(--pos)" : pos === false ? "var(--neg)" : "var(--tx-1)" }}>{value}</span>
    </div>
  );
}

function RatingDistribution({ scenarios }) {
  const counts = {};
  scenarios.forEach(s => { counts[s.overall_rating] = (counts[s.overall_rating] || 0) + 1; });
  const max = Math.max(...Object.values(counts), 1);
  return (
    <div style={{ display: "grid", gap: 6 }}>
      {RATING_ORDER.map(r => {
        const n = counts[r] || 0;
        return (
          <div key={r} style={{ display: "flex", alignItems: "center", gap: 8 }}>
            <Rating value={r} />
            <div style={{ flex: 1, height: 12, background: "var(--bg-inset)", borderRadius: 1, position: "relative" }}>
              <div style={{ width: (n / max * 100) + "%", height: "100%", background: `var(--rt-${r.toLowerCase()})` }} />
            </div>
            <span className="mono" style={{ width: 24, textAlign: "right", color: n > 0 ? "var(--tx-1)" : "var(--tx-4)", fontSize: 11 }}>{n}</span>
          </div>
        );
      })}
    </div>
  );
}

window.ScreenOverview = ScreenOverview;
