/* ---------------------------------------------------------------------
   Climate Risk Premium — synthetic model
   Mirrors the Python pipeline at a high level: takes plant params + scenario
   defs, returns scenarios (NPV, CRP, ratings), per-year cashflows, ratings,
   and physical-risk trajectories. Fully deterministic, no I/O.

   All domain constants are empty shells — populated at startup by
   initFromData(d) after app.jsx fetches /api/data from serve.py.
   Do NOT hardcode CSV values here; edit the source CSVs instead.
--------------------------------------------------------------------- */

const RATING_ORDER = ["AAA","AA","A","BBB","BB","B","CCC","CC","C","D"];

// --- Empty shells — populated by initFromData() before React mounts --------
const RATING_SPREADS      = {};    // ← data/credit/rating_spreads.csv
const DEFAULT_PLANT       = {};    // ← data/plant/plant_parameters.csv
const DEFAULT_TRANSITIONS = [];    // ← data/transition/scenarios.csv
const DEFAULT_PHYSICAL    = [];    // ← data/physical/scenarios.csv
const CLIMADA             = {};    // ← data/physical/climada_data.csv
const PHYSICAL_ASSUMPTIONS = {};   // ← data/physical/model_assumptions.csv
const WF_CLIMATE_FACTORS  = [];    // ← data/physical/literature_data.csv  WILDFIRE
const TC_CLIMATE_FACTORS  = [];    // ← data/physical/literature_data.csv  TC
const DR_CLIMATE_FACTORS  = [];    // ← data/physical/literature_data.csv  DROUGHT
const TEMP_CHANGE_SSP585  = [];    // ← data/physical/literature_data.csv  HEAT
const EFFICIENCY_PARAMS   = {};    // ← data/physical/literature_data.csv  EFFICIENCY
const HEATWAVE_PARAMS     = {};    // ← data/physical/literature_data.csv  HEATWAVE
const MODEL_ASSUMPTIONS   = {};    // ← data/assumptions/model_assumptions.csv
const RATING_SCORE_MODEL  = {};    // ← data/credit/rating_score_model.csv

// --- Composition logic — IDs must match server-returned transitions/physical --
// DEFAULT_CLIMATE_SCENARIOS is pairing logic, not domain parameters.
// It does not change when CSVs change, so it stays static here.
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

// ---------------------------------------------------------------------------
// initFromData — called once by app.jsx after GET /api/data succeeds.
// Mutates const shells in-place so all existing references remain valid.
// ---------------------------------------------------------------------------
function initFromData(d) {
  Object.assign(RATING_SPREADS,       d.rating_spreads);
  Object.assign(DEFAULT_PLANT,        d.plant);
  Object.assign(CLIMADA,              d.climada);
  Object.assign(PHYSICAL_ASSUMPTIONS, d.physical_assumptions);
  Object.assign(EFFICIENCY_PARAMS,    d.efficiency_params);
  Object.assign(HEATWAVE_PARAMS,      d.heatwave_params);
  Object.assign(MODEL_ASSUMPTIONS,    d.model_assumptions);
  Object.assign(RATING_SCORE_MODEL,   d.rating_score_model);

  // Arrays — splice-replace keeps existing references valid
  const _swap = (arr, src) => { arr.length = 0; arr.push(...src); };
  _swap(DEFAULT_TRANSITIONS, d.transitions);
  _swap(DEFAULT_PHYSICAL,    d.physical_scenarios);
  _swap(WF_CLIMATE_FACTORS,  d.wf_climate_factors);
  _swap(TC_CLIMATE_FACTORS,  d.tc_climate_factors);
  _swap(DR_CLIMATE_FACTORS,  d.dr_climate_factors);
  _swap(TEMP_CHANGE_SSP585,  d.temp_change_ssp585);

  // Normalise JSON null thresholds → JS infinity sentinels so .find() comparisons work:
  //   descending >= tiers (dscr, coverage):  null → -Infinity (last catch-all row)
  //   ascending  <= tiers (equity_leverage): null → +Infinity (last catch-all row)
  ["dscr", "coverage"].forEach(key => {
    (RATING_SCORE_MODEL[key] || []).forEach(t => {
      if (t.threshold == null) t.threshold = -Infinity;
    });
  });
  (RATING_SCORE_MODEL.equity_leverage || []).forEach(t => {
    if (t.threshold == null) t.threshold = Infinity;
  });
}

// ---------------------------------------------------------------------------
// Carbon price interpolation
// ---------------------------------------------------------------------------

