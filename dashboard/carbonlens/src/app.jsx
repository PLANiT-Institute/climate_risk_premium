/* App shell — sidebar + topbar + active screen */
const SCREENS = [
  { id: "overview",    label: "Overview",        icon: "M3 12l2-2 4 4 8-8 4 4" },
  { id: "scenarios",   label: "Scenarios",       icon: "M3 5h18M3 12h18M3 19h18" },
  { id: "cashflows",   label: "Cashflows",       icon: "M3 17l6-6 4 4 8-8" },
  { id: "credit",      label: "Credit & DSCR",   icon: "M4 6h16v4H4zM4 14h16v4H4z" },
  { id: "physical",    label: "Physical Risk",   icon: "M12 2l3 7h7l-5.5 4 2 7L12 16l-6.5 4 2-7L2 9h7z" },
  { id: "decomp",      label: "Decomposition",   icon: "M3 3h7v7H3zM14 3h7v7h-7zM3 14h7v7H3zM14 14h7v7h-7z" },
  { id: "pipeline",    label: "Pipeline",        icon: "M4 4h7v7H4zM13 13h7v7h-7zM11 8h2M8 11v2" },
  { id: "builder",     label: "Builder",         icon: "M12 2v20M2 12h20" },
  { id: "assumptions", label: "Assumptions",     icon: "M5 4h14v4H5zM5 10h14v4H5zM5 16h14v4H5z" },
];

// Colour palette cycled across custom scenarios — distinct from all preset colours
const _CUSTOM_PALETTE = ["#f97316","#14b8a6","#e879f9","#a3e635","#fb923c","#22d3ee","#f43f5e","#84cc16"];

