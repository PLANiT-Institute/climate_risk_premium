/* Shared UI primitives + scenario palette */
const { useState: uS, useEffect: uE, useRef: uR, useMemo: uM, useCallback: uC } = React;

const SCENARIO_COLORS = {
  no_risk_baseline:   "#64748b",
  conservative:       "#0ea5e9",
  moderate:           "#8b5cf6",
  korea_ndc:          "#10b981",
  net_zero_high:      "#f59e0b",
  aggressive_severe:  "#ef4444",
  delayed_moderate:   "#6366f1",
  high_ambition_high: "#ec4899",
};
function scenarioColor(id) { return SCENARIO_COLORS[id] || "#94a3b8"; }

function Panel({ title, sub, children, actions, body = "default", style }) {
  return (
    <div className="panel" style={style}>
      <div className="panel-head">
        <span className="corner" />
        <span className="title">{title}</span>
        {sub && <span className="sub">{sub}</span>}
        {actions && <div className="actions">{actions}</div>}
      </div>
      <div className={"panel-body" + (body === "flush" ? " flush" : body === "tight" ? " tight" : "")}>
        {children}
      </div>
    </div>
  );
}

function KPI({ label, value, unit, delta, deltaPos, accent, spark, sparkColor }) {
  return (
    <div className={"kpi" + (accent ? " accent" : "")}>
      {spark && <div className="spark"><Sparkline data={spark} color={sparkColor || "var(--tx-3)"} width={80} height={26} /></div>}
      <div className="lab">{label}</div>
      <div className="val">{value}{unit && <span className="unit">{unit}</span>}</div>
      {delta && (
        <div className={"delta " + (deltaPos === true ? "pos" : deltaPos === false ? "neg" : "")}>
          {delta}
        </div>
      )}
    </div>
  );
}

function Rating({ value }) { return <span className={"rating " + value}>{value}</span>; }

function Field({ label, value, unit, children }) {
  return (
    <div className="field">
      <div className="lab">
        <span>{label}</span>
        {value !== undefined && <span><span className="val">{value}</span>{unit && <span className="unit"> {unit}</span>}</span>}
      </div>
      {children}
    </div>
  );
}

function Slider({ value, min, max, step, onChange, format }) {
  const pct = ((value - min) / (max - min) * 100).toFixed(1);
  return (
    <input type="range" value={value} min={min} max={max} step={step}
      style={{ "--rng": pct + "%" }}
      onChange={e => onChange(parseFloat(e.target.value))} />
  );
}

function Editable({ children, onClick, label }) {
  return (
    <span className="editable" onClick={onClick} title={label || "Click to edit"}>
      {children}
    </span>
  );
}

/* Pending changes context — used by inputs across all screens */
const PendingCtx = React.createContext({ pending: {}, setPending: () => {}, clear: () => {} });

function usePending() { return React.useContext(PendingCtx); }

/* Inspector — opened by editable values */
function Inspector({ open, onClose, target, onApply, onResetAll }) {
  if (!open || !target) return null;
  const [v, setV] = uS(target.value);
  uE(() => { setV(target.value); }, [target?.key]);
  const isNum = typeof target.value === "number";
  return (
    <div className={"inspector " + (open ? "open" : "")}>
      <div className="head">
        <span className="ttl">Edit · {target.section}</span>
        <button className="icon-btn close" onClick={onClose}>
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M18 6 6 18M6 6l12 12"/></svg>
        </button>
      </div>
      <div className="body">
        <div className="row">
          <div className="key">Parameter</div>
          <div style={{ fontWeight: 600, color: "var(--tx-1)", fontSize: 13 }}>{target.label}</div>
          {target.desc && <div className="desc">{target.desc}</div>}
        </div>
        <div className="row">
          <div className="key">Current value</div>
          {isNum ? (
            <>
              <input className="input" type="number" value={v}
                step={target.step || 1}
                onChange={e => setV(parseFloat(e.target.value) || 0)} />
              {target.min != null && target.max != null && (
                <Slider value={v} min={target.min} max={target.max} step={target.step || 1} onChange={setV} />
              )}
            </>
          ) : (
            <input className="input" value={v} onChange={e => setV(e.target.value)} />
          )}
        </div>
        {target.unit && <div className="row"><div className="key">Unit</div><div className="mono" style={{ color: "var(--tx-2)" }}>{target.unit}</div></div>}
        {target.formula && (
          <div className="row">
            <div className="key">Used in</div>
            <div className="mono" style={{ color: "var(--tx-2)", fontSize: 11 }}>{target.formula}</div>
          </div>
        )}
        <div className="row" style={{ flexDirection: "row", gap: 8, paddingTop: 16 }}>
          <button className="btn primary" onClick={() => { onApply(target.key, v); onClose(); }}>Stage change</button>
          <button className="btn ghost" onClick={onClose}>Cancel</button>
          {target.canReset && (
            <button className="btn ghost" style={{ marginLeft: "auto" }} onClick={() => { setV(target.default); }}>Reset</button>
          )}
        </div>
      </div>
    </div>
  );
}

Object.assign(window, {
  SCENARIO_COLORS, scenarioColor,
  Panel, KPI, Rating, Field, Slider, Editable, PendingCtx, usePending, Inspector,
});
