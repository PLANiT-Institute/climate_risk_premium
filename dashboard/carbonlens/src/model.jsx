/* ---------------------------------------------------------------------
   Climate Risk Premium — synthetic model
   Mirrors the Python pipeline at a high level: takes plant params + scenario
   defs, returns scenarios (NPV, CRP, ratings), per-year cashflows, ratings,
   and physical-risk trajectories. Fully deterministic, no I/O.
--------------------------------------------------------------------- */

const RATING_ORDER = ["AAA","AA","A","BBB","BB","B","CCC","CC","C","D"];
const RATING_SPREADS = {
  AAA: 50, AA: 100, A: 150, BBB: 250, BB: 400, B: 600,
  CCC: 900, CC: 1500, C: 2500, D: 5000,
};

const DEFAULT_PLANT = {
  name: "Samcheok Blue Power",
  capacity_mw: 2100,
  capacity_factor: 0.60,
  total_capex_million: 3550,
  debt_fraction: 0.80,
  equity_fraction: 0.20,
  debt_interest_rate: 0.05,
  debt_tenor_years: 20,
  operating_years: 40,
  useful_life: 30,
  depreciation_years: 20,
  discount_rate: 0.08,
  emissions_tco2_per_mwh: 0.82,
  power_price_per_mwh: 80,
  fuel_cost_per_mwh: 50.512,  // heat_rate(8.8 MMBtu/MWh) × fuel_price($5.74/MMBtu)
  heat_rate_mmbtu_per_mwh: 8.8,
  fuel_price_per_mmbtu: 5.74,
  fixed_opex_per_kw: 35,
  variable_opex_per_mwh: 4.5,
  tax_rate: 0.25,
  inflation_rate: 0.02,
  start_year: 2025,
};

// Default transition scenarios — mirrors data/transition/scenarios.csv
const DEFAULT_TRANSITIONS = [
  { id:"baseline",              name:"Baseline",              dispatch:0.00, retire:40, cp:[8,20,40,60],     desc:"K-ETS inertia, current policy" },
  { id:"moderate_transition",   name:"Moderate Transition",   dispatch:0.10, retire:35, cp:[10,35,85,150],   desc:"K-ETS tightening" },
  { id:"korea_ndc",             name:"Korea NDC",             dispatch:0.15, retire:30, cp:[15,80,180,280],  desc:"NDC-aligned coal phase-down" },
  { id:"aggressive_transition", name:"Aggressive Transition", dispatch:0.25, retire:25, cp:[15,80,180,280],  desc:"Aggressive decarbonization" },
  { id:"net_zero_2050",         name:"Net Zero 2050",         dispatch:0.20, retire:25, cp:[20,110,260,450], desc:"Net Zero 2050 trajectory" },
  { id:"delayed_transition",    name:"Delayed Transition",    dispatch:0.05, retire:40, cp:[8,25,100,200],   desc:"Delayed action, late catch-up" },
  { id:"high_ambition",         name:"High Ambition",         dispatch:0.30, retire:20, cp:[40,185,420,600], desc:"1.5°C aligned" },
  { id:"no_carbon_baseline",    name:"No-Carbon (Counterfactual)", dispatch:0.00, retire:40, cp:[0,0,0,0], desc:"Hypothetical no carbon pricing" },
];

const DEFAULT_PHYSICAL = [
  { id:"baseline",          name:"Baseline (SSP1-2.6)",       wildfire:0.30, color:"#22c55e" },
  { id:"moderate_physical", name:"Moderate (SSP2-4.5)",       wildfire:0.60, color:"#f59e0b" },
  { id:"high_physical",     name:"High (SSP5-8.5)",           wildfire:1.00, color:"#ef4444" },
  { id:"severe_drought",    name:"Severe Drought (SSP5-8.5)", wildfire:1.00, color:"#7c3aed" },
];

