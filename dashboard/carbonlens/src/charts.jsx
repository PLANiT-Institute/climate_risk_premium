/* Chart primitives — bespoke SVG, no deps. */
const { useState, useRef, useMemo, useEffect, useCallback } = React;

const fmtNum = (n, opts = {}) => {
  if (n === null || n === undefined || (typeof n === "number" && isNaN(n))) return "—";
  const { digits = 0, prefix = "", suffix = "", compact = false } = opts;
  if (compact) {
    const abs = Math.abs(n);
    if (abs >= 1e9) return prefix + (n/1e9).toFixed(2) + "B" + suffix;
    if (abs >= 1e6) return prefix + (n/1e6).toFixed(1) + "M" + suffix;
    if (abs >= 1e3) return prefix + (n/1e3).toFixed(1) + "K" + suffix;
    return prefix + n.toFixed(digits) + suffix;
  }
  return prefix + n.toLocaleString(undefined, { minimumFractionDigits: digits, maximumFractionDigits: digits }) + suffix;
};
const fmtBps = (n) => (n === null || n === undefined || isNaN(n)) ? "—" : Math.round(n).toLocaleString() + " bps";
const fmtPct = (n, d = 1) => (n === null || n === undefined || isNaN(n)) ? "—" : n.toFixed(d) + "%";
const fmtMoney = (n, d = 0) => (n === null || n === undefined || isNaN(n)) ? "—" : "$" + n.toLocaleString(undefined,{minimumFractionDigits:d, maximumFractionDigits:d});

function useTooltip() {
  const [tip, setTip] = useState(null);
  return { tip, show: (x, y, content) => setTip({ x, y, content }), hide: () => setTip(null) };
}

function ChartTip({ tip, parentRef }) {
  if (!tip) return null;
  return (
    <div className="chart-tip" style={{ left: tip.x + 12, top: tip.y - 12 }}>
      {tip.content}
    </div>
  );
}

