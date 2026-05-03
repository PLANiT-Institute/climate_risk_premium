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

function App() {
  const [model, setModel] = uS(() => buildModel(DEFAULT_PLANT));
  const [screen, setScreen] = uS("overview");
  const [pending, setPending] = uS({});
  const [inspector, setInspector] = uS(null);
  const [theme, setTheme] = uS(localStorage.getItem("ksl_theme") || "dark");
  const [accent, setAccent] = uS(localStorage.getItem("ksl_accent") || "amber");

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

  const onCommitScenario = (custom) => {
    alert("Custom scenario saved: " + custom.name + "\n(Demo — would append to scenarios list.)");
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
            {screen === "overview"    && <ScreenOverview model={model} onEdit={onEdit} />}
            {screen === "scenarios"   && <ScreenScenarios model={model} />}
            {screen === "cashflows"   && <ScreenCashflows model={model} />}
            {screen === "credit"      && <ScreenCredit model={model} />}
            {screen === "physical"    && <ScreenPhysical model={model} />}
            {screen === "decomp"      && <ScreenDecomp model={model} />}
            {screen === "pipeline"    && <ScreenPipeline model={model} />}
            {screen === "builder"     && <ScreenBuilder model={model} onCommit={onCommitScenario} />}
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

ReactDOM.createRoot(document.getElementById("root")).render(<App />);