const DEFAULT_CLIMATE_SCENARIOS = [
  { id:"no_risk_baseline",   name:"No-Risk Baseline",      transition:"no_carbon_baseline",    physical:"baseline",          desc:"Counterfactual: no carbon + low warming" },
  { id:"conservative",       name:"Conservative",          transition:"baseline",              physical:"baseline",          desc:"K-ETS inertia + low warming" },
  { id:"moderate",           name:"Moderate",              transition:"moderate_transition",   physical:"moderate_physical", desc:"K-ETS tighten + mid warming" },
  { id:"korea_ndc",          name:"Korea NDC",             transition:"korea_ndc",             physical:"moderate_physical", desc:"NDC + moderate physical" },
  { id:"net_zero_high",      name:"Net Zero × High",       transition:"net_zero_2050",         physical:"high_physical",     desc:"Net Zero 2050 + worst-case warming" },
  { id:"aggressive_severe",  name:"Aggressive × Severe",   transition:"aggressive_transition", physical:"severe_drought",    desc:"Aggressive + severe drought" },
  { id:"delayed_moderate",   name:"Delayed × Moderate",    transition:"delayed_transition",    physical:"moderate_physical", desc:"Late policy + moderate warming" },
  { id:"high_ambition_high", name:"High Ambition × High",  transition:"high_ambition",         physical:"high_physical",     desc:"1.5°C + worst-case physical" },
];

function carbonPrice(cp, year) {
  // cp = [2025, 2030, 2040, 2050]
  const xs = [2025, 2030, 2040, 2050];
  if (year <= xs[0]) return cp[0];
  if (year >= xs[3]) return cp[3];
  for (let i = 0; i < 3; i++) {
    if (year >= xs[i] && year <= xs[i+1]) {
      const t = (year - xs[i]) / (xs[i+1] - xs[i]);
      return cp[i] + t * (cp[i+1] - cp[i]);
    }
  }
  return cp[3];
}

function physicalAdjustment(phys, year) {
  // SSP-style scaling — increases roughly with year, scaled by `wildfire`
  const t = Math.max(0, year - 2025) / 75; // 0..1 by 2100
  const scale = phys ? phys.wildfire : 0;
  // Sigmoid for nonlinear acceleration
  const sig = 1 / (1 + Math.exp(-(t * 6 - 2.5)));
  const outage = scale * sig * 0.012;          // up to ~1.2% by 2100 at SSP585
  const tx = scale * sig * 0.006;
  const derate = scale * sig * 0.018 * (phys && phys.id === "severe_drought" ? 2.4 : 1);
  const efficiency = scale * sig * 0.005;
  return { outage, tx, derate, efficiency };
}

function ratingFromMetrics(avgEbitda, dscr, debtToEquity, ebitdaToInterest, capacityMw, consecutiveLossYears, cumulativeEbitdaMillion) {
  // Floor at D when cumulative EBITDA negative — matches Python
  if (cumulativeEbitdaMillion < 0) return "D";
  if (consecutiveLossYears >= 8) return "D";
  if (avgEbitda <= 0) return "C";

  // Score buckets (0..100, higher = better)
  let score = 60;
  // DSCR (28% weight)
  if (dscr >= 2.5) score += 18;
  else if (dscr >= 1.8) score += 12;
  else if (dscr >= 1.4) score += 6;
  else if (dscr >= 1.2) score -= 0;
  else if (dscr >= 1.0) score -= 8;
  else if (dscr >= 0.5) score -= 22;
  else score -= 35;

  // EBITDA / interest (12%)
  if (ebitdaToInterest >= 12) score += 6;
  else if (ebitdaToInterest >= 6) score += 3;
  else if (ebitdaToInterest >= 4) score += 0;
  else if (ebitdaToInterest >= 2) score -= 4;
  else score -= 10;

  // Debt / equity (20%)
  if (debtToEquity <= 80) score += 6;
  else if (debtToEquity <= 150) score += 3;
  else if (debtToEquity <= 250) score += 0;
  else if (debtToEquity <= 400) score -= 5;
  else score -= 12;

  // Scale (15%) — fixed 2100MW = AAA tier
  if (capacityMw >= 2000) score += 4;

  // Map score → rating
  if (score >= 92) return "AAA";
  if (score >= 82) return "AA";
  if (score >= 72) return "A";
  if (score >= 62) return "BBB";
  if (score >= 52) return "BB";
  if (score >= 42) return "B";
  if (score >= 30) return "CCC";
  if (score >= 18) return "CC";
  return "C";
}

