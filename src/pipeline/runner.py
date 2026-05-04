"""Class-based orchestration for CRP runs using CSV inputs and CSV/plot outputs."""
from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Any, List, Optional

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

from src.data import load_inputs, get_param_value
from src.scenarios import TransitionScenario, PhysicalScenario, MarketScenario
from src.risk import (
    TransitionAdjustments, apply_transition,
    map_expected_loss_to_spreads, calculate_expected_loss, FinancingImpact,
    assess_credit_rating, calculate_rating_metrics_from_financials, RatingAssessment,
    calculate_financing_from_rating
)
from src.risk.credit_rating import (
    assess_rating_with_counterfactual,
    get_counterfactual_baseline_rating,
    Rating
)
from src.risk.financing import calculate_financing_with_counterfactual
from src.risk.attribution import decompose_risk_shapley
from src.financials import compute_cashflows_timeseries, calculate_metrics, CashFlowTimeSeries, FinancialMetrics
from src.scenarios.korea_power_plan import load_korea_power_plan_scenarios
from src.risk.physical import PhysicalAdjustments, load_yearly_from_output_csv, YearlyPhysicalAdjustments
from src.planit import PLANiTRunner, PLANiTAdapter, PLANiTIntegrationConfig

# Conditional import for enhanced 11th Basic Plan
try:
    from src.scenarios.enhanced_korea_power_plan import create_enhanced_11th_plan
    ENHANCED_PLAN_AVAILABLE = True
except ImportError:
    ENHANCED_PLAN_AVAILABLE = False
    create_enhanced_11th_plan = None


# CRP physical scenario → PLANiT SSP + target year
PHYSICAL_SCENARIO_SSP_MAP: Dict[str, tuple] = {
    "baseline": ("ssp126", 2024),
    "moderate_physical": ("ssp245", 2040),
    "high_physical": ("ssp585", 2040),
    "severe_drought": ("ssp585", 2050),
}


@dataclass
class RiskComponentResult:
    """Independent result for a single risk factor."""
    risk_type: str  # "baseline" | "transition_only" | "physical_only" | "combined"
    cashflow: CashFlowTimeSeries
    metrics: FinancialMetrics
    credit_rating: RatingAssessment | None
    crp_bps: float
    adjustments: Dict[str, Any]


@dataclass
class RiskAttribution:
    """Shapley-value risk attribution decomposition."""
    baseline_crp_bps: float
    transition_only_crp_bps: float
    physical_only_crp_bps: float
    combined_crp_bps: float
    transition_contribution_bps: float
    physical_contribution_bps: float
    interaction_effect_bps: float

    def to_dict(self) -> Dict[str, float]:
        return {
            "baseline_crp_bps": self.baseline_crp_bps,
            "transition_only_crp_bps": self.transition_only_crp_bps,
            "physical_only_crp_bps": self.physical_only_crp_bps,
            "combined_crp_bps": self.combined_crp_bps,
            "transition_contribution_bps": self.transition_contribution_bps,
            "physical_contribution_bps": self.physical_contribution_bps,
            "interaction_effect_bps": self.interaction_effect_bps,
        }


@dataclass
class ScenarioResult:
    """Results for a single scenario."""
    scenario_name: str
    cashflow: CashFlowTimeSeries
    metrics: FinancialMetrics
    financing: FinancingImpact | None = None  # Only for risk scenarios
    credit_rating: RatingAssessment | None = None  # Credit rating assessment
    counterfactual_crp: Dict[str, Any] | None = None  # Counterfactual-based CRP analysis
    risk_components: Dict[str, RiskComponentResult] | None = None
    risk_attribution: RiskAttribution | None = None


