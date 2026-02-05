export interface ScenarioResult {
  id?: number;
  run_id?: string;
  scenario: string;
  npv_million: number;
  irr_pct: number;
  avg_dscr: number;
  min_dscr: number;
  llcr: number;
  payback_years: number;
  expected_loss_pct: number;
  npv_loss_million: number;
  debt_spread_bps: number;
  equity_premium_pct: number;
  crp_bps: number;
  climate_risk_premium_bps: number;
  wacc_baseline_pct: number;
  wacc_adjusted_pct: number;
  overall_rating: string;
  rating_numeric: number;
  spread_bps: number;
  is_investment_grade: boolean;
  is_distressed: boolean;
  capacity_rating: string;
  profitability_rating: string;
  coverage_rating: string;
  dscr_rating: string;
  net_debt_leverage_rating: string;
  equity_leverage_rating: string;
  asset_leverage_rating: string;
  capacity_mw: number;
  ebitda_to_fixed_assets: number;
  ebitda_to_interest: number;
  dscr: number;
  net_debt_to_ebitda: number;
  debt_to_equity: number;
  debt_to_assets: number;
  is_ebitda_negative: boolean;
  rating_rationale: string;
  counterfactual_rating: string;
  counterfactual_spread_bps: number;
  scenario_rating_new: string;
  scenario_spread_bps_new: number;
  rating_migration: string;
  notch_change: number;
  counterfactual_crp_bps: number;
}

export interface CashflowRow {
  id?: number;
  run_id?: string;
  scenario: string;
  year: number;
  revenue: number;
  fuel_costs: number;
  variable_opex: number;
  fixed_opex: number;
  outage_costs: number;
  total_costs: number;
  ebitda: number;
  depreciation: number;
  ebit: number;
  interest_expense: number;
  tax_expense: number;
  net_income: number;
  capex: number;
  free_cash_flow: number;
  capacity_factor: number;
}

export interface CreditRatingRow {
  id?: number;
  run_id?: string;
  scenario: string;
  display_name: string;
  year: number;
  dscr: number;
  rating: string;
  spread_bps: number;
  cost_of_debt: number;
  ebitda: number;
  debt_service: number;
}

export interface LiteratureReference {
  id?: number;
  paper_id: number;
  authors: string;
  year: number;
  title: string;
  journal: string;
  doi: string;
  key_finding: string;
  verified: boolean;
}

export interface ModelRun {
  id?: string;
  created_at?: string;
  git_hash: string;
  description: string;
}