function computeScenario(plant, transition, physical, opts = {}) {
  const startYear = plant.start_year;
  const years = transition.retire;
  const out = [];

  // All monetary values in raw USD throughout — no mixed-unit conversions.
  const debtUSD        = plant.total_capex_million * 1e6 * plant.debt_fraction;
  const principalUSD   = debtUSD / plant.debt_tenor_years;   // annual principal payment
  const depreciationUSD = plant.total_capex_million * 1e6 / plant.depreciation_years;

  let outstandingDebtUSD = debtUSD;
  let cumulativeEbitda = 0;
  let consecutiveLossYears = 0;

  for (let i = 0; i < years; i++) {
    const year = startYear + i;
    const phyAdj = physicalAdjustment(physical, year);
    const cfRedFromPhysical = phyAdj.outage + phyAdj.tx + phyAdj.derate;
    const effLoss = phyAdj.efficiency;

    const cf = Math.max(0, plant.capacity_factor * (1 - transition.dispatch) * (1 - cfRedFromPhysical));
    const mwh = plant.capacity_mw * cf * 8760;
    const heatRatePenalty = 1 + effLoss;
    const revenue     = mwh * plant.power_price_per_mwh;
    const fuel        = mwh * plant.fuel_cost_per_mwh * heatRatePenalty;
    const fixedOpex   = plant.capacity_mw * 1000 * plant.fixed_opex_per_kw;
    const variableOpex = mwh * plant.variable_opex_per_mwh;
    const cp          = carbonPrice(transition.cp, year);
    const carbonCost  = mwh * plant.emissions_tco2_per_mwh * cp;
    const totalCosts  = fuel + fixedOpex + variableOpex + carbonCost;
    const ebitda      = revenue - totalCosts;

    const inDebtPeriod   = i < plant.debt_tenor_years;
    const interestExpense = inDebtPeriod ? outstandingDebtUSD * plant.debt_interest_rate : 0;
    const principalPmt    = inDebtPeriod ? principalUSD : 0;
    const debtService     = interestExpense + principalPmt;

    const ebit           = ebitda - depreciationUSD;
    const taxableIncome  = Math.max(0, ebit - interestExpense);
    const tax            = taxableIncome * plant.tax_rate;
    const netIncome      = ebit - interestExpense - tax;
    // FCF = NOPAT + Depreciation  (maintenance capex = 0)
    const nopat          = ebit * (1 - plant.tax_rate);
    const fcf            = nopat + depreciationUSD;

    const cfads = ebitda - tax;
    const dscr  = debtService > 0 ? cfads / debtService : NaN;

    if (ebitda < 0) consecutiveLossYears++;
    else consecutiveLossYears = 0;
    cumulativeEbitda += ebitda;

    out.push({
      year, capacity_factor: cf, mwh, revenue, fuel, fixed_opex: fixedOpex,
      variable_opex: variableOpex, carbon_cost: carbonCost, total_costs: totalCosts,
      ebitda, depreciation: depreciationUSD, ebit, interest_expense: interestExpense,
      tax, net_income: netIncome, free_cash_flow: fcf, dscr, debt_service: debtService,
      cumulative_ebitda: cumulativeEbitda,
      consecutive_loss_years: consecutiveLossYears,
      carbon_price: cp,
      outage_rate: phyAdj.outage,
      capacity_derate: phyAdj.derate,
      efficiency_loss: phyAdj.efficiency,
    });
    if (inDebtPeriod) outstandingDebtUSD -= principalUSD;
  }

  // NPV
  let npv = -plant.total_capex_million * 1e6;
  for (let i = 0; i < out.length; i++) {
    npv += out[i].free_cash_flow / Math.pow(1 + plant.discount_rate, i + 1);
  }

  // Aggregate metrics
  const avgEbitda = out.reduce((a, r) => a + r.ebitda, 0) / out.length;
  const avgDscr = (() => {
    const valid = out.filter(r => !isNaN(r.dscr) && isFinite(r.dscr));
    return valid.length ? valid.reduce((a, r) => a + r.dscr, 0) / valid.length : 0;
  })();
  const minDscr = (() => {
    const valid = out.filter(r => !isNaN(r.dscr) && isFinite(r.dscr));
    return valid.length ? Math.min(...valid.map(r => r.dscr)) : 0;
  })();
  const llcr = (() => {
    let pv = 0;
    for (let i = 0; i < Math.min(plant.debt_tenor_years, out.length); i++) {
      pv += (out[i].ebitda - out[i].tax) / Math.pow(1 + plant.discount_rate, i + 1);
    }
    return debtUSD > 0 ? pv / debtUSD : 0;
  })();
  const totalCarbonCost = out.reduce((a, r) => a + r.carbon_cost, 0);
  const totalLossYears = out.filter(r => r.ebitda < 0).length;
  const avgInterest = out.reduce((a, r) => a + r.interest_expense, 0) / out.length;
  const debtToEquity = (plant.debt_fraction / plant.equity_fraction) * 100;
  const ebitdaToInterest = avgInterest > 0 ? avgEbitda / avgInterest : 99;

  const overallRating = ratingFromMetrics(
    avgEbitda, avgDscr, debtToEquity, ebitdaToInterest, plant.capacity_mw,
    totalLossYears, cumulativeEbitda / 1e6
  );
  const spreadBps = RATING_SPREADS[overallRating];

  // CRP vs counterfactual A
  const counterfactualSpread = RATING_SPREADS["A"];
  const baseEquity = 0.12;
  const equityNotchPenalty = 0.005 * Math.max(0, RATING_ORDER.indexOf(overallRating) - RATING_ORDER.indexOf("A"));
  const waccBaseline = (plant.debt_fraction * (0.0675 + counterfactualSpread / 1e4) +
                       plant.equity_fraction * baseEquity) * 100;
  const waccAdjusted = (plant.debt_fraction * (0.0675 + spreadBps / 1e4) +
                       plant.equity_fraction * (baseEquity + equityNotchPenalty)) * 100;
  const crpBps = (waccAdjusted - waccBaseline) * 100;

  // Year-by-year ratings
  const yearlyRatings = out.map((r, i) => {
    const ebitdaTrailing = out.slice(Math.max(0, i - 2), i + 1)
      .reduce((a, x) => a + x.ebitda, 0) / Math.min(3, i + 1);
    const consec = r.consecutive_loss_years;
    const dscrLocal = isFinite(r.dscr) ? r.dscr : 1.5;
    const interestLocal = r.interest_expense > 0 ? ebitdaTrailing / r.interest_expense : 99;
    const rating = ratingFromMetrics(
      ebitdaTrailing, dscrLocal, debtToEquity, interestLocal, plant.capacity_mw, consec, r.cumulative_ebitda / 1e6
    );
    return {
      year: r.year, rating, dscr: r.dscr, ebitda: r.ebitda,
      spread_bps: RATING_SPREADS[rating],
      cost_of_debt: 0.0675 + RATING_SPREADS[rating] / 1e4,
    };
  });

  return {
    rows: out,
    npv_million: npv / 1e6,
    avg_ebitda_million: avgEbitda / 1e6,
    avg_dscr: avgDscr,
    min_dscr: minDscr,
    llcr,
    total_carbon_cost_million: totalCarbonCost / 1e6,
    overall_rating: overallRating,
    spread_bps: spreadBps,
    crp_bps: crpBps,
    wacc_baseline_pct: waccBaseline,
    wacc_adjusted_pct: waccAdjusted,
    yearly_ratings: yearlyRatings,
    debt_to_equity_pct: debtToEquity,
    ebitda_to_interest: ebitdaToInterest,
    irr_pct: estimateIRR(out, plant.total_capex_million * 1e6),
  };
}

