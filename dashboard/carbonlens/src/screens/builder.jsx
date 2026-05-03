/* Scenario builder — form + carbon-price curve editor */
function ScreenBuilder({ model, onCommit }) {
  const [name, setName] = uS("Custom Scenario");
  const [dispatch, setDispatch] = uS(0.10);
  const [retire, setRetire] = uS(35);
  const [cp, setCp] = uS([15, 50, 120, 220]); // 2025, 30, 40, 50
  const [physical, setPhysical] = uS("moderate_physical");
  const [base, setBase] = uS("moderate_transition");

  // Live preview — synthesize a transition scenario and run
  const previewScenario = uM(() => {
    const pdef = model.physicalDefs.find(p => p.id === physical);
    const tr = { id: "preview", name, dispatch, retire, cp };
    return computeScenario(model.plant, tr, pdef);
  }, [name, dispatch, retire, cp[0], cp[1], cp[2], cp[3], physical, model.plant]);

  // Curve editor - drag handles
  const [drag, setDrag] = uS(null);
  const editorRef = uR(null);
  const W = 540, H = 220;
  const padding = { left: 50, right: 16, top: 16, bottom: 32 };
  const innerW = W - padding.left - padding.right;
  const innerH = H - padding.top - padding.bottom;
  const yMax = Math.max(...cp, 100) * 1.2;
  const xs = [2025, 2030, 2040, 2050];
  const sx = (x) => padding.left + (x - 2025) / 25 * innerW;
  const sy = (y) => padding.top + innerH - y / yMax * innerH;
  const fromY = (py) => Math.max(0, Math.round((1 - (py - padding.top) / innerH) * yMax));

  const onMouseMove = (e) => {
    if (drag == null) return;
    const rect = editorRef.current.getBoundingClientRect();
    const py = (e.clientY - rect.top) / rect.height * H;
    const v = Math.min(700, Math.max(0, fromY(py)));
    const next = [...cp]; next[drag] = v; setCp(next);
  };
  const onMouseUp = () => setDrag(null);
  uE(() => {
    if (drag != null) {
      window.addEventListener("mousemove", onMouseMove);
      window.addEventListener("mouseup", onMouseUp);
      return () => { window.removeEventListener("mousemove", onMouseMove); window.removeEventListener("mouseup", onMouseUp); };
    }
  }, [drag, cp]);

  const yTicks = niceTicks(0, yMax, 4);

  const path = xs.map((x, i) => (i === 0 ? "M" : "L") + sx(x) + " " + sy(cp[i])).join(" ");

  return (
    <div className="page" style={{ padding: 14 }}>
      <div className="grid-2">
        <Panel title="Scenario Form" sub="parametric inputs">
          <div style={{ display: "grid", gap: 16 }}>
            <Field label="Name">
              <input className="input" value={name} onChange={e => setName(e.target.value)} />
            </Field>
            <Field label="Base preset">
              <select className="select" value={base}
                onChange={e => {
                  const t = model.transitions.find(x => x.id === e.target.value);
                  setBase(e.target.value);
                  if (t) { setDispatch(t.dispatch); setRetire(t.retire); setCp([...t.cp]); }
                }}>
                {model.transitions.map(t => <option key={t.id} value={t.id}>{t.name}</option>)}
              </select>
            </Field>
            <Field label="Dispatch penalty" value={(dispatch*100).toFixed(0)} unit="%">
              <Slider value={dispatch} min={0} max={0.5} step={0.01} onChange={setDispatch} />
            </Field>
            <Field label="Operating life" value={retire} unit="years">
              <Slider value={retire} min={15} max={40} step={1} onChange={setRetire} />
            </Field>
            <Field label="Physical scenario">
              <select className="select" value={physical} onChange={e => setPhysical(e.target.value)}>
                {model.physicalDefs.map(p => <option key={p.id} value={p.id}>{p.name}</option>)}
              </select>
            </Field>
            <div className="divider" />
            <div className="label-mono">Carbon price anchors ($/tCO₂)</div>
            <div className="grid-4">
              {[2025,2030,2040,2050].map((y,i) => (
                <Field key={y} label={y.toString()} value={cp[i]} unit="$/t">
                  <input className="input" type="number" value={cp[i]} step={5}
                    onChange={e => { const v = parseFloat(e.target.value)||0; const next = [...cp]; next[i] = v; setCp(next); }} />
                </Field>
              ))}
            </div>
          </div>
        </Panel>

        <Panel title="Carbon-Price Curve · Drag the Handles" sub="live preview below">
          <svg ref={editorRef} width="100%" height={H} viewBox={`0 0 ${W} ${H}`} style={{ background: "var(--bg-inset)", borderRadius: 4 }}>
            {yTicks.map((t,i) => (
              <g key={i}>
                <line x1={padding.left} x2={W - padding.right} y1={sy(t)} y2={sy(t)}
                  stroke="var(--grid)" strokeDasharray="2 3" />
                <text x={padding.left - 8} y={sy(t)} dy="0.32em" textAnchor="end"
                  fontFamily="var(--font-mono)" fontSize="10" fill="var(--tx-3)">${t}</text>
              </g>
            ))}
            {xs.map((x,i) => (
              <text key={i} x={sx(x)} y={H - 12} textAnchor="middle"
                fontFamily="var(--font-mono)" fontSize="10" fill="var(--tx-3)">{x}</text>
            ))}
            <path d={path + " L" + sx(2050) + " " + sy(0) + " L" + sx(2025) + " " + sy(0) + " Z"}
              fill="var(--accent)" opacity="0.12" />
            <path d={path} fill="none" stroke="var(--accent)" strokeWidth="2.5" />
            {xs.map((x, i) => (
              <g key={i} className="curve-handle" onMouseDown={() => setDrag(i)}>
                <circle cx={sx(x)} cy={sy(cp[i])} r="14" fill="transparent" />
                <circle cx={sx(x)} cy={sy(cp[i])} r="6" fill="var(--accent)" stroke="var(--bg-1)" strokeWidth="2" />
                <text x={sx(x)} y={sy(cp[i]) - 12} textAnchor="middle"
                  fontFamily="var(--font-mono)" fontSize="10" fontWeight="600" fill="var(--tx-1)">${cp[i]}</text>
              </g>
            ))}
          </svg>
        </Panel>
      </div>

      <Panel title="Live Preview · Custom Scenario" sub="re-runs as you edit">
        <div className="grid-4">
          <KPI accent label="NPV" value={"$" + fmtNum(previewScenario.npv_million,{digits:0})} unit="M" />
          <KPI label="Rating" value={<Rating value={previewScenario.overall_rating} />} />
          <KPI label="CRP" value={fmtNum(previewScenario.crp_bps,{digits:0})} unit="bps" />
          <KPI label="Avg DSCR" value={previewScenario.avg_dscr.toFixed(2)} unit="×" />
        </div>
        <div className="divider" />
        <LineChart
          data={previewScenario.rows.filter(r => r.year <= 2050).map(r => ({
            x: r.year, ebitda: r.ebitda/1e6, fcf: r.free_cash_flow/1e6,
            carbon: r.carbon_cost/1e6,
          }))}
          series={[
            { key: "ebitda", label: "EBITDA", color: "var(--info)", width: 2.5 },
            { key: "fcf", label: "Free Cash Flow", color: "#a78bfa", dash: "5 4" },
            { key: "carbon", label: "Carbon cost", color: "var(--neg)" },
          ]}
          height={260} yFormat={v => "$" + v.toFixed(0) + "M"} xFormat={v => v.toString()}
          refLines={[{ y: 0, color: "var(--tx-3)", dash: "3 3" }]}
          xMin={2025} xMax={2050}
        />
        <div style={{ display: "flex", gap: 8, marginTop: 12, justifyContent: "flex-end" }}>
          <button className="btn ghost" onClick={() => { setName("Custom Scenario"); setDispatch(0.10); setRetire(35); setCp([15,50,120,220]); }}>Reset</button>
          <button className="btn primary" onClick={() => onCommit && onCommit({ name, dispatch, retire, cp, physical })}>Save scenario</button>
        </div>
      </Panel>
    </div>
  );
}
window.ScreenBuilder = ScreenBuilder;
