"""
Class-based orchestration for CRP runs using CSV inputs and CSV/plot outputs.

Updated to support new class-based risk models (src.models).
"""
from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Any, List, Optional

import pandas as pd

logger = logging.getLogger(__name__)

from src.data import load_inputs, get_param_value
from src.scenarios import TransitionScenario, PhysicalScenario, MarketScenario
from src.risk import (
    TransitionAdjustments, apply_transition, apply_physical,
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
from src.risk.physical import get_physical_risk_scenario, PhysicalAdjustments
from src.planit import PLANiTRunner, PLANiTAdapter, PLANiTIntegrationConfig
from src.models.physical.wri_thermal import WaterTemperatureModel

# Conditional import for enhanced 11th Basic Plan
try:
    from src.scenarios.enhanced_korea_power_plan import create_enhanced_11th_plan
    ENHANCED_PLAN_AVAILABLE = True
except ImportError:
    ENHANCED_PLAN_AVAILABLE = False
    create_enhanced_11th_plan = None

# New class-based models (optional import for backward compatibility)
try:
    from src.models import ClimateRiskAPI, CombinedRiskResult
    NEW_MODELS_AVAILABLE = True
except ImportError:
    NEW_MODELS_AVAILABLE = False
    ClimateRiskAPI = None
    CombinedRiskResult = None


# CRP physical scenario → PLANiT SSP + target year
PHYSICAL_SCENARIO_SSP_MAP: Dict[str, tuple] = {
    "baseline": ("ssp126", 2024),
    "moderate_physical": ("ssp126", 2040),
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
        self._wt_model_by_scenario: Dict[str, WaterTemperatureModel] = {}

    def _load_planit_results(self) -> List[Any]:
        """Load PLANiT hazard results.

        Modes:
        - csv  (default): read pre-computed CSV snapshots from Physicalrisk_PLANiT/data/results
        - live          : call PLANiT runtime (CLIMADA/PhysRisk) and backfill gaps from csv snapshots
        """
        mode = os.getenv("CRP_PLANIT_MODE", "csv").strip().lower()
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
        # Also add plant finance params
        plant_params = self._get_plant_params()
        params['debt_fraction'] = plant_params.get('debt_fraction', 0.70)
        params['equity_fraction'] = plant_params.get('equity_fraction', 0.30)
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

        # WRI water temperature disruption (intake seawater → forced curtailment)
        if crp_label not in self._wt_model_by_scenario:
            self._wt_model_by_scenario[crp_label] = WaterTemperatureModel(scenario=crp_label)
        water_temp_disruption = self._wt_model_by_scenario[crp_label].calculate_disruption(target_year)

        return PhysicalAdjustments(
            outage_rate=adj["outage_rate"],
            capacity_derate=adj["capacity_derate"],
            efficiency_loss=adj["efficiency_loss"],
            water_constrained_capacity=adj["water_constrained_capacity"],
            water_temp_disruption=water_temp_disruption,
            notes=adj["notes"],
        )

    def _load_market_scenario(self, scenario_name: str) -> MarketScenario:
        """Load market scenario (demand/price)."""
        if scenario_name == "low_demand":
            return MarketScenario(name="low_demand", demand_growth_pct=-1.0, price_sensitivity=0.5)
        elif scenario_name == "high_demand":
            return MarketScenario(name="high_demand", demand_growth_pct=2.0, price_sensitivity=0.5)
        else:
            return MarketScenario(name="baseline", demand_growth_pct=1.0, price_sensitivity=0.5)

    def _compute_component(
        self,
        plant_params: Dict[str, Any],
        transition_scenario: TransitionScenario,
        transition_adj: TransitionAdjustments,
        physical_adj: PhysicalAdjustments,
        market_scenario: MarketScenario | None,
        risk_type: str,
        yearly_transition_adj=None,
    ) -> RiskComponentResult:
        """Run cashflow → metrics → rating → CRP for a single risk configuration."""
        cashflow = compute_cashflows_timeseries(
            plant_params,
            transition_scenario,
            transition_adj,
            physical_adj,
            market_scenario,
            yearly_transition_adj=yearly_transition_adj,
        )
        metrics = calculate_metrics(cashflow, plant_params)

        avg_ebitda = float(cashflow.ebitda.mean())
        capacity_mw = plant_params.get('capacity_mw', 2000)
        total_capex = plant_params.get('total_capex_million', 3200) * 1e6
        debt_fraction = plant_params.get('debt_fraction', 0.70)
        equity_fraction = plant_params.get('equity_fraction', 0.30)
        debt_interest = plant_params.get('debt_interest_rate', 0.05)

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
            "physical_water_temp": physical_adj.water_temp_disruption,
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

        # --- Combined run (always performed, same as before) ---
        combined = self._compute_component(
            plant_params, transition_scenario, transition_adj, physical_adj,
            market_scenario, "combined",
            yearly_transition_adj=yearly_transition_adj,
        )

        # Build the primary ScenarioResult from the combined run
        result = ScenarioResult(
            scenario_name=scenario_name,
            cashflow=combined.cashflow,
            metrics=combined.metrics,
            credit_rating=combined.credit_rating,
            counterfactual_crp=assess_rating_with_counterfactual(
                calculate_rating_metrics_from_financials(
                    capacity_mw=plant_params.get('capacity_mw', 2000),
                    ebitda=float(combined.cashflow.ebitda.mean()),
                    fixed_assets=plant_params.get('total_capex_million', 3200) * 1e6,
                    interest_expense=(plant_params.get('total_capex_million', 3200) * 1e6
                                      * plant_params.get('debt_fraction', 0.70)
                                      * plant_params.get('debt_interest_rate', 0.05)),
                    total_debt=(plant_params.get('total_capex_million', 3200) * 1e6
                                * plant_params.get('debt_fraction', 0.70)),
                    cash_and_equivalents=float(combined.cashflow.ebitda.mean()) * 0.1,
                    total_equity=(plant_params.get('total_capex_million', 3200) * 1e6
                                  * plant_params.get('equity_fraction', 0.30)),
                    total_assets=plant_params.get('total_capex_million', 3200) * 1e6,
                    dscr=combined.metrics.avg_dscr,
                )
            ),
        )

        if not decompose:
            return result

        # --- Decomposition: 3 additional runs ---

        # No-risk adjustments
        no_transition = TransitionAdjustments(
            capacity_factor=float(plant_params.get("capacity_factor", 0.85)),
            operating_years=int(plant_params.get("operating_years", 40)),
            notes="No transition risk (baseline)",
        )
        no_physical = PhysicalAdjustments(
            outage_rate=0.0,
            capacity_derate=0.0,
            efficiency_loss=0.0,
            water_constrained_capacity=1.0,
            water_temp_disruption=0.0,
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
        total_capex = plant_params.get('total_capex_million', 3200) * 1e6

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

    # =========================================================================
    # NEW CLASS-BASED API METHODS
    # =========================================================================

    def run_with_new_models(
        self,
        climate_scenario: str = "RCP8.5",
        carbon_scenario: str = "korea_ets_current",
        policy_scenario: str = "korea_10th_plan",
        damage_functions: Dict[str, str] = None,
        years: List[int] = None,
    ) -> Dict[str, Any]:
        """
        Run analysis using new class-based models.

        This method uses the new ClimateRiskAPI for cleaner scenario selection.

        Args:
            climate_scenario: Climate scenario (RCP or SSP)
            carbon_scenario: Carbon pricing scenario
            policy_scenario: Policy phase-out scenario
            damage_functions: Dict mapping hazard type to function name
            years: List of years to analyze

        Returns:
            Dict with results and summary table
        """
        if not NEW_MODELS_AVAILABLE:
            raise ImportError("New models not available. Check src.models imports.")

        if years is None:
            years = [2024, 2030, 2050]

        # Initialize API
        api = ClimateRiskAPI()

        # Configure
        api.configure(
            climate_scenario=climate_scenario,
            carbon_scenario=carbon_scenario,
            policy_scenario=policy_scenario,
            damage_functions=damage_functions or {},
        )

        # Calculate for each year
        results = {}
        for year in years:
            plant_params = self._get_plant_params()
            result = api.calculate(
                year=year,
                emissions_rate=plant_params.get('emissions_tCO2_per_mwh', 0.85),
                baseline_cf=plant_params.get('capacity_factor', 0.85),
            )
            results[year] = result

        # Get summary table
        summary = api.get_summary_table(years)

        return {
            "results": results,
            "summary": summary,
            "configuration": {
                "climate_scenario": climate_scenario,
                "carbon_scenario": carbon_scenario,
                "policy_scenario": policy_scenario,
                "damage_functions": damage_functions,
            },
        }

    def list_available_options(self) -> Dict[str, Any]:
        """
        List all available scenarios and damage functions.

        Uses new class-based API.
        """
        if not NEW_MODELS_AVAILABLE:
            return {"error": "New models not available"}

        api = ClimateRiskAPI()
        return api.list_available()

    def export_new_model_results(
        self,
        results: Dict[str, Any],
        output_dir: Path,
    ) -> Dict[str, Path]:
        """
        Export results from new model API to CSV.

        Args:
            results: Output from run_with_new_models()
            output_dir: Output directory

        Returns:
            Dict of output paths
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        paths = {}

        # Export summary table
        summary = results.get("summary", {})
        if summary:
            rows = []
            years = sorted(set().union(*[set(v.keys()) for v in summary.values()]))
            for year in years:
                row = {"year": year}
                for metric, values in summary.items():
                    row[metric] = values.get(year, 0)
                rows.append(row)

            df = pd.DataFrame(rows)
            path = output_dir / "new_model_summary.csv"
            df.to_csv(path, index=False)
            paths["summary"] = path

        # Export detailed results
        year_results = results.get("results", {})
        if year_results:
            rows = []
            for year, result in year_results.items():
                row = {
                    "year": year,
                    "total_risk_premium_bps": result.total_risk_premium,
                    "transition_value": result.transition_result.value,
                    "physical_value": result.physical_result.value,
                }
                # Add components
                for k, v in result.transition_result.components.items():
                    row[f"transition_{k}"] = v
                for k, v in result.physical_result.components.items():
                    row[f"physical_{k}"] = v
                rows.append(row)

            df = pd.DataFrame(rows)
            path = output_dir / "new_model_detailed.csv"
            df.to_csv(path, index=False)
            paths["detailed"] = path

        # Export configuration
        config = results.get("configuration", {})
        if config:
            config_df = pd.DataFrame([config])
            path = output_dir / "new_model_config.csv"
            config_df.to_csv(path, index=False)
            paths["config"] = path

        return paths