function estimateIRR(rows, capex) {
  // Simple IRR via bisection
  const cf = [-capex, ...rows.map(r => r.free_cash_flow)];
  let lo = -0.5, hi = 1.0;
  const npvAt = (r) => cf.reduce((a, v, i) => a + v / Math.pow(1 + r, i), 0);
  if (npvAt(lo) * npvAt(hi) > 0) return null;
  for (let i = 0; i < 60; i++) {
    const mid = (lo + hi) / 2;
    if (npvAt(mid) > 0) lo = mid; else hi = mid;
  }
  return (lo + hi) / 2 * 100;
}

function runModel(plant, transitions, physicalDefs, climateScenarios, options = {}) {
  const trIdx = Object.fromEntries(transitions.map(t => [t.id, t]));
  const phIdx = Object.fromEntries(physicalDefs.map(p => [p.id, p]));

  const scenarios = climateScenarios.map(cs => {
    const tr = trIdx[cs.transition];
    const ph = phIdx[cs.physical];
    if (!tr) return null;
    const r = computeScenario(plant, tr, ph, options);
    return {
      id: cs.id, name: cs.name, desc: cs.desc,
      transition_id: cs.transition, physical_id: cs.physical,
      transition_name: tr.name, physical_name: ph ? ph.name : "—",
      dispatch_pct: tr.dispatch * 100, retirement_years: tr.retire,
      carbon_prices: tr.cp,
      ...r,
    };
  }).filter(Boolean);

  return { plant, transitions, physicalDefs, climateScenarios, scenarios };
}