class CRPModelRunner:
    """
    Orchestrates loading CSV inputs, applying risk adjustments, and exporting outputs.
    """

    def __init__(self, base_dir: Path):
        self.base_dir = Path(base_dir)
        self.dataset = load_inputs(self.base_dir)
        self.power_plans = load_korea_power_plan_scenarios(self.base_dir / "data/raw/korea_power_plan.csv")
        # Default behavior remains CSV-backed. Set CRP_PLANIT_MODE=live to run PLANiT at runtime.
        self._planit_config = PLANiTIntegrationConfig()
        self._planit_results = self._load_planit_results()
        self._planit_adapter = PLANiTAdapter(self._planit_config)

    def _load_planit_results(self) -> List[Any]:
        """Load PLANiT hazard results.

        Modes:
        - csv  (default): read pre-computed CSV snapshots from Physicalrisk_PLANiT/data/results
        - live          : call PLANiT runtime (CLIMADA/PhysRisk) and backfill gaps from csv snapshots
        """
        mode = os.getenv("CRP_PLANIT_MODE", "live").strip().lower()
        if mode == "live":
            live_results = self._load_planit_results_live()
            if live_results:
                if self._is_dynamic_planit_location():
                    logger.info(
                        "Using live PLANiT runtime results for dynamic location (rows=%d, no CSV backfill)",
                        len(live_results),
                    )
                    return live_results
                csv_results = self._load_planit_results_csv()
                merged = self._merge_planit_results(live_results, csv_results)
                logger.info(
                    "Using live PLANiT runtime results with CSV backfill (live=%d, csv=%d, merged=%d)",
                    len(live_results), len(csv_results), len(merged),
                )
                return merged
            if self._is_dynamic_planit_location():
                logger.warning("Live PLANiT returned no results for dynamic location; returning empty set.")
                return []
            logger.warning("Live PLANiT returned no results; falling back to CSV snapshots.")
        return self._load_planit_results_csv()

    def _load_planit_results_csv(self) -> List[Any]:
        """Load pre-computed PLANiT CSV snapshots."""
        results_dir = str(self._planit_config.get_results_dir(str(self.base_dir)))
        results = PLANiTRunner.load_results_from_csv(results_dir)
        logger.info("Loaded PLANiT CSV results (%d rows) from %s", len(results), results_dir)
        return results

    def _load_planit_results_live(self) -> List[Any]:
        """Run PLANiT and return flattened hazard results.

        Optional environment variables:
        - CRP_PLANIT_SCENARIOS: comma-separated SSP ids, e.g. "ssp126,ssp245,ssp585"
        - CRP_PLANIT_YEARS: comma-separated years, e.g. "2030,2040,2050,2060"
        """
        scenarios = self._parse_planit_scenarios_env() or self._default_planit_scenarios()
        years = self._parse_planit_years_env()

        try:
            runner = PLANiTRunner(self._planit_config, base_dir=str(self.base_dir))
            by_hazard = runner.run_all_hazards(scenarios=scenarios, years=years)
            flattened = [r for rows in by_hazard.values() for r in rows]
            return flattened
        except Exception as exc:
            logger.warning("Live PLANiT run failed: %s", exc)
            return []

    @staticmethod
    def _default_planit_scenarios() -> List[str]:
        """Default live scenarios used by CRP physical pathways.

        Derived from CRP physical scenario mapping to avoid running
        unnecessary SSPs in live mode.
        """
        used = {ssp for ssp, _year in PHYSICAL_SCENARIO_SSP_MAP.values() if ssp != "historical"}
        return sorted(used)

    @staticmethod
    def _is_dynamic_planit_location() -> bool:
        return bool(os.getenv("CRP_PLANIT_LAT", "").strip() and os.getenv("CRP_PLANIT_LON", "").strip())

    @staticmethod
    def _merge_planit_results(live_results: List[Any], csv_results: List[Any]) -> List[Any]:
        """Merge live and csv PLANiT rows with live rows taking priority.

        Key fields are chosen so each hazard/scenario/year/asset has one row.
        """
        merged: Dict[tuple, Any] = {}
        for row in csv_results:
            key = (row.hazard_type, row.scenario, row.year, row.asset)
            merged[key] = row
        for row in live_results:
            key = (row.hazard_type, row.scenario, row.year, row.asset)
            merged[key] = row
        return list(merged.values())

    @staticmethod
    def _parse_planit_scenarios_env() -> Optional[List[str]]:
        raw = os.getenv("CRP_PLANIT_SCENARIOS", "").strip()
        if not raw:
            return None
        items = [s.strip().lower() for s in raw.split(",") if s.strip()]
        return items or None

    @staticmethod
    def _parse_planit_years_env() -> Optional[List[int]]:
        raw = os.getenv("CRP_PLANIT_YEARS", "").strip()
        if not raw:
            return None
        years: List[int] = []
        for token in raw.split(","):
            token = token.strip()
            if not token:
                continue
            try:
                years.append(int(token))
            except ValueError:
                logger.warning("Ignoring invalid CRP_PLANIT_YEARS token: %s", token)
        return years or None

    def _get_plant_params(self) -> Dict[str, Any]:
        """Extract plant parameters as a flat dict."""
        # dataset is a dict from load_all(): {'plant': PlantParameters, 'financing': ..., etc.}
        plant = self.dataset.get('plant') if isinstance(self.dataset, dict) else self.dataset.plant_params
        if hasattr(plant, 'to_dict'):
            return plant.to_dict()
        elif hasattr(plant, '__dict__'):
            return {k: v for k, v in plant.__dict__.items() if not k.startswith('_')}
        elif isinstance(plant, dict):
            return plant
        return {}

    def _get_financing_params(self) -> Dict[str, Any]:
        """Extract financing parameters."""
        financing = self.dataset.get('financing') if isinstance(self.dataset, dict) else self.dataset.financing_params
        if hasattr(financing, 'to_dict'):
            params = financing.to_dict()
        elif hasattr(financing, '__dict__'):
            params = {k: v for k, v in financing.__dict__.items() if not k.startswith('_')}
        elif isinstance(financing, dict):
            params = dict(financing)
        else:
            params = {}
        # Also add plant finance params (must come from CSV — raise if missing)
        plant_params = self._get_plant_params()
        params['debt_fraction'] = plant_params['debt_fraction']
        params['equity_fraction'] = plant_params['equity_fraction']
        return params

    def _load_transition_scenario(self, scenario_name: str) -> TransitionScenario:
        """
        Load transition scenario from CSV.
        """
        policy_scenarios = self.dataset.get('transition') if isinstance(self.dataset, dict) else self.dataset.policy_scenarios
        scenario_obj = policy_scenarios.get(scenario_name) if policy_scenarios else None

        # If we got a TransitionScenario object directly (from new data_loader), use it
        if scenario_obj is not None:
            # Data loader's TransitionScenario has dispatch_penalty, but src/scenarios uses dispatch_priority_penalty
            # Return a compatible scenario object
            return TransitionScenario(
                name=scenario_name,
                dispatch_priority_penalty=getattr(scenario_obj, 'dispatch_penalty', 0.0),
                retirement_years=getattr(scenario_obj, 'retirement_years', 40),
            )

        # Return default baseline scenario
        return TransitionScenario(
            name=scenario_name,
            dispatch_priority_penalty=0.0,
            retirement_years=40,
        )

    def _load_physical_scenario(self, scenario_name: str) -> PhysicalAdjustments:
        """Load physical scenario via PLANiT adapter.

        Maps CRP scenario names to SSP scenarios, then converts PLANiT
        hazard results (wildfire, drought, water_risk) into PhysicalAdjustments.
        """
        ssp, target_year = PHYSICAL_SCENARIO_SSP_MAP.get(
            scenario_name, ("ssp126", 2024)
        )

        # Map SSP back to CRP label for the adapter's scenario mapper
        ssp_to_crp = {"ssp126": "SSP1-2.6", "ssp245": "RCP4.5", "ssp585": "RCP8.5"}
        crp_label = ssp_to_crp.get(ssp, "SSP1-2.6")

        adj = self._planit_adapter.convert(
            self._planit_results, target_year, crp_label
        )
        return PhysicalAdjustments(
            outage_rate=adj["outage_rate"],
            capacity_derate=adj["capacity_derate"],
            efficiency_loss=adj["efficiency_loss"],
            water_constrained_capacity=adj["water_constrained_capacity"],
            notes=adj["notes"],
        )

    def _build_yearly_physical_from_planit(
        self, scenario_name: str, start_year: int, end_year: int
    ) -> Optional[YearlyPhysicalAdjustments]:
        """Build year-by-year physical adjustments from PLANiT adapter.

        Uses the PLANiT adapter to compute scenario-specific adjustments for
        each year, ensuring physical risk varies across scenarios.
        Falls back to load_yearly_from_output_csv() if PLANiT results are empty.
        """
        if not self._planit_results:
            logger.warning("No PLANiT results; building physical adjustments from hazard_baselines.csv × climate_factors.csv.")
            return self._build_yearly_from_baselines_csv(scenario_name, start_year, end_year)

        ssp, _target_year = PHYSICAL_SCENARIO_SSP_MAP.get(
            scenario_name, ("ssp126", 2024)
        )
        ssp_to_crp = {"ssp126": "SSP1-2.6", "ssp245": "RCP4.5", "ssp585": "RCP8.5"}
        crp_label = ssp_to_crp.get(ssp, "SSP1-2.6")

        all_years = np.arange(start_year, end_year + 1)
        outage_rates = np.zeros(len(all_years))
        capacity_derates = np.zeros(len(all_years))
        efficiency_losses = np.zeros(len(all_years))
        water_constraints = np.ones(len(all_years))

        for i, year in enumerate(all_years):
            adj = self._planit_adapter.convert(
                self._planit_results, int(year), crp_label
            )
            outage_rates[i] = adj["outage_rate"]
            capacity_derates[i] = adj["capacity_derate"]
            efficiency_losses[i] = adj["efficiency_loss"]
            water_constraints[i] = adj["water_constrained_capacity"]

        label = f"PLANiT {crp_label} ({scenario_name})"
        logger.info(
            "Built yearly physical adjustments from PLANiT: scenario=%s, years=%d-%d, "
            "avg_outage=%.6f, avg_derate=%.6f, avg_eff_loss=%.6f",
            label, start_year, end_year,
            outage_rates.mean(), capacity_derates.mean(), efficiency_losses.mean(),
        )

        return YearlyPhysicalAdjustments(
            years=all_years,
            outage_rates=outage_rates,
            capacity_derates=capacity_derates,
            efficiency_losses=efficiency_losses,
            water_constraints=water_constraints,
            scenario_name=label,
        )

    def _build_yearly_from_baselines_csv(
        self, scenario_name: str, start_year: int, end_year: int
    ) -> YearlyPhysicalAdjustments:
        """Build year-by-year adjustments from hazard_baselines.csv × climate_factors.csv.

        Channels populated for every scenario × year:
            outage_rate              = wildfire(plant) + tropical_cyclone(plant)
            capacity_derate          = drought.capacity_derate × cf("drought")
            efficiency_loss          = drought.eff_loss × cf("drought") + heat_stress.eff_loss × cf("heat_stress")
            water_constrained_capacity = 1.0 (only set when severe drought distribution available)
            transmission_outage_rate = wildfire(line) + typhoon(line) + heat_sag(line) + flood(substation)
            asset_capex_loss_rate    = annual replacement-value fraction (line corridor + plant damage_ratio)
        """
        from ..data.loaders import (
            get_climate_factor,
            load_hazard_baselines as _load_baselines,
        )
        from ..planit.vulnerability import (
            event_frequency_to_outage_rate,
            transmission_outage_rate as _trans_outage,
            substation_outage_rate as _sub_outage,
        )
        from ..planit.outage_model import load_outage_params, p_outage_given_event

        baselines = _load_baselines()
        line_params = (
            self.dataset.get('transmission') if isinstance(self.dataset, dict) else {}
        ) or {}

        ssp, _target_year = PHYSICAL_SCENARIO_SSP_MAP.get(scenario_name, ("ssp126", 2024))
        ssp_to_crp = {"ssp126": "SSP1-2.6", "ssp245": "RCP4.5", "ssp585": "RCP8.5"}
        crp_label = ssp_to_crp.get(ssp, "SSP1-2.6")

        years = np.arange(start_year, end_year + 1)
        n = len(years)
        plant_outage = np.zeros(n)
        capacity_derate = np.zeros(n)
        efficiency_loss = np.zeros(n)
        water_constraint = np.ones(n)
        line_outage = np.zeros(n)
        capex_loss = np.zeros(n)

        # Plant-level wildfire outage: exponential failure model.
        # P(outage|event) = 1 - exp(-λ×t), params from data/physical/outage_params.csv
        _outage_params = load_outage_params()
        _plant_params = _outage_params.get("power_plant", _outage_params.get("transmission_tower"))
        plant_wf_p = p_outage_given_event(_plant_params.failure_rate_per_hour, _plant_params.exposure_duration_hours) if _plant_params else 0.45
        plant_wf_dur = _plant_params.outage_duration_hours if _plant_params else 24.0

        wf = baselines.get("wildfire")
        tc = baselines.get("tropical_cyclone")
        dr = baselines.get("drought")
        hs = baselines.get("heat_stress")
        cf = baselines.get("coastal_flood")

        for i, yr in enumerate(years):
            yi = int(yr)
            # --- Plant-level outage: wildfire + tropical cyclone direct hits ---
            if wf is not None:
                wf_freq = wf.base_frequency * get_climate_factor("wildfire", yi, crp_label)
                plant_outage[i] += event_frequency_to_outage_rate(
                    wf_freq, plant_wf_p, plant_wf_dur
                )
            if tc is not None:
                # tropical_cyclone in hazard_baselines stores outage_rate directly; scale by cf
                tc_factor = get_climate_factor("tropical_cyclone", yi, crp_label)
                plant_outage[i] += tc.outage_rate * tc_factor

            # --- Capacity derate (drought) ---
            if dr is not None:
                dr_factor = get_climate_factor("drought", yi, crp_label)
                capacity_derate[i] = dr.capacity_derate * dr_factor

            # --- Efficiency loss (drought + heat stress) ---
            if dr is not None:
                efficiency_loss[i] += dr.efficiency_loss * get_climate_factor("drought", yi, crp_label)
            if hs is not None:
                efficiency_loss[i] += hs.efficiency_loss * get_climate_factor("heat_stress", yi, crp_label)

            # --- Transmission outage: wildfire + typhoon + heat-sag on line + substation flood ---
            wf_freq_line = wf.base_frequency * get_climate_factor("wildfire", yi, crp_label) if wf else 0.0
            tc_freq_line = tc.base_frequency * get_climate_factor("tropical_cyclone", yi, crp_label) if tc else 0.0
            heat_freq_line = hs.base_frequency * get_climate_factor("heat_stress", yi, crp_label) if hs else 0.0
            flood_freq = cf.base_frequency * get_climate_factor("coastal_flood", yi, crp_label) if cf else 0.0

            line_outage[i] = _trans_outage(wf_freq_line, tc_freq_line, heat_freq_line, line_params)
            line_outage[i] += _sub_outage(flood_freq, line_params)
            line_outage[i] = min(1.0, line_outage[i])

            # --- Asset capex loss (annual fraction destroyed) ---
            # Plant: damage_ratio per event × event_frequency, summed across hazards
            plant_loss = 0.0
            for h, name in [(wf, "wildfire"), (tc, "tropical_cyclone")]:
                if h is None:
                    continue
                f = get_climate_factor(name, yi, crp_label)
                plant_loss += h.damage_ratio * h.base_frequency * f
            # Line/substation: prebuilt fraction in transmission.csv
            line_loss = float(line_params.get("line_annual_damage_fraction", 0.0))
            # Scale line losses by an aggregate climate factor (use wildfire as bellwether)
            line_loss *= get_climate_factor("wildfire", yi, crp_label)
            capex_loss[i] = plant_loss + line_loss

        adj = YearlyPhysicalAdjustments(
            years=years,
            outage_rates=plant_outage,
            capacity_derates=capacity_derate,
            efficiency_losses=efficiency_loss,
            water_constraints=water_constraint,
            transmission_outage_rates=line_outage,
            asset_capex_loss_rates=capex_loss,
            scenario_name=f"hazard_baselines × climate_factor[{crp_label}]",
        )
        logger.info(
            "Physical adj %s (%s): plant_outage=%.6f line_outage=%.6f derate=%.6f eff_loss=%.6f capex_loss=%.6f",
            scenario_name, crp_label,
            plant_outage.mean(), line_outage.mean(), capacity_derate.mean(),
            efficiency_loss.mean(), capex_loss.mean(),
        )
        return adj

    def _save_physical_adjustments(
        self,
        physical_adj,
        yearly_physical_adj,
        scenario_name: str,
    ) -> None:
        """Save Path A (PhysicalAdjustments) and Path B (YearlyPhysicalAdjustments) to CSV."""
        import csv as _csv
        out_dir = self.base_dir / "data" / "physical_risk_steps" / "output"
        out_dir.mkdir(parents=True, exist_ok=True)
        safe_scenario = scenario_name.replace("/", "_").replace(" ", "_")

        # Path A: single-row CSV
        path_a_file = out_dir / f"physical_adj_pathA_{safe_scenario}.csv"
        with open(path_a_file, "w", newline="", encoding="utf-8") as f:
            writer = _csv.writer(f)
            writer.writerow(["field", "value"])
            writer.writerow(["outage_rate", physical_adj.outage_rate])
            writer.writerow(["capacity_derate", physical_adj.capacity_derate])
            writer.writerow(["efficiency_loss", physical_adj.efficiency_loss])
            writer.writerow(["water_constrained_capacity", physical_adj.water_constrained_capacity])
            writer.writerow(["transmission_outage_rate", physical_adj.transmission_outage_rate])
            writer.writerow(["asset_capex_loss_rate", physical_adj.asset_capex_loss_rate])
            writer.writerow(["notes", physical_adj.notes])
        logger.info("Saved Path A PhysicalAdjustments → %s", path_a_file)

        # Path B: year-by-year CSV (includes transmission + capex channels)
        path_b_file = out_dir / f"physical_adj_pathB_{safe_scenario}.csv"
        with open(path_b_file, "w", newline="", encoding="utf-8") as f:
            writer = _csv.writer(f)
            writer.writerow([
                "year", "plant_outage_rate", "capacity_derate", "efficiency_loss",
                "water_constrained_capacity", "transmission_outage_rate",
                "asset_capex_loss_rate",
            ])
            for i, yr in enumerate(yearly_physical_adj.years):
                writer.writerow([
                    int(yr),
                    yearly_physical_adj.outage_rates[i],
                    yearly_physical_adj.capacity_derates[i],
                    yearly_physical_adj.efficiency_losses[i],
                    yearly_physical_adj.water_constraints[i],
                    yearly_physical_adj.transmission_outage_rates[i],
                    yearly_physical_adj.asset_capex_loss_rates[i],
                ])
        logger.info("Saved Path B YearlyPhysicalAdjustments → %s", path_b_file)

    def _load_market_scenario(self, scenario_name: str) -> MarketScenario:
        """Load market scenario (demand/price)."""
        if scenario_name == "low_demand":
            return MarketScenario(name="low_demand", demand_growth_pct=-1.0, price_sensitivity=0.5)
        elif scenario_name == "high_demand":
            return MarketScenario(name="high_demand", demand_growth_pct=2.0, price_sensitivity=0.5)
        else:
            return MarketScenario(name="baseline", demand_growth_pct=0.0, price_sensitivity=0.5)

    def _compute_component(
        self,
        plant_params: Dict[str, Any],
        transition_scenario: TransitionScenario,
        transition_adj: TransitionAdjustments,
        physical_adj: PhysicalAdjustments,
        market_scenario: MarketScenario | None,
        risk_type: str,
        yearly_transition_adj=None,
        yearly_physical_adj=None,
    ) -> RiskComponentResult:
        """Run cashflow → metrics → rating → CRP for a single risk configuration."""
        cashflow = compute_cashflows_timeseries(
            plant_params,
            transition_scenario,
            transition_adj,
            physical_adj,
            market_scenario,
            yearly_transition_adj=yearly_transition_adj,
            yearly_physical_adj=yearly_physical_adj,
        )
        metrics = calculate_metrics(cashflow, plant_params)

        avg_ebitda = float(cashflow.ebitda.mean())
        capacity_mw = plant_params['capacity_mw']
        total_capex = plant_params['total_capex_million'] * 1e6
        debt_fraction = plant_params['debt_fraction']
        equity_fraction = plant_params['equity_fraction']
        debt_interest = plant_params['debt_interest_rate']

        fixed_assets = total_capex
        total_debt = total_capex * debt_fraction
        total_equity = total_capex * equity_fraction
        total_assets = total_capex
        interest_expense = total_debt * debt_interest
        cash_and_equivalents = avg_ebitda * 0.1

        rating_metrics = calculate_rating_metrics_from_financials(
            capacity_mw=capacity_mw,
            ebitda=avg_ebitda,
            fixed_assets=fixed_assets,
            interest_expense=interest_expense,
            total_debt=total_debt,
            cash_and_equivalents=cash_and_equivalents,
            total_equity=total_equity,
            total_assets=total_assets,
            dscr=metrics.avg_dscr,
        )

        credit_rating = assess_credit_rating(rating_metrics)
        counterfactual_result = assess_rating_with_counterfactual(rating_metrics)
        crp_bps = float(counterfactual_result.get("crp_bps", 0.0))

        adjustments = {
            "transition_cf": transition_adj.capacity_factor,
            "transition_years": transition_adj.operating_years,
            "physical_outage": physical_adj.outage_rate,
            "physical_derate": physical_adj.capacity_derate,
            "physical_efficiency_loss": physical_adj.efficiency_loss,
            "physical_water": physical_adj.water_constrained_capacity,
        }

        return RiskComponentResult(
            risk_type=risk_type,
            cashflow=cashflow,
            metrics=metrics,
            credit_rating=credit_rating,
            crp_bps=crp_bps,
            adjustments=adjustments,
        )

    def run_scenario(
        self,
        scenario_name: str,
        transition_scenario_name: str = "baseline",
        physical_scenario_name: str = "baseline",
        market_scenario_name: str = "baseline",
        power_plan_name: str | None = None,
        use_enhanced_korea_plan: bool = False,
        current_year: int | None = None,
        decompose: bool = False,
    ) -> ScenarioResult:
        """Run a single scenario.

        Args:
            decompose: If True, run 4 independent cashflow calculations
                (baseline, transition-only, physical-only, combined) and
                produce a Shapley-value risk attribution.
        """
        logger.info(
            "Running scenario '%s' (transition=%s, physical=%s, market=%s)",
            scenario_name, transition_scenario_name, physical_scenario_name, market_scenario_name,
        )
        plant_params = self._get_plant_params()

        transition_scenario = self._load_transition_scenario(transition_scenario_name)
        physical_adj = self._load_physical_scenario(physical_scenario_name)
        market_scenario = self._load_market_scenario(market_scenario_name)

        # Load Korea Power Plan if specified
        korea_plan = None
        if power_plan_name and power_plan_name in self.power_plans:
            korea_plan = self.power_plans[power_plan_name]

        # Load Enhanced 11th Basic Plan if requested
        enhanced_korea_scenario = None
        if use_enhanced_korea_plan and ENHANCED_PLAN_AVAILABLE:
            enhanced_korea_scenario = create_enhanced_11th_plan()

        transition_adj = apply_transition(
            plant_params,
            transition_scenario,
            korea_plan_scenario=korea_plan,
            enhanced_korea_scenario=enhanced_korea_scenario,
            current_year=current_year,
        )

        # Build yearly transition adjustments if enhanced plan available
        yearly_transition_adj = None
        if enhanced_korea_scenario is not None:
            from src.risk.transition import create_yearly_transition_adjustments
            start = int(plant_params.get("cod_year", 2025))
            yearly_transition_adj = create_yearly_transition_adjustments(
                plant_params, enhanced_korea_scenario,
                start_year=start,
                end_year=start + transition_adj.operating_years - 1,
                dispatch_priority_penalty=transition_scenario.dispatch_priority_penalty,
            )

        # Build yearly physical adjustments from PLANiT (scenario-aware)
        _phys_start = int(plant_params.get("cod_year", 2025))
        _phys_end = _phys_start + transition_adj.operating_years - 1
        yearly_physical_adj = self._build_yearly_physical_from_planit(
            physical_scenario_name, _phys_start, _phys_end
        )

        self._save_physical_adjustments(
            physical_adj, yearly_physical_adj, scenario_name
        )

        # --- Combined run (always performed, same as before) ---
        combined = self._compute_component(
            plant_params, transition_scenario, transition_adj, physical_adj,
            market_scenario, "combined",
            yearly_transition_adj=yearly_transition_adj,
            yearly_physical_adj=yearly_physical_adj,
        )

        # Build the primary ScenarioResult from the combined run
        cf_total_capex = plant_params['total_capex_million'] * 1e6
        cf_debt_fraction = plant_params['debt_fraction']
        cf_avg_ebitda = float(combined.cashflow.ebitda.mean())
        result = ScenarioResult(
            scenario_name=scenario_name,
            cashflow=combined.cashflow,
            metrics=combined.metrics,
            credit_rating=combined.credit_rating,
            counterfactual_crp=assess_rating_with_counterfactual(
                calculate_rating_metrics_from_financials(
                    capacity_mw=plant_params['capacity_mw'],
                    ebitda=cf_avg_ebitda,
                    fixed_assets=cf_total_capex,
                    interest_expense=cf_total_capex * cf_debt_fraction * plant_params['debt_interest_rate'],
                    total_debt=cf_total_capex * cf_debt_fraction,
                    cash_and_equivalents=cf_avg_ebitda * 0.1,
                    total_equity=cf_total_capex * plant_params['equity_fraction'],
                    total_assets=cf_total_capex,
                    dscr=combined.metrics.avg_dscr,
                )
            ),
        )

        if not decompose:
            return result

        # --- Decomposition: 3 additional runs ---

        # No-risk adjustments
        no_transition = TransitionAdjustments(
            capacity_factor=float(plant_params['capacity_factor']),
            operating_years=int(plant_params['operating_years']),
            notes="No transition risk (baseline)",
        )
        no_physical = PhysicalAdjustments(
            outage_rate=0.0,
            capacity_derate=0.0,
            efficiency_loss=0.0,
            water_constrained_capacity=1.0,
            notes="No physical risk (baseline)",
        )

        baseline = self._compute_component(
            plant_params, transition_scenario, no_transition, no_physical,
            market_scenario, "baseline",
        )
        transition_only = self._compute_component(
            plant_params, transition_scenario, transition_adj, no_physical,
            market_scenario, "transition_only",
        )
        physical_only = self._compute_component(
            plant_params, transition_scenario, no_transition, physical_adj,
            market_scenario, "physical_only",
            yearly_physical_adj=yearly_physical_adj,
        )

        # Shapley decomposition
        shapley = decompose_risk_shapley(
            baseline_crp=baseline.crp_bps,
            transition_only_crp=transition_only.crp_bps,
            physical_only_crp=physical_only.crp_bps,
            combined_crp=combined.crp_bps,
        )

        result.risk_components = {
            "baseline": baseline,
            "transition_only": transition_only,
            "physical_only": physical_only,
            "combined": combined,
        }
        result.risk_attribution = RiskAttribution(
            baseline_crp_bps=baseline.crp_bps,
            transition_only_crp_bps=transition_only.crp_bps,
            physical_only_crp_bps=physical_only.crp_bps,
            combined_crp_bps=combined.crp_bps,
            transition_contribution_bps=shapley["transition_contribution_bps"],
            physical_contribution_bps=shapley["physical_contribution_bps"],
            interaction_effect_bps=shapley["interaction_effect_bps"],
        )

        return result

    def run_multi_scenario(
        self,
        scenarios: List[Dict[str, str]] = None,
        decompose: bool = False,
    ) -> Dict[str, ScenarioResult]:
        """
        Run multiple scenarios and calculate financing impacts.

        Args:
            scenarios: List of dicts with keys: name, transition, physical
                      If None, runs default scenarios
        """
        if scenarios is None:
            scenarios = [
                # Baseline scenario (no transition risk, no physical risk)
                {"name": "baseline", "transition": "baseline", "physical": "baseline"},
                # Transition risk scenarios (dispatch penalties only, no carbon)
                {"name": "moderate_transition", "transition": "moderate_transition", "physical": "baseline"},
                {"name": "aggressive_transition", "transition": "aggressive_transition", "physical": "baseline"},
                # Physical risk scenarios
                {"name": "moderate_physical", "transition": "baseline", "physical": "moderate_physical"},
                {"name": "high_physical", "transition": "baseline", "physical": "high_physical"},
                # Combined scenarios
                {"name": "combined_moderate", "transition": "moderate_transition", "physical": "moderate_physical"},
                {"name": "combined_aggressive", "transition": "aggressive_transition", "physical": "high_physical"},
                # Additional scenarios
                {"name": "low_demand", "transition": "baseline", "physical": "baseline", "market": "low_demand"},
                {"name": "severe_drought", "transition": "baseline", "physical": "severe_drought", "market": "baseline"},
                # Enhanced 11th Basic Plan scenarios
                {"name": "enhanced_11th_plan", "transition": "moderate_transition", "physical": "baseline", "use_enhanced": True},
                {"name": "enhanced_combined", "transition": "moderate_transition", "physical": "moderate_physical", "use_enhanced": True},
            ]

        logger.info("Running %d scenarios (decompose=%s)", len(scenarios), decompose)
        results = {}
        baseline_result = None

        # Run all scenarios
        for i, scenario_spec in enumerate(scenarios, 1):
            market_name = scenario_spec.get("market", "baseline")
            power_plan_name = scenario_spec.get("power_plan", None)
            use_enhanced = scenario_spec.get("use_enhanced", False)

            try:
                result = self.run_scenario(
                    scenario_spec["name"],
                    scenario_spec["transition"],
                    scenario_spec.get("physical", "baseline"),
                    market_name,
                    power_plan_name,
                    use_enhanced_korea_plan=use_enhanced,
                    decompose=decompose,
                )
                results[scenario_spec["name"]] = result
                logger.info(
                    "[%d/%d] Scenario '%s' completed (NPV=%,.0f, IRR=%.2f%%)",
                    i, len(scenarios), scenario_spec["name"],
                    result.metrics.npv, result.metrics.irr * 100,
                )
            except Exception as exc:
                logger.error(
                    "[%d/%d] Scenario '%s' failed: %s",
                    i, len(scenarios), scenario_spec["name"], exc,
                )
                raise

            if scenario_spec["name"] == "baseline":
                baseline_result = result

        # Calculate financing impacts using counterfactual baseline
        plant_params = self._get_plant_params()
        financing_params = self._get_financing_params()
        total_capex = plant_params['total_capex_million'] * 1e6

        # Get counterfactual rating (A = no risk world)
        counterfactual_rating = get_counterfactual_baseline_rating()
        counterfactual_spread = counterfactual_rating.to_spread_bps()
        counterfactual_notch = counterfactual_rating.value

        for name, result in results.items():
            # Calculate counterfactual NPV loss
            counterfactual_npv = baseline_result.metrics.npv if baseline_result else result.metrics.npv
            npv_loss = counterfactual_npv - result.metrics.npv

            if result.credit_rating:
                scenario_spread = result.credit_rating.overall_rating.to_spread_bps()
                scenario_notch = result.credit_rating.overall_rating.value

                result.financing = calculate_financing_with_counterfactual(
                    scenario_spread_bps=scenario_spread,
                    counterfactual_spread_bps=counterfactual_spread,
                    npv_loss=max(0, npv_loss),  # Floor at 0
                    total_capex=total_capex,
                    params=financing_params,
                    scenario_notch=scenario_notch,
                    counterfactual_notch=counterfactual_notch,
                )
            else:
                # Fallback to old linear model if no rating (shouldn't happen)
                el_pct = calculate_expected_loss(counterfactual_npv, result.metrics.npv, total_capex)
                result.financing = map_expected_loss_to_spreads(el_pct, npv_loss, financing_params)

        return results

    def export_results(
        self,
        results: Dict[str, ScenarioResult],
        output_dir: Path,
    ) -> Dict[str, Path]:
        """Export scenario results to CSV files."""
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        paths = {}

        # Export cashflow time series for each scenario
        for name, result in results.items():
            cf_df = pd.DataFrame(result.cashflow.to_dict())
            cf_path = output_dir / f"cashflow_{name}.csv"
            cf_df.to_csv(cf_path, index=False)
            paths[f"cashflow_{name}"] = cf_path

        # Export summary metrics
        metrics_rows = []
        for name, result in results.items():
            row = {"scenario": name}
            row.update(result.metrics.to_dict())
            if result.financing:
                row.update(result.financing.to_dict())
            if result.credit_rating:
                row.update(result.credit_rating.to_dict())
            # Add counterfactual CRP data
            if result.counterfactual_crp:
                row["counterfactual_rating"] = result.counterfactual_crp.get("counterfactual_rating")
                row["counterfactual_spread_bps"] = result.counterfactual_crp.get("counterfactual_spread_bps")
                row["scenario_rating_new"] = result.counterfactual_crp.get("scenario_rating")
                row["scenario_spread_bps_new"] = result.counterfactual_crp.get("scenario_spread_bps")
                row["rating_migration"] = result.counterfactual_crp.get("rating_migration")
                row["notch_change"] = result.counterfactual_crp.get("notch_change")
                row["counterfactual_crp_bps"] = result.counterfactual_crp.get("crp_bps")
                row["is_investment_grade"] = result.counterfactual_crp.get("is_investment_grade")
                row["is_distressed"] = result.counterfactual_crp.get("is_distressed")
            metrics_rows.append(row)

        metrics_df = pd.DataFrame(metrics_rows)
        metrics_path = output_dir / "scenario_comparison.csv"
        metrics_df.to_csv(metrics_path, index=False)
        paths["scenario_comparison"] = metrics_path

        # Export credit rating summary
        rating_rows = []
        for name, result in results.items():
            if result.credit_rating:
                row = {"scenario": name}
                row.update(result.credit_rating.to_dict())
                rating_rows.append(row)

        if rating_rows:
            rating_df = pd.DataFrame(rating_rows)
            rating_path = output_dir / "credit_ratings.csv"
            rating_df.to_csv(rating_path, index=False)
            paths["credit_ratings"] = rating_path

        # Export risk attribution table (for scenarios that have decomposition)
        attribution_rows = []
        for name, result in results.items():
            if result.risk_attribution is not None:
                row = {"scenario": name}
                row.update(result.risk_attribution.to_dict())
                attribution_rows.append(row)

        if attribution_rows:
            attr_df = pd.DataFrame(attribution_rows)
            attr_path = output_dir / "risk_attribution.csv"
            attr_df.to_csv(attr_path, index=False)
            paths["risk_attribution"] = attr_path

        return paths
