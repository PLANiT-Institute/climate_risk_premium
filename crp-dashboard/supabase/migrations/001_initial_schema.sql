-- CRP Dashboard Schema
-- Run this in Supabase SQL editor

-- Model Runs
CREATE TABLE IF NOT EXISTS model_runs (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  created_at TIMESTAMPTZ DEFAULT now(),
  git_hash TEXT NOT NULL,
  description TEXT
);

-- Scenario Results (from scenario_comparison.csv)
CREATE TABLE IF NOT EXISTS scenario_results (
  id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  run_id UUID REFERENCES model_runs(id),
  scenario TEXT NOT NULL,
  npv_million DOUBLE PRECISION,
  irr_pct DOUBLE PRECISION,
  avg_dscr DOUBLE PRECISION,
  min_dscr DOUBLE PRECISION,
  llcr DOUBLE PRECISION,
  payback_years DOUBLE PRECISION,
  expected_loss_pct DOUBLE PRECISION,
  npv_loss_million DOUBLE PRECISION,
  debt_spread_bps DOUBLE PRECISION,
  equity_premium_pct DOUBLE PRECISION,
  crp_bps DOUBLE PRECISION,
  climate_risk_premium_bps DOUBLE PRECISION,
  wacc_baseline_pct DOUBLE PRECISION,
  wacc_adjusted_pct DOUBLE PRECISION,
  overall_rating TEXT,
  rating_numeric INTEGER,
  spread_bps DOUBLE PRECISION,
  is_investment_grade BOOLEAN,
  is_distressed BOOLEAN,
  capacity_rating TEXT,
  profitability_rating TEXT,
  coverage_rating TEXT,
  dscr_rating TEXT,
  net_debt_leverage_rating TEXT,
  equity_leverage_rating TEXT,
  asset_leverage_rating TEXT,
  capacity_mw DOUBLE PRECISION,
  ebitda_to_fixed_assets DOUBLE PRECISION,
  ebitda_to_interest DOUBLE PRECISION,
  dscr DOUBLE PRECISION,
  net_debt_to_ebitda DOUBLE PRECISION,
  debt_to_equity DOUBLE PRECISION,
  debt_to_assets DOUBLE PRECISION,
  is_ebitda_negative BOOLEAN,
  rating_rationale TEXT,
  counterfactual_rating TEXT,
  counterfactual_spread_bps DOUBLE PRECISION,
  scenario_rating_new TEXT,
  scenario_spread_bps_new DOUBLE PRECISION,
  rating_migration TEXT,
  notch_change INTEGER,
  counterfactual_crp_bps DOUBLE PRECISION,
  UNIQUE(run_id, scenario)
);

-- Cashflow Timeseries
CREATE TABLE IF NOT EXISTS cashflow_timeseries (
  id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  run_id UUID REFERENCES model_runs(id),
  scenario TEXT NOT NULL,
  year INTEGER NOT NULL,
  revenue DOUBLE PRECISION,
  fuel_costs DOUBLE PRECISION,
  variable_opex DOUBLE PRECISION,
  fixed_opex DOUBLE PRECISION,
  outage_costs DOUBLE PRECISION,
  total_costs DOUBLE PRECISION,
  ebitda DOUBLE PRECISION,
  depreciation DOUBLE PRECISION,
  ebit DOUBLE PRECISION,
  interest_expense DOUBLE PRECISION,
  tax_expense DOUBLE PRECISION,
  net_income DOUBLE PRECISION,
  capex DOUBLE PRECISION,
  free_cash_flow DOUBLE PRECISION,
  capacity_factor DOUBLE PRECISION,
  UNIQUE(run_id, scenario, year)
);

-- Credit Rating Trajectories
CREATE TABLE IF NOT EXISTS credit_rating_trajectories (
  id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  run_id UUID REFERENCES model_runs(id),
  scenario TEXT NOT NULL,
  display_name TEXT,
  year INTEGER NOT NULL,
  dscr DOUBLE PRECISION,
  rating TEXT,
  spread_bps DOUBLE PRECISION,
  cost_of_debt DOUBLE PRECISION,
  ebitda DOUBLE PRECISION,
  debt_service DOUBLE PRECISION,
  UNIQUE(run_id, scenario, year)
);

-- Literature References
CREATE TABLE IF NOT EXISTS literature_references (
  id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  paper_id INTEGER NOT NULL,
  authors TEXT NOT NULL,
  year INTEGER NOT NULL,
  title TEXT NOT NULL,
  journal TEXT,
  doi TEXT,
  key_finding TEXT,
  verified BOOLEAN DEFAULT true,
  UNIQUE(paper_id)
);

-- Row Level Security
ALTER TABLE model_runs ENABLE ROW LEVEL SECURITY;
ALTER TABLE scenario_results ENABLE ROW LEVEL SECURITY;
ALTER TABLE cashflow_timeseries ENABLE ROW LEVEL SECURITY;
ALTER TABLE credit_rating_trajectories ENABLE ROW LEVEL SECURITY;
ALTER TABLE literature_references ENABLE ROW LEVEL SECURITY;

-- Public read access
CREATE POLICY "Public read model_runs" ON model_runs FOR SELECT USING (true);
CREATE POLICY "Public read scenario_results" ON scenario_results FOR SELECT USING (true);
CREATE POLICY "Public read cashflow_timeseries" ON cashflow_timeseries FOR SELECT USING (true);
CREATE POLICY "Public read credit_rating_trajectories" ON credit_rating_trajectories FOR SELECT USING (true);
CREATE POLICY "Public read literature_references" ON literature_references FOR SELECT USING (true);

-- Indexes for common queries
CREATE INDEX idx_scenario_results_scenario ON scenario_results(scenario);
CREATE INDEX idx_cashflow_scenario_year ON cashflow_timeseries(scenario, year);
CREATE INDEX idx_ratings_scenario_year ON credit_rating_trajectories(scenario, year);