function App({ initialPlant }) {
  const [model, setModel] = uS(() => buildModel(initialPlant || DEFAULT_PLANT));
  const [screen, setScreen] = uS("overview");
  const [pending, setPending] = uS({});
  const [inspector, setInspector] = uS(null);
  const [theme, setTheme] = uS(localStorage.getItem("ksl_theme") || "dark");
  const [accent, setAccent] = uS(localStorage.getItem("ksl_accent") || "amber");

  // Custom scenarios added from the Builder screen
  const [customScenarios, setCustomScenarios] = uS([]);

  uE(() => {
    document.documentElement.setAttribute("data-theme", theme);
    document.documentElement.setAttribute("data-accent", accent);
    localStorage.setItem("ksl_theme", theme);
    localStorage.setItem("ksl_accent", accent);
  }, [theme, accent]);

  const onEdit = (t) => setInspector(t);
  const stageChange = (key, value) => {
    if (key.startsWith("plant.")) {
      const k = key.split(".")[1];
      setPending(p => ({ ...p, [k]: value }));
    } else {
      setPending(p => ({ ...p, [key]: value }));
    }
  };
  const applyAll = () => {
    const newPlant = { ...model.plant, ...pending };
    setModel(buildModel(newPlant));
    setPending({});
  };
  const resetAll = () => setPending({});

  // Augmented model: base scenarios + any saved custom scenarios
  const augmentedModel = uM(() => {
    if (!customScenarios.length) return model;
    const extras = customScenarios.map(cs => {
      const pdef = model.physicalDefs.find(p => p.id === cs.physical) || model.physicalDefs[0];
      const tr = { id: cs.id, name: cs.name, dispatch: cs.dispatch, retire: cs.retire, cp: cs.cp };
      const r = computeScenario(model.plant, tr, pdef);
      return {
        id: cs.id, name: cs.name, desc: "Custom (builder)",
        transition_id: cs.id, physical_id: cs.physical,
        transition_name: cs.name, physical_name: pdef?.name ?? "—",
        dispatch_pct: cs.dispatch * 100, retirement_years: cs.retire,
        carbon_prices: cs.cp, _custom: true,
        ...r,
      };
    });
    return { ...model, scenarios: [...model.scenarios, ...extras] };
  }, [model, customScenarios]);

  const onCommitScenario = (custom) => {
    const id = "custom_" + Date.now();
    const color = _CUSTOM_PALETTE[customScenarios.length % _CUSTOM_PALETTE.length];
    // Register color so scenarioColor(id) works in every screen without changes
    SCENARIO_COLORS[id] = color;
    setCustomScenarios(prev => [...prev, { ...custom, id, color }]);
    setScreen("scenarios"); // jump straight to the results
  };

  const onDeleteCustom = (id) => {
    delete SCENARIO_COLORS[id];
    setCustomScenarios(prev => prev.filter(c => c.id !== id));
  };

  return (
    <PendingCtx.Provider value={{ pending, setPending, clear: resetAll }}>
      <div className="app">
        <aside className="sidebar">
          <div className="brand">
            <div className="brand-mark">
              <svg viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="currentColor" strokeWidth="1.8">
                <path d="M3 20l5-10 4 6 3-4 6 8" />
                <circle cx="3" cy="20" r="1.2" fill="currentColor" />
                <circle cx="21" cy="20" r="1.2" fill="currentColor" />
              </svg>
            </div>
            <div>
              <div className="brand-name">CARBONLENS</div>
              <div className="brand-sub">Climate · Credit · Cashflow</div>
            </div>
          </div>
          <nav className="nav">
            <div className="nav-section">Workbench</div>
            {SCREENS.slice(0, 6).map(s => (
              <button key={s.id} className={"nav-item " + (screen === s.id ? "active" : "")} onClick={() => setScreen(s.id)}>
                <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" strokeWidth="2"><path d={s.icon}/></svg>
                {s.label}
              </button>
            ))}
            <div className="nav-section" style={{ marginTop: 12 }}>Author</div>
            {SCREENS.slice(6).map(s => (
              <button key={s.id} className={"nav-item " + (screen === s.id ? "active" : "")} onClick={() => setScreen(s.id)}>
                <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" strokeWidth="2"><path d={s.icon}/></svg>
                {s.label}
              </button>
            ))}
          </nav>
          <div className="sidebar-foot">
            <div className="status">
              <span className="dot" />
              <span>Live · last run {new Date().toLocaleTimeString()}</span>
            </div>
            <div className="muted" style={{ fontSize: 9, marginTop: 4 }}>v1.4.2 · Samcheok #1 · KIS methodology</div>
          </div>
        </aside>

        <div className="main">
          <header className="topbar">
            <div className="crumbs">
              <span className="muted">Workbench</span>
              <span className="sep">/</span>
              <span>{SCREENS.find(s => s.id === screen)?.label}</span>
              <span className="sep">·</span>
              <span className="muted">{model.plant.name}</span>
            </div>
            <div className="topbar-actions">
              {Object.keys(pending).length > 0 && (
                <>
                  <span className="chip" style={{ borderColor: "var(--accent)", color: "var(--accent)" }}>
                    {Object.keys(pending).length} pending
                  </span>
                  <button className="btn sm ghost" onClick={resetAll}>Discard</button>
                  <button className="btn sm primary" onClick={applyAll}>Run model ▸</button>
                </>
              )}
              <div className="theme-toggle">
                <button className={theme === "light" ? "active" : ""} onClick={() => setTheme("light")}>
                  <svg viewBox="0 0 24 24" width="12" height="12" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M2 12h2M20 12h2M5 5l1.5 1.5M17.5 17.5L19 19M5 19l1.5-1.5M17.5 6.5L19 5"/></svg>
                </button>
                <button className={theme === "dark" ? "active" : ""} onClick={() => setTheme("dark")}>
                  <svg viewBox="0 0 24 24" width="12" height="12" fill="none" stroke="currentColor" strokeWidth="2"><path d="M21 12.8A9 9 0 0111.2 3 7 7 0 1021 12.8z"/></svg>
                </button>
              </div>
            </div>
          </header>

          <main className="screen">
            {screen === "overview"    && <ScreenOverview model={augmentedModel} onEdit={onEdit} />}
            {screen === "scenarios"   && <ScreenScenarios model={augmentedModel} />}
            {screen === "cashflows"   && <ScreenCashflows model={augmentedModel} />}
            {screen === "credit"      && <ScreenCredit model={augmentedModel} />}
            {screen === "physical"    && <ScreenPhysical model={augmentedModel} />}
            {screen === "decomp"      && <ScreenDecomp model={augmentedModel} />}
            {screen === "pipeline"    && <ScreenPipeline model={augmentedModel} />}
            {screen === "builder"     && <ScreenBuilder model={model} onCommit={onCommitScenario}
                                           customScenarios={customScenarios} onDeleteCustom={onDeleteCustom}
                                           onGoToScenarios={() => setScreen("scenarios")} />}
            {screen === "assumptions" && <ScreenAssumptions plant={model.plant} pending={pending} onEdit={onEdit} onApplyAll={applyAll} onResetAll={resetAll} />}
          </main>
        </div>

        <Inspector
          open={!!inspector}
          target={inspector}
          onClose={() => setInspector(null)}
          onApply={stageChange}
        />
      </div>
    </PendingCtx.Provider>
  );
}

(async () => {
  const root = document.getElementById("root");

  // Show a minimal spinner while CSVs are loading from the backend
  root.innerHTML =
    '<div style="display:flex;align-items:center;justify-content:center;height:100vh;' +
    'color:var(--tx-2);font-family:var(--font-mono);gap:14px">' +
    '<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"' +
    ' style="animation:spin 1s linear infinite">' +
    '<style>@keyframes spin{to{transform:rotate(360deg)}}</style>' +
    '<path d="M12 2v4M12 18v4M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83M2 12h4M18 12h4' +
    'M4.93 19.07l2.83-2.83M16.24 7.76l2.83-2.83"/></svg>' +
    'Loading data…</div>';

  try {
    const data = await fetch("/api/data").then(r => {
      if (!r.ok) throw new Error("HTTP " + r.status);
      return r.json();
    });
    initFromData(data);          // populate all empty-shell constants
    root.innerHTML = "";         // clear spinner
    ReactDOM.createRoot(root).render(<App initialPlant={data.plant} />);
  } catch (err) {
    root.innerHTML =
      '<div style="display:flex;flex-direction:column;align-items:center;justify-content:center;' +
      'height:100vh;gap:16px;color:var(--neg);font-family:var(--font-mono)">' +
      '<strong>Failed to load model data</strong>' +
      '<span style="color:var(--tx-3);font-size:12px">' + err.message + '</span>' +
      '<span style="color:var(--tx-4);font-size:11px">Is serve.py running on this port?</span>' +
      '</div>';
  }
})();