// Initial run for dashboard  startup
function defaultModel() {
  return runModel(DEFAULT_PLANT, DEFAULT_TRANSITIONS, DEFAULT_PHYSICAL, DEFAULT_CLIMATE_SCENARIOS);
}

function buildModel(plant) {
  return runModel(plant || DEFAULT_PLANT, DEFAULT_TRANSITIONS, DEFAULT_PHYSICAL, DEFAULT_CLIMATE_SCENARIOS);
}

/* Formatters */
function fmtNum(v, opts = {}) {
  if (v == null || isNaN(v)) return "—";
  const digits = opts.digits != null ? opts.digits : 1;
  const abs = Math.abs(v);
  if (abs >= 1e9) return (v / 1e9).toFixed(digits) + "B";
  if (abs >= 1e6 && opts.scaleM !== false) return v.toFixed(digits);
  return v.toLocaleString(undefined, { minimumFractionDigits: digits, maximumFractionDigits: digits });
}
function fmtPct(v, digits = 1) {
  if (v == null || isNaN(v)) return "—";
  return v.toFixed(digits) + "%";
}

/* Nice axis ticks */
function niceTicks(min, max, count = 5) {
  if (min === max) return [min];
  const range = max - min;
  const rough = range / count;
  const pow = Math.pow(10, Math.floor(Math.log10(rough)));
  const norm = rough / pow;
  let step;
  if (norm < 1.5) step = 1 * pow;
  else if (norm < 3) step = 2 * pow;
  else if (norm < 7) step = 5 * pow;
  else step = 10 * pow;
  const start = Math.ceil(min / step) * step;
  const ticks = [];
  for (let v = start; v <= max + 1e-9; v += step) ticks.push(Math.round(v / step) * step);
  return ticks;
}

Object.assign(window, {
  RATING_ORDER, RATING_SPREADS,
  DEFAULT_PLANT, DEFAULT_TRANSITIONS, DEFAULT_PHYSICAL, DEFAULT_CLIMATE_SCENARIOS,
  carbonPrice, physicalAdjustment, ratingFromMetrics,
  computeScenario, runModel, defaultModel, buildModel,
  fmtNum, fmtPct, niceTicks,
});