function carbonPrice(cp, year) {
  // cp = array of prices at MODEL_ASSUMPTIONS.carbon_price_years anchor points
  const xs = MODEL_ASSUMPTIONS.carbon_price_years;
  if (year <= xs[0]) return cp[0];
  if (year >= xs[xs.length - 1]) return cp[xs.length - 1];
  for (let i = 0; i < xs.length - 1; i++) {
    if (year >= xs[i] && year <= xs[i+1]) {
      const t = (year - xs[i]) / (xs[i+1] - xs[i]);
      return cp[i] + t * (cp[i+1] - cp[i]);
    }
  }
  return cp[xs.length - 1];
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function _linInterp(x, anchors) {
  // Piecewise linear; clamps to first/last value outside anchor range.
  if (x <= anchors[0][0]) return anchors[0][1];
  const last = anchors[anchors.length - 1];
  if (x >= last[0]) return last[1];
  for (let i = 0; i < anchors.length - 1; i++) {
    const [x0, y0] = anchors[i], [x1, y1] = anchors[i + 1];
    if (x >= x0 && x <= x1) return y0 + (y1 - y0) * (x - x0) / (x1 - x0);
  }
  return last[1];
}

function physicalAdjustment(phys, year) {
  const scale = phys ? phys.wildfire : 0;
  const A = PHYSICAL_ASSUMPTIONS;

  // --- Wildfire (climada_data.csv: 6 events / 20 yr = 0.30/yr) ---
  const wfFreq   = CLIMADA.wildfire_events / CLIMADA.wildfire_years;
  const wfBase   = wfFreq * A.outage_prob_wildfire * (A.outage_duration_wildfire / A.hours_per_year);
  const wfBaseTx = wfFreq * A.outage_prob_tc       * (A.outage_duration_tc       / A.hours_per_year);
  const wfScl    = 1 + (_linInterp(year, WF_CLIMATE_FACTORS) - 1) * scale;
  const outage   = wfBase   * wfScl;
  const tx       = wfBaseTx * wfScl;

  // --- Tropical cyclone (climada_data.csv: 5 damaging / 40 yr = 0.125/yr) ---
  const tcFreq   = CLIMADA.tc_damaging_events / CLIMADA.tc_damaging_years;
  const tcBase   = tcFreq * A.outage_prob_tc * (A.outage_duration_wildfire / A.hours_per_year);
  const tcBaseTx = tcFreq * A.outage_prob_tc * (A.outage_duration_tc       / A.hours_per_year);
  const tcScl    = 1 + (_linInterp(year, TC_CLIMATE_FACTORS) - 1) * scale;
  const tc_outage  = tcBase   * tcScl;
  const tc_tx      = tcBaseTx * tcScl;

  // --- Drought derate (model_assumptions.csv: base 0.5 %, ×2.4 for severe drought) ---
  const drScl   = 1 + (_linInterp(year, DR_CLIMATE_FACTORS) - 1) * scale;
  const sevMult = (phys && phys.id === "severe_drought") ? A.drought_severe_multiplier : 1;
  const derate  = A.drought_capacity_derate_base * drScl * sevMult;

  // --- Chronic heat + SST (literature_data.csv EFFICIENCY rows) ---
  const E = EFFICIENCY_PARAMS;
  const effPerC    = (E.ambient_derate_model + E.sst_air_ratio * E.cooling_water_derate) / 100;
  const deltaT     = _linInterp(year, TEMP_CHANGE_SSP585) * scale;
  const chronicEff = deltaT * effPerC;

  // --- Heatwave acute (literature_data.csv HEATWAVE rows) ---
  const H     = HEATWAVE_PARAMS;
  const hwT   = Math.max(0, Math.min(1, (year - H.year_baseline) / (H.year_future - H.year_baseline)));
  const hwDays = H.days_baseline + (H.days_future - H.days_baseline) * hwT * scale;
  const hwEff  = (hwDays / PHYSICAL_ASSUMPTIONS.days_per_year) * (H.efficiency_loss / 100);

  const efficiency = chronicEff + hwEff;

  return { outage, tx, tc_outage, tc_tx, derate, efficiency, chronicEff, hwEff };
}

function ratingFromMetrics(avgEbitda, dscr, debtToEquity, ebitdaToInterest, capacityMw, consecutiveLossYears, cumulativeEbitdaMillion) {
  // Floor overrides — all thresholds from data/credit/rating_score_model.csv
  const M = MODEL_ASSUMPTIONS;
  const RS = RATING_SCORE_MODEL;
  if (cumulativeEbitdaMillion < 0) return "D";
  if (consecutiveLossYears >= M.consecutive_loss_years_d) return "D";
  if (avgEbitda <= 0) return "C";

  // Score buckets — base score and all deltas from RATING_SCORE_MODEL (rating_score_model.csv)
  let score = M.rating_base_score;

  // DSCR — use first matching threshold (descending order)
  const dscrTier = RS.dscr.find(t => dscr >= t.threshold);
  score += dscrTier ? dscrTier.delta : RS.dscr[RS.dscr.length - 1].delta;

  // EBITDA / interest — use first matching threshold (descending order)
  const covTier = RS.coverage.find(t => ebitdaToInterest >= t.threshold);
  score += covTier ? covTier.delta : RS.coverage[RS.coverage.length - 1].delta;

  // Debt / equity — use first matching threshold (ascending, <=)
  const levTier = RS.equity_leverage.find(t => debtToEquity <= t.threshold);
  score += levTier ? levTier.delta : RS.equity_leverage[RS.equity_leverage.length - 1].delta;

  // Scale bonus
  if (capacityMw >= RS.scale_threshold_mw) score += RS.scale_bonus;

  // Map score → rating using cutoffs (descending; first match wins)
  const cutoff = RS.cutoffs.find(c => score >= c.score);
  return cutoff ? cutoff.rating : "C";
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
    // Combined CF reduction: wildfire + TC (independent) + drought derate.
    // Independent formula: 1−(1−wf_plant)(1−tc_plant)·… ≈ sum for small rates.
    const cfRedFromPhysical = phyAdj.outage + phyAdj.tc_outage + phyAdj.tx + phyAdj.tc_tx + phyAdj.derate;
    const effLoss = phyAdj.efficiency;

    const cf = Math.max(0, plant.capacity_factor * (1 - transition.dispatch) * (1 - cfRedFromPhysical));
    const mwh = plant.capacity_mw * cf * PHYSICAL_ASSUMPTIONS.hours_per_year;
    const heatRatePenalty = 1 + effLoss;
    const revenue     = mwh * plant.power_price_per_mwh;
    // Fuel cost derived from components — matches Python cashflow.py exactly.
    const fuelCostPerMwh = plant.heat_rate_mmbtu_per_mwh * plant.fuel_price_per_mmbtu;
    const fuel        = mwh * fuelCostPerMwh * heatRatePenalty;
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
    // Levered FCF = Net income + Depreciation = EBITDA - interest - tax
    // Negative in early high-debt years (debt service > EBITDA), smoothly
    // improves as principal amortises, equals ~EBITDA post-payoff. No cliff.
    const fcf            = netIncome + depreciationUSD;

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
  const ebitdaToInterest = avgInterest > 0 ? avgEbitda / avgInterest : MODEL_ASSUMPTIONS.coverage_infinity_sentinel;

  const overallRating = ratingFromMetrics(
    avgEbitda, avgDscr, debtToEquity, ebitdaToInterest, plant.capacity_mw,
    totalLossYears, cumulativeEbitda / 1e6
  );
  const spreadBps = RATING_SPREADS[overallRating];

  // CRP vs counterfactual — all parameters from data/assumptions/model_assumptions.csv
  const M = MODEL_ASSUMPTIONS;
  const counterfactualRating  = M.counterfactual_rating;
  const counterfactualSpread  = RATING_SPREADS[counterfactualRating];
  const baseEquity            = M.baseline_equity_rate;
  const equityNotchPenalty    = M.equity_premium_per_notch
    * Math.max(0, RATING_ORDER.indexOf(overallRating) - RATING_ORDER.indexOf(counterfactualRating));
  const waccBaseline = (plant.debt_fraction * (M.base_rate + counterfactualSpread / 1e4) +
                       plant.equity_fraction * baseEquity) * 100;
  const waccAdjusted = (plant.debt_fraction * (M.base_rate + spreadBps / 1e4) +
                       plant.equity_fraction * (baseEquity + equityNotchPenalty)) * 100;
  const crpBps = (waccAdjusted - waccBaseline) * 100;

  // Year-by-year ratings
  const yearlyRatings = out.map((r, i) => {
    const ebitdaTrailing = out.slice(Math.max(0, i - 2), i + 1)
      .reduce((a, x) => a + x.ebitda, 0) / Math.min(3, i + 1);
    const consec = r.consecutive_loss_years;
    const dscrLocal = isFinite(r.dscr) ? r.dscr : MODEL_ASSUMPTIONS.dscr_post_debt_fallback;
    const interestLocal = r.interest_expense > 0 ? ebitdaTrailing / r.interest_expense : MODEL_ASSUMPTIONS.coverage_infinity_sentinel;
    const rating = ratingFromMetrics(
      ebitdaTrailing, dscrLocal, debtToEquity, interestLocal, plant.capacity_mw, consec, r.cumulative_ebitda / 1e6
    );
    return {
      year: r.year, rating, dscr: r.dscr, ebitda: r.ebitda,
      spread_bps: RATING_SPREADS[rating],
      cost_of_debt: MODEL_ASSUMPTIONS.base_rate + RATING_SPREADS[rating] / 1e4,
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

// Initial run for dashboard startup
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
  CLIMADA, PHYSICAL_ASSUMPTIONS, MODEL_ASSUMPTIONS, EFFICIENCY_PARAMS, HEATWAVE_PARAMS,
  WF_CLIMATE_FACTORS, TC_CLIMATE_FACTORS, DR_CLIMATE_FACTORS, TEMP_CHANGE_SSP585,
  RATING_SCORE_MODEL,
  initFromData,
  carbonPrice, physicalAdjustment, _linInterp, ratingFromMetrics,
  computeScenario, runModel, defaultModel, buildModel,
  fmtNum, fmtPct, niceTicks,
});