/* ---- LineChart -------------------------------------------------- */
function LineChart({
  data, // [{x, ...series}]
  series, // [{key, label, color, dash}]
  width = 600, height = 240,
  yLabel = "", yFormat = (v) => v.toFixed(0),
  xFormat = (v) => v,
  yMin, yMax, xMin, xMax,
  refLines = [], // [{y, label, color, dash}]
  refLinesX = [], // [{x, label, color, dash}]
  area = false,
  showLegend = true,
  padding = { top: 10, right: 16, bottom: 32, left: 50 },
}) {
  const svgRef = useRef(null);
  const { tip, show, hide } = useTooltip();
  const [hoverX, setHoverX] = useState(null);

  const xs = data.map(d => d.x);
  const allY = series.flatMap(s => data.map(d => d[s.key])).filter(v => v != null && !isNaN(v));
  const yLo = yMin ?? Math.min(0, ...allY);
  const yHi = yMax ?? Math.max(...allY) * 1.05;
  const xLo = xMin ?? Math.min(...xs);
  const xHi = xMax ?? Math.max(...xs);

  const innerW = width - padding.left - padding.right;
  const innerH = height - padding.top - padding.bottom;
  const sx = (x) => padding.left + (x - xLo) / (xHi - xLo || 1) * innerW;
  const sy = (y) => padding.top + innerH - (y - yLo) / (yHi - yLo || 1) * innerH;

  const yTicks = niceTicks(yLo, yHi, 5);
  const xTicks = niceXTicks(xLo, xHi, 6);

  const path = (s) => data.map((d, i) => {
    const v = d[s.key];
    if (v == null || isNaN(v)) return "";
    return (i === 0 ? "M" : "L") + sx(d.x) + " " + sy(v);
  }).join(" ");

  const areaPath = (s) => {
    const top = data.map((d, i) => (i === 0 ? "M" : "L") + sx(d.x) + " " + sy(d[s.key])).join(" ");
    return top + " L" + sx(xs[xs.length-1]) + " " + sy(0) + " L" + sx(xs[0]) + " " + sy(0) + " Z";
  };

  const onMove = (e) => {
    const rect = svgRef.current.getBoundingClientRect();
    const px = e.clientX - rect.left;
    if (px < padding.left || px > width - padding.right) { setHoverX(null); hide(); return; }
    const xVal = xLo + (px - padding.left) / innerW * (xHi - xLo);
    let nearest = data[0], minD = Infinity;
    data.forEach(d => { const dd = Math.abs(d.x - xVal); if (dd < minD) { minD = dd; nearest = d; }});
    setHoverX(nearest.x);
    show(e.clientX - rect.left, e.clientY - rect.top, (
      <div>
        <div style={{ color: "var(--tx-3)", marginBottom: 4 }}>{xFormat(nearest.x)}</div>
        {series.map(s => (
          <div key={s.key} style={{ display: "flex", justifyContent: "space-between", gap: 12 }}>
            <span><span className="k" style={{ background: s.color }}/>{s.label}</span>
            <span style={{ fontWeight: 600 }}>{nearest[s.key] != null ? yFormat(nearest[s.key]) : "—"}</span>
          </div>
        ))}
      </div>
    ));
  };

  return (
    <div style={{ position: "relative", width: "100%" }}>
      <svg ref={svgRef} width="100%" height={height} viewBox={`0 0 ${width} ${height}`} preserveAspectRatio="none"
        onMouseMove={onMove} onMouseLeave={() => { setHoverX(null); hide(); }}>
        {/* gridlines */}
        {yTicks.map((t, i) => (
          <g key={"y"+i}>
            <line x1={padding.left} x2={width - padding.right} y1={sy(t)} y2={sy(t)}
              stroke="var(--grid)" strokeWidth="1" strokeDasharray={t === 0 ? "" : "2 3"} />
            <text x={padding.left - 8} y={sy(t)} dy="0.32em" textAnchor="end"
              fontFamily="var(--font-mono)" fontSize="10" fill="var(--tx-3)">{yFormat(t)}</text>
          </g>
        ))}
        {xTicks.map((t, i) => (
          <text key={"x"+i} x={sx(t)} y={height - 12} textAnchor="middle"
            fontFamily="var(--font-mono)" fontSize="10" fill="var(--tx-3)">{xFormat(t)}</text>
        ))}
        {/* axis */}
        <line x1={padding.left} x2={width - padding.right} y1={padding.top + innerH} y2={padding.top + innerH} stroke="var(--line-2)" />
        {yLabel && (
          <text x={padding.left} y={padding.top - 2} fontFamily="var(--font-mono)" fontSize="9"
            letterSpacing="0.12em" fill="var(--tx-3)" textTransform="uppercase">{yLabel}</text>
        )}
        {/* refLines */}
        {refLines.map((r, i) => (
          <g key={"r"+i}>
            <line x1={padding.left} x2={width - padding.right} y1={sy(r.y)} y2={sy(r.y)}
              stroke={r.color || "var(--warn)"} strokeDasharray={r.dash || "4 3"} strokeWidth="1" />
            {r.label && <text x={width - padding.right - 4} y={sy(r.y) - 3} textAnchor="end"
              fontFamily="var(--font-mono)" fontSize="9" fill={r.color || "var(--warn)"}>{r.label}</text>}
          </g>
        ))}
        {refLinesX.map((r, i) => (
          <g key={"rx"+i}>
            <line x1={sx(r.x)} x2={sx(r.x)} y1={padding.top} y2={padding.top + innerH}
              stroke={r.color || "var(--tx-4)"} strokeDasharray={r.dash || "2 3"} strokeWidth="1" />
            {r.label && <text x={sx(r.x) + 4} y={padding.top + 10}
              fontFamily="var(--font-mono)" fontSize="9" fill={r.color || "var(--tx-3)"}>{r.label}</text>}
          </g>
        ))}
        {/* area fill */}
        {area && series.map((s, i) => (
          <path key={"a"+i} d={areaPath(s)} fill={s.color} opacity="0.10" />
        ))}
        {/* lines */}
        {series.map((s, i) => (
          <path key={"l"+i} d={path(s)} fill="none" stroke={s.color}
            strokeWidth={s.width || 2} strokeDasharray={s.dash} strokeLinecap="round" strokeLinejoin="round" />
        ))}
        {/* hover crosshair */}
        {hoverX != null && (
          <line x1={sx(hoverX)} x2={sx(hoverX)} y1={padding.top} y2={padding.top + innerH}
            stroke="var(--accent)" strokeDasharray="2 2" strokeWidth="1" />
        )}
        {hoverX != null && series.map((s, i) => {
          const d = data.find(d => d.x === hoverX);
          if (!d || d[s.key] == null) return null;
          return <circle key={"h"+i} cx={sx(hoverX)} cy={sy(d[s.key])} r="3"
            fill="var(--bg-1)" stroke={s.color} strokeWidth="2" />;
        })}
      </svg>
      <ChartTip tip={tip} />
      {showLegend && (
        <div style={{ display: "flex", flexWrap: "wrap", gap: 14, paddingLeft: padding.left, marginTop: 4, fontFamily: "var(--font-mono)", fontSize: 10, color: "var(--tx-2)" }}>
          {series.map(s => (
            <div key={s.key} style={{ display: "flex", alignItems: "center", gap: 6 }}>
              <span style={{ display: "inline-block", width: 16, height: 2, background: s.color }} />
              <span style={{ letterSpacing: "0.08em" }}>{s.label}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

/* ---- BarChart (horizontal or vertical) -------------------------- */
function BarChart({
  data, // [{label, value, color?, secondary?}]
  width = 600, height = 240,
  orientation = "horizontal",
  valueFormat = (v) => v.toFixed(0),
  xLabel = "",
  stacked = false,
  series, // when stacked: [{key, label, color}]
  showValues = true,
  padding = { top: 8, right: 60, bottom: 28, left: 140 },
}) {
  if (orientation === "horizontal") {
    const innerW = width - padding.left - padding.right;
    const innerH = height - padding.top - padding.bottom;
    const rowH = innerH / data.length;
    const total = stacked
      ? Math.max(...data.map(d => series.reduce((a, s) => a + (d[s.key] || 0), 0)))
      : Math.max(...data.map(d => Math.abs(d.value)));
    const min = stacked ? 0 : Math.min(0, ...data.map(d => d.value));
    const sx = (v) => padding.left + (v - min) / (total - min || 1) * innerW;
    const xTicks = niceTicks(min, total, 4);
    return (
      <svg width="100%" height={height} viewBox={`0 0 ${width} ${height}`}>
        {xTicks.map((t, i) => (
          <g key={i}>
            <line x1={sx(t)} x2={sx(t)} y1={padding.top} y2={padding.top + innerH}
              stroke="var(--grid)" strokeDasharray={t === 0 ? "" : "2 3"} />
            <text x={sx(t)} y={height - 10} textAnchor="middle"
              fontFamily="var(--font-mono)" fontSize="10" fill="var(--tx-3)">{valueFormat(t)}</text>
          </g>
        ))}
        {data.map((d, i) => {
          const y = padding.top + i * rowH + 4;
          const h = rowH - 8;
          if (stacked) {
            let acc = 0;
            return (
              <g key={i}>
                <text x={padding.left - 8} y={y + h/2} dy="0.32em" textAnchor="end"
                  fontFamily="var(--font-mono)" fontSize="11" fill="var(--tx-2)">{d.label}</text>
                {series.map((s, j) => {
                  const v = d[s.key] || 0;
                  const x0 = sx(acc), x1 = sx(acc + v);
                  acc += v;
                  return <rect key={j} x={x0} y={y} width={Math.max(0, x1-x0)} height={h} fill={s.color} />;
                })}
                {showValues && (
                  <text x={sx(acc) + 4} y={y + h/2} dy="0.32em"
                    fontFamily="var(--font-mono)" fontSize="10" fill="var(--tx-2)">{valueFormat(acc)}</text>
                )}
              </g>
            );
          }
          const x0 = sx(Math.min(0, d.value));
          const x1 = sx(Math.max(0, d.value));
          return (
            <g key={i}>
              <text x={padding.left - 8} y={y + h/2} dy="0.32em" textAnchor="end"
                fontFamily="var(--font-mono)" fontSize="11" fill="var(--tx-2)">{d.label}</text>
              <rect x={x0} y={y} width={Math.max(1, x1-x0)} height={h} fill={d.color || "var(--accent)"} rx="1" />
              {showValues && (
                <text x={x1 + 4} y={y + h/2} dy="0.32em"
                  fontFamily="var(--font-mono)" fontSize="10" fill="var(--tx-2)">{valueFormat(d.value)}</text>
              )}
            </g>
          );
        })}
        {xLabel && (
          <text x={padding.left} y={padding.top - 2}
            fontFamily="var(--font-mono)" fontSize="9" letterSpacing="0.12em" fill="var(--tx-3)">{xLabel}</text>
        )}
      </svg>
    );
  }
  // vertical
  const innerW = width - padding.left - padding.right;
  const innerH = height - padding.top - padding.bottom;
  const colW = innerW / data.length;
  const max = Math.max(...data.map(d => d.value));
  const min = Math.min(0, ...data.map(d => d.value));
  const sy = (v) => padding.top + innerH - (v - min) / (max - min || 1) * innerH;
  const yTicks = niceTicks(min, max, 4);
  return (
    <svg width="100%" height={height} viewBox={`0 0 ${width} ${height}`}>
      {yTicks.map((t, i) => (
        <g key={i}>
          <line x1={padding.left} x2={width - padding.right} y1={sy(t)} y2={sy(t)} stroke="var(--grid)" />
          <text x={padding.left - 8} y={sy(t)} dy="0.32em" textAnchor="end"
            fontFamily="var(--font-mono)" fontSize="10" fill="var(--tx-3)">{valueFormat(t)}</text>
        </g>
      ))}
      {data.map((d, i) => {
        const x = padding.left + i * colW + colW * 0.2;
        const w = colW * 0.6;
        const y = sy(Math.max(0, d.value));
        const h = Math.abs(sy(d.value) - sy(0));
        return (
          <g key={i}>
            <rect x={x} y={y} width={w} height={h} fill={d.color || "var(--accent)"} />
            <text x={x + w/2} y={padding.top + innerH + 14} textAnchor="middle"
              fontFamily="var(--font-mono)" fontSize="10" fill="var(--tx-3)">{d.label}</text>
          </g>
        );
      })}
    </svg>
  );
}

/* ---- StackedAreaChart ------------------------------------------- */
function StackedAreaChart({
  data, series, width = 600, height = 240,
  yFormat = (v) => v.toFixed(0), xFormat = (v) => v,
  padding = { top: 10, right: 16, bottom: 28, left: 56 },
}) {
  const xs = data.map(d => d.x);
  const innerW = width - padding.left - padding.right;
  const innerH = height - padding.top - padding.bottom;
  const totals = data.map(d => series.reduce((a, s) => a + (d[s.key] || 0), 0));
  const yMax = Math.max(...totals) * 1.05;
  const xLo = Math.min(...xs), xHi = Math.max(...xs);
  const sx = (x) => padding.left + (x - xLo) / (xHi - xLo || 1) * innerW;
  const sy = (y) => padding.top + innerH - y / (yMax || 1) * innerH;
  const yTicks = niceTicks(0, yMax, 4);
  const xTicks = niceXTicks(xLo, xHi, 6);
  // stacks bottom-up
  const stacks = series.map((s, idx) => {
    return data.map(d => {
      let base = 0;
      for (let j = 0; j < idx; j++) base += data.find(x => x.x === d.x)[series[j].key] || 0;
      return { x: d.x, y0: base, y1: base + (d[s.key] || 0) };
    });
  });
  return (
    <svg width="100%" height={height} viewBox={`0 0 ${width} ${height}`}>
      {yTicks.map((t,i) => (
        <g key={i}>
          <line x1={padding.left} x2={width-padding.right} y1={sy(t)} y2={sy(t)} stroke="var(--grid)" strokeDasharray="2 3" />
          <text x={padding.left-8} y={sy(t)} dy="0.32em" textAnchor="end"
            fontFamily="var(--font-mono)" fontSize="10" fill="var(--tx-3)">{yFormat(t)}</text>
        </g>
      ))}
      {xTicks.map((t,i) => (
        <text key={i} x={sx(t)} y={height - 10} textAnchor="middle"
          fontFamily="var(--font-mono)" fontSize="10" fill="var(--tx-3)">{xFormat(t)}</text>
      ))}
      {stacks.map((stk, idx) => {
        const top = stk.map((p, i) => (i===0?"M":"L") + sx(p.x) + " " + sy(p.y1));
        const bot = stk.slice().reverse().map(p => "L" + sx(p.x) + " " + sy(p.y0));
        return <path key={idx} d={top.concat(bot).join(" ") + " Z"} fill={series[idx].color} opacity="0.85" />;
      })}
      <line x1={padding.left} x2={width - padding.right} y1={padding.top + innerH} y2={padding.top + innerH} stroke="var(--line-2)" />
    </svg>
  );
}

/* ---- HeatmapChart ----------------------------------------------- */
function HeatmapChart({
  rows, cols, // arrays of labels
  values, // 2D [row][col]
  cellLabel, // optional fn(r,c) → string
  cellColor, // fn(value) → color
  cellTip,   // fn(r,c) → tooltip content
  width = 600, height = 280,
  padding = { top: 8, right: 16, bottom: 28, left: 160 },
}) {
  const innerW = width - padding.left - padding.right;
  const innerH = height - padding.top - padding.bottom;
  const cw = innerW / cols.length;
  const rh = innerH / rows.length;
  const { tip, show, hide } = useTooltip();
  const svgRef = useRef(null);
  return (
    <div style={{ position: "relative", width: "100%" }}>
    <svg ref={svgRef} width="100%" height={height} viewBox={`0 0 ${width} ${height}`} onMouseLeave={hide}>
      {rows.map((r, i) => (
        <text key={"r"+i} x={padding.left - 8} y={padding.top + i*rh + rh/2} dy="0.32em" textAnchor="end"
          fontFamily="var(--font-mono)" fontSize="10.5" fill="var(--tx-2)">{r}</text>
      ))}
      {cols.map((c, j) => {
        const everyN = Math.max(1, Math.floor(cols.length / 12));
        if (j % everyN !== 0 && j !== cols.length - 1) return null;
        return (
          <text key={"c"+j} x={padding.left + j*cw + cw/2} y={height - 10} textAnchor="middle"
            fontFamily="var(--font-mono)" fontSize="9.5" fill="var(--tx-3)">{c}</text>
        );
      })}
      {values.map((row, i) => row.map((v, j) => {
        const x = padding.left + j*cw, y = padding.top + i*rh;
        return (
          <g key={i+"-"+j}
             onMouseEnter={(e) => {
               const rect = svgRef.current.getBoundingClientRect();
               show(e.clientX - rect.left, e.clientY - rect.top, cellTip ? cellTip(i,j) : `${rows[i]} · ${cols[j]}: ${v}`);
             }}
             onMouseMove={(e) => {
               const rect = svgRef.current.getBoundingClientRect();
               show(e.clientX - rect.left, e.clientY - rect.top, cellTip ? cellTip(i,j) : `${rows[i]} · ${cols[j]}: ${v}`);
             }}
             onMouseLeave={hide}>
            <rect x={x+0.5} y={y+0.5} width={cw-1} height={rh-1} fill={cellColor(v)} />
            {cellLabel && cw > 24 && rh > 16 && (
              <text x={x + cw/2} y={y + rh/2} dy="0.32em" textAnchor="middle"
                fontFamily="var(--font-mono)" fontSize="9" fontWeight="700" fill="white"
                style={{ pointerEvents: "none" }}>{cellLabel(i,j)}</text>
            )}
          </g>
        );
      }))}
    </svg>
    <ChartTip tip={tip} />
    </div>
  );
}

/* ---- Sparkline -------------------------------------------------- */
function Sparkline({ data, width = 120, height = 30, color = "currentColor", area = true }) {
  if (!data || data.length === 0) return null;
  const min = Math.min(...data), max = Math.max(...data);
  const span = max - min || 1;
  const sx = (i) => i / (data.length - 1) * (width - 2) + 1;
  const sy = (v) => (1 - (v - min) / span) * (height - 2) + 1;
  const path = data.map((v, i) => (i === 0 ? "M" : "L") + sx(i) + " " + sy(v)).join(" ");
  const areaPath = path + " L" + sx(data.length-1) + " " + (height - 1) + " L" + sx(0) + " " + (height - 1) + " Z";
  return (
    <svg width={width} height={height}>
      {area && <path d={areaPath} fill={color} opacity="0.15" />}
      <path d={path} fill="none" stroke={color} strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

/* ---- ScatterChart ----------------------------------------------- */
function ScatterChart({
  data, // [{x,y,label,color,size}]
  width = 600, height = 240,
  xLabel, yLabel,
  xFormat = (v)=>v.toFixed(0), yFormat = (v)=>v.toFixed(0),
  refDiagonal = false,
  padding = { top: 10, right: 20, bottom: 32, left: 56 },
}) {
  const xs = data.map(d => d.x), ys = data.map(d => d.y);
  const xLo = Math.min(...xs) * 0.95, xHi = Math.max(...xs) * 1.05;
  const yLo = Math.min(...ys) * 0.95, yHi = Math.max(...ys) * 1.05;
  const innerW = width - padding.left - padding.right;
  const innerH = height - padding.top - padding.bottom;
  const sx = (x) => padding.left + (x - xLo)/(xHi-xLo || 1) * innerW;
  const sy = (y) => padding.top + innerH - (y - yLo)/(yHi-yLo || 1) * innerH;
  const xTicks = niceTicks(xLo, xHi, 4);
  const yTicks = niceTicks(yLo, yHi, 4);
  return (
    <svg width="100%" height={height} viewBox={`0 0 ${width} ${height}`}>
      {yTicks.map((t,i) => (
        <g key={i}>
          <line x1={padding.left} x2={width-padding.right} y1={sy(t)} y2={sy(t)} stroke="var(--grid)" strokeDasharray="2 3" />
          <text x={padding.left-8} y={sy(t)} dy="0.32em" textAnchor="end"
            fontFamily="var(--font-mono)" fontSize="10" fill="var(--tx-3)">{yFormat(t)}</text>
        </g>
      ))}
      {xTicks.map((t,i) => (
        <text key={i} x={sx(t)} y={height-12} textAnchor="middle"
          fontFamily="var(--font-mono)" fontSize="10" fill="var(--tx-3)">{xFormat(t)}</text>
      ))}
      {refDiagonal && (
        <line x1={sx(Math.max(xLo,yLo))} y1={sy(Math.max(xLo,yLo))}
              x2={sx(Math.min(xHi,yHi))} y2={sy(Math.min(xHi,yHi))}
              stroke="var(--tx-4)" strokeDasharray="3 3" />
      )}
      {data.map((d, i) => (
        <g key={i}>
          <circle cx={sx(d.x)} cy={sy(d.y)} r={d.size || 5}
            fill={d.color || "var(--accent)"} opacity="0.9" stroke="var(--bg-1)" strokeWidth="1.5" />
          {d.label && <text x={sx(d.x) + 8} y={sy(d.y) - 6}
            fontFamily="var(--font-mono)" fontSize="9.5" fill="var(--tx-2)">{d.label}</text>}
        </g>
      ))}
      {xLabel && <text x={width/2} y={height-2} textAnchor="middle"
        fontFamily="var(--font-mono)" fontSize="9" letterSpacing="0.12em" fill="var(--tx-3)">{xLabel}</text>}
      {yLabel && <text x={4} y={padding.top + innerH/2} textAnchor="middle" transform={`rotate(-90 8 ${padding.top + innerH/2})`}
        fontFamily="var(--font-mono)" fontSize="9" letterSpacing="0.12em" fill="var(--tx-3)">{yLabel}</text>}
    </svg>
  );
}

/* ---- Helpers ---------------------------------------------------- */
function niceTicks(lo, hi, n) {
  if (lo === hi) return [lo];
  const span = hi - lo;
  const step0 = span / n;
  const mag = Math.pow(10, Math.floor(Math.log10(step0)));
  const norm = step0 / mag;
  const step = (norm < 1.5 ? 1 : norm < 3 ? 2 : norm < 7 ? 5 : 10) * mag;
  const out = [];
  const start = Math.ceil(lo / step) * step;
  for (let v = start; v <= hi + step * 0.001; v += step) out.push(+v.toFixed(8));
  return out;
}
function niceXTicks(lo, hi, n) { return niceTicks(lo, hi, n).map(x => Math.round(x)); }

Object.assign(window, {
  LineChart, BarChart, StackedAreaChart, HeatmapChart, Sparkline, ScatterChart,
  ChartTip, useTooltip,
  fmtNum, fmtBps, fmtPct, fmtMoney, niceTicks,
});
