"""
Probabilistic Physical Risk Framework.

This module implements a proper probabilistic framework for physical climate risk
that produces:
1. Annual Exceedance Probability (AEP) for each hazard
2. Expected Annual Loss (EAL) = Sum of (Probability × Damage)
3. Probable Maximum Loss (PML) at different return periods
4. Credit risk inputs: PD impact, LGD impact, Expected Loss

The framework follows the standard risk equation:
    Risk = Hazard × Exposure × Vulnerability

References:
-----------
[1] CLIMADA methodology: Impact = Σ (Hazard_intensity × Damage_function × Exposure)
[2] Zscheischler et al. (2018) for compound risk amplification
[3] FEMA HAZUS for depth-damage curves
[4] IPCC AR6 for climate projections

Author: Climate Risk Premium Model
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Optional, Callable
import numpy as np
from scipy import stats
from enum import Enum

from .literature_parameters import (
    THERMAL_EFFICIENCY_PARAMS,
    WILDFIRE_OUTAGE_PARAMS,
    FLOOD_OUTAGE_PARAMS,
    COMPOUND_RISK_PARAMS,
    SLR_PARAMS,
    LiteratureSource,
)


class HazardType(Enum):
    """Types of physical hazards."""
    WILDFIRE = "wildfire"
    FLOOD = "flood"
    SEA_LEVEL_RISE = "sea_level_rise"
    HEAT_WAVE = "heat_wave"
    DROUGHT = "drought"


@dataclass
class HazardEvent:
    """
    A single hazard event with intensity and probability.

    Attributes:
        hazard_type: Type of hazard
        intensity: Hazard intensity (units depend on type)
        annual_probability: Probability of occurrence in any year
        return_period: Return period in years (= 1/annual_probability)
        duration_days: Expected duration of event
    """
    hazard_type: HazardType
    intensity: float
    annual_probability: float
    duration_days: float = 1.0

    @property
    def return_period(self) -> float:
        """Return period in years."""
        if self.annual_probability > 0:
            return 1.0 / self.annual_probability
        return float('inf')

    def __repr__(self) -> str:
        return (f"HazardEvent({self.hazard_type.value}, "
                f"intensity={self.intensity:.2f}, "
                f"P={self.annual_probability:.4f}, "
                f"RP={self.return_period:.0f}yr)")


@dataclass
class DamageFunction:
    """
    Vulnerability/damage function relating hazard intensity to damage.

    The function returns Mean Damage Ratio (MDR) as fraction of asset value.

    Attributes:
        hazard_type: Type of hazard this function applies to
        intensity_unit: Unit of hazard intensity (e.g., "m/s", "meters", "°C")
        damage_unit: Usually "fraction" (0-1)
        curve_points: Dict of intensity -> damage fraction
        source: Literature source for the curve
    """
    hazard_type: HazardType
    intensity_unit: str
    curve_points: Dict[float, float]
    source: str

    def get_damage(self, intensity: float) -> float:
        """
        Get damage fraction for given hazard intensity.

        Uses linear interpolation between curve points.
        """
        intensities = sorted(self.curve_points.keys())

        if intensity <= intensities[0]:
            return self.curve_points[intensities[0]]
        if intensity >= intensities[-1]:
            return self.curve_points[intensities[-1]]

        # Linear interpolation
        for i in range(len(intensities) - 1):
            if intensities[i] <= intensity <= intensities[i + 1]:
                x0, x1 = intensities[i], intensities[i + 1]
                y0, y1 = self.curve_points[x0], self.curve_points[x1]
                weight = (intensity - x0) / (x1 - x0)
                return y0 + weight * (y1 - y0)

        return 0.0


@dataclass
class ExposureAsset:
    """
    An exposed asset (power plant) with its characteristics.

    Attributes:
        name: Asset identifier
        value_usd: Total asset value in USD
        capacity_mw: Generation capacity in MW
        annual_revenue_usd: Annual revenue in USD
        location_lat: Latitude
        location_lon: Longitude
        coastal: Whether asset is coastal (affects SLR vulnerability)
        cooling_type: "once-through" or "closed-loop"
    """
    name: str
    value_usd: float
    capacity_mw: float
    annual_revenue_usd: float
    location_lat: float = 37.15  # Samcheok default
    location_lon: float = 129.17
    coastal: bool = True
    cooling_type: str = "once-through"


@dataclass
class AnnualRiskResult:
    """
    Annual risk calculation result for a single hazard.

    Attributes:
        hazard_type: Type of hazard
        expected_annual_loss: Expected annual loss in USD
        expected_annual_outage_days: Expected outage days per year
        loss_distribution: (probability, loss) pairs for loss curve
        pml_100yr: Probable Maximum Loss at 100-year return period
        pml_250yr: Probable Maximum Loss at 250-year return period
    """
    hazard_type: HazardType
    expected_annual_loss: float
    expected_annual_outage_days: float
    loss_distribution: List[Tuple[float, float]]
    pml_100yr: float
    pml_250yr: float

    @property
    def eal_rate(self) -> float:
        """Expected annual loss as fraction of exposure."""
        if self.loss_distribution and self.loss_distribution[-1][1] > 0:
            max_loss = max(loss for _, loss in self.loss_distribution)
            return self.expected_annual_loss / max_loss if max_loss > 0 else 0
        return 0


@dataclass
class CreditRiskImpact:
    """
    Physical risk impact on credit metrics.

    Attributes:
        pd_increase_bps: Increase in probability of default (basis points)
        lgd_increase_pct: Increase in loss given default (percentage points)
        expected_loss_annual: Annual expected loss from physical risk
        dscr_reduction: Reduction in DSCR from physical risk
        rating_notches_down: Expected credit rating notches downgrade
    """
    pd_increase_bps: float
    lgd_increase_pct: float
    expected_loss_annual: float
    dscr_reduction: float
    rating_notches_down: int

    @property
    def credit_spread_impact_bps(self) -> float:
        """Estimated credit spread impact in basis points."""
        # Simplified: 1 notch ≈ 50 bps for investment grade
        return self.pd_increase_bps + (self.rating_notches_down * 50)


class ProbabilisticRiskEngine:
    """
    Engine for probabilistic physical risk calculation.

    Implements the full risk chain:
    1. Generate hazard scenarios with probabilities
    2. Apply damage functions to get conditional losses
    3. Aggregate to Expected Annual Loss
    4. Compute loss exceedance curves
    5. Translate to credit risk metrics
    """

    def __init__(self, exposure: ExposureAsset):
        """Initialize with asset exposure."""
        self.exposure = exposure
        self.damage_functions = self._load_damage_functions()
        self.hazard_scenarios = self._generate_hazard_scenarios()

    def _load_damage_functions(self) -> Dict[HazardType, DamageFunction]:
        """Load literature-backed damage functions."""
        functions = {}

        # Flood damage function from HAZUS
        functions[HazardType.FLOOD] = DamageFunction(
            hazard_type=HazardType.FLOOD,
            intensity_unit="meters",
            curve_points=FLOOD_OUTAGE_PARAMS["flood_depth_damage_curve"],
            source="FEMA HAZUS-MH Technical Manual (2022)"
        )

        # Wildfire damage function (derived from California ISO data)
        # Intensity = Fire Weather Index (FWI)
        functions[HazardType.WILDFIRE] = DamageFunction(
            hazard_type=HazardType.WILDFIRE,
            intensity_unit="FWI",
            curve_points={
                0: 0.00,    # No fire risk
                20: 0.01,   # Low risk - baseline outages
                30: 0.03,   # Moderate risk
                40: 0.06,   # High risk
                50: 0.10,   # Very high risk
                60: 0.15,   # Extreme risk
                80: 0.25,   # Catastrophic
            },
            source="Derived from CAISO wildfire statistics (2003-2016)"
        )

        # Heat wave efficiency loss function
        # Intensity = temperature anomaly above baseline (°C)
        functions[HazardType.HEAT_WAVE] = DamageFunction(
            hazard_type=HazardType.HEAT_WAVE,
            intensity_unit="°C above normal",
            curve_points={
                0: 0.00,
                5: 0.015,   # 1.5% capacity loss at 5°C above normal
                10: 0.035,  # 3.5% at 10°C
                15: 0.060,  # 6% at 15°C (heat wave)
                20: 0.100,  # 10% at 20°C (extreme heat)
            },
            source="S&P Global/ES&T (2017) thermal efficiency study"
        )

        # Sea level rise capacity derate function
        # Intensity = SLR in meters
        functions[HazardType.SEA_LEVEL_RISE] = DamageFunction(
            hazard_type=HazardType.SEA_LEVEL_RISE,
            intensity_unit="meters SLR",
            curve_points={
                0.0: 0.00,
                0.1: 0.005,   # 0.5% at 0.1m
                0.3: 0.015,   # 1.5% at 0.3m
                0.5: 0.030,   # 3% at 0.5m
                1.0: 0.060,   # 6% at 1.0m
                1.5: 0.100,   # 10% at 1.5m (severe)
            },
            source="IPCC AR6 + coastal power plant studies"
        )

        return functions

    def _generate_hazard_scenarios(self) -> Dict[HazardType, List[HazardEvent]]:
        """
        Generate hazard scenarios with probabilities.

        Uses return period approach: generate events at different
        return periods (10yr, 25yr, 50yr, 100yr, 250yr, 500yr).
        """
        scenarios = {}

        # Flood scenarios (Korea-specific)
        # Based on Seoul flood return period standards
        scenarios[HazardType.FLOOD] = [
            HazardEvent(HazardType.FLOOD, 0.0, 0.50, 0),      # No flood (50% of years)
            HazardEvent(HazardType.FLOOD, 0.3, 0.20, 3),      # Minor flood (1 in 5 yr)
            HazardEvent(HazardType.FLOOD, 0.6, 0.10, 5),      # Moderate (1 in 10 yr)
            HazardEvent(HazardType.FLOOD, 1.0, 0.04, 7),      # Significant (1 in 25 yr)
            HazardEvent(HazardType.FLOOD, 1.5, 0.02, 10),     # Major (1 in 50 yr)
            HazardEvent(HazardType.FLOOD, 2.0, 0.01, 14),     # Severe (1 in 100 yr)
            HazardEvent(HazardType.FLOOD, 3.0, 0.004, 21),    # Extreme (1 in 250 yr)
            HazardEvent(HazardType.FLOOD, 4.0, 0.002, 30),    # Catastrophic (1 in 500 yr)
        ]

        # Wildfire scenarios (FWI-based)
        # Based on California transmission line statistics
        scenarios[HazardType.WILDFIRE] = [
            HazardEvent(HazardType.WILDFIRE, 20, 0.60, 0),    # Normal conditions
            HazardEvent(HazardType.WILDFIRE, 30, 0.20, 3),    # Elevated risk
            HazardEvent(HazardType.WILDFIRE, 40, 0.10, 5),    # High risk
            HazardEvent(HazardType.WILDFIRE, 50, 0.05, 7),    # Very high
            HazardEvent(HazardType.WILDFIRE, 60, 0.03, 10),   # Extreme
            HazardEvent(HazardType.WILDFIRE, 80, 0.01, 14),   # Catastrophic
        ]

        # Heat wave scenarios
        # Temperature anomaly above normal
        scenarios[HazardType.HEAT_WAVE] = [
            HazardEvent(HazardType.HEAT_WAVE, 0, 0.50, 0),    # Normal
            HazardEvent(HazardType.HEAT_WAVE, 5, 0.25, 14),   # Warm
            HazardEvent(HazardType.HEAT_WAVE, 10, 0.15, 7),   # Hot
            HazardEvent(HazardType.HEAT_WAVE, 15, 0.07, 5),   # Heat wave
            HazardEvent(HazardType.HEAT_WAVE, 20, 0.03, 3),   # Extreme heat
        ]

        # Sea level rise is chronic, not event-based
        # Modeled as continuous increase over time
        # This will be handled separately in projection

        return scenarios

    def calculate_annual_risk(
        self,
        hazard_type: HazardType,
        year: int = 2024,
        rcp_scenario: str = "RCP4.5"
    ) -> AnnualRiskResult:
        """
        Calculate expected annual risk for a single hazard type.

        Args:
            hazard_type: Type of hazard to analyze
            year: Projection year (for climate change adjustment)
            rcp_scenario: Climate scenario ("RCP4.5" or "RCP8.5")

        Returns:
            AnnualRiskResult with expected losses and distribution
        """
        if hazard_type not in self.hazard_scenarios:
            return AnnualRiskResult(
                hazard_type=hazard_type,
                expected_annual_loss=0,
                expected_annual_outage_days=0,
                loss_distribution=[],
                pml_100yr=0,
                pml_250yr=0
            )

        scenarios = self.hazard_scenarios[hazard_type]
        damage_func = self.damage_functions.get(hazard_type)

        if not damage_func:
            return AnnualRiskResult(
                hazard_type=hazard_type,
                expected_annual_loss=0,
                expected_annual_outage_days=0,
                loss_distribution=[],
                pml_100yr=0,
                pml_250yr=0
            )

        # Climate change adjustment factor
        climate_factor = self._get_climate_adjustment(hazard_type, year, rcp_scenario)

        # Calculate losses for each scenario
        losses = []
        outage_days = []
        probabilities = []

        for event in scenarios:
            # Adjust intensity for climate change
            adjusted_intensity = event.intensity * climate_factor

            # Get damage fraction from vulnerability function
            damage_fraction = damage_func.get_damage(adjusted_intensity)

            # Calculate loss (as revenue loss, not asset destruction for operations)
            annual_revenue = self.exposure.annual_revenue_usd
            loss = damage_fraction * annual_revenue

            # Outage days
            days = event.duration_days * damage_fraction * 365 / 100

            losses.append(loss)
            outage_days.append(days)
            probabilities.append(event.annual_probability)

        # Expected Annual Loss = Σ (probability × loss)
        eal = sum(p * l for p, l in zip(probabilities, losses))
        ead = sum(p * d for p, d in zip(probabilities, outage_days))

        # Build loss distribution for exceedance curve
        loss_dist = sorted(zip(probabilities, losses), key=lambda x: x[1])

        # PML at different return periods
        pml_100yr = self._get_pml(loss_dist, 0.01)  # 1% annual probability
        pml_250yr = self._get_pml(loss_dist, 0.004)  # 0.4% annual probability

        return AnnualRiskResult(
            hazard_type=hazard_type,
            expected_annual_loss=eal,
            expected_annual_outage_days=ead,
            loss_distribution=loss_dist,
            pml_100yr=pml_100yr,
            pml_250yr=pml_250yr
        )

    def _get_climate_adjustment(
        self,
        hazard_type: HazardType,
        year: int,
        rcp_scenario: str
    ) -> float:
        """
        Get climate change adjustment factor for hazard intensity.

        Based on IPCC AR6 projections.
        """
        years_from_baseline = max(0, year - 2024)

        # Annual increase rates based on literature
        if rcp_scenario == "RCP8.5":
            rates = {
                HazardType.FLOOD: 0.02,       # 2% per year intensity increase
                HazardType.WILDFIRE: 0.025,   # 2.5% per year (FWI increase)
                HazardType.HEAT_WAVE: 0.03,   # 3% per year (warming)
                HazardType.SEA_LEVEL_RISE: 0.01,
            }
        else:  # RCP4.5
            rates = {
                HazardType.FLOOD: 0.01,
                HazardType.WILDFIRE: 0.015,
                HazardType.HEAT_WAVE: 0.015,
                HazardType.SEA_LEVEL_RISE: 0.005,
            }

        rate = rates.get(hazard_type, 0.01)
        return 1.0 + (rate * years_from_baseline)

    def _get_pml(
        self,
        loss_dist: List[Tuple[float, float]],
        exceedance_prob: float
    ) -> float:
        """Get Probable Maximum Loss at given exceedance probability."""
        cumulative_prob = 0
        for prob, loss in loss_dist:
            cumulative_prob += prob
            if cumulative_prob >= (1 - exceedance_prob):
                return loss
        return loss_dist[-1][1] if loss_dist else 0

    def calculate_compound_risk(
        self,
        year: int = 2024,
        rcp_scenario: str = "RCP4.5"
    ) -> Dict[str, float]:
        """
        Calculate compound risk from multiple concurrent hazards.

        Applies the Zscheischler et al. (2018) compound risk amplification.

        Returns:
            Dict with total EAL, compound multiplier, and component breakdowns
        """
        # Calculate individual hazard risks
        individual_risks = {}
        for hazard_type in [HazardType.FLOOD, HazardType.WILDFIRE, HazardType.HEAT_WAVE]:
            result = self.calculate_annual_risk(hazard_type, year, rcp_scenario)
            individual_risks[hazard_type] = result

        # Sum of individual EALs
        total_individual_eal = sum(r.expected_annual_loss for r in individual_risks.values())
        total_individual_days = sum(r.expected_annual_outage_days for r in individual_risks.values())

        # Compound risk multiplier (Zscheischler et al. 2018)
        # Higher when more hazards have significant probability
        base_multiplier = float(COMPOUND_RISK_PARAMS["base_compound_multiplier"].value)
        max_multiplier = float(COMPOUND_RISK_PARAMS["max_compound_multiplier"].value)

        # Calculate system stress (sum of individual EAL rates)
        stress = sum(r.eal_rate for r in individual_risks.values())

        # Sigmoid scaling: multiplier increases with stress
        stress_factor = min(1.0, stress * 10)  # Scales 0-0.1 to 0-1
        compound_multiplier = base_multiplier + (max_multiplier - base_multiplier) * stress_factor

        # Total compound EAL
        total_compound_eal = total_individual_eal * compound_multiplier
        total_compound_days = total_individual_days * compound_multiplier

        return {
            "total_eal_individual": total_individual_eal,
            "total_eal_compound": total_compound_eal,
            "compound_multiplier": compound_multiplier,
            "total_outage_days_individual": total_individual_days,
            "total_outage_days_compound": total_compound_days,
            "flood_eal": individual_risks[HazardType.FLOOD].expected_annual_loss,
            "wildfire_eal": individual_risks[HazardType.WILDFIRE].expected_annual_loss,
            "heat_wave_eal": individual_risks[HazardType.HEAT_WAVE].expected_annual_loss,
            "flood_pml_100yr": individual_risks[HazardType.FLOOD].pml_100yr,
            "wildfire_pml_100yr": individual_risks[HazardType.WILDFIRE].pml_100yr,
        }

    def calculate_credit_impact(
        self,
        year: int = 2024,
        rcp_scenario: str = "RCP4.5",
        baseline_dscr: float = 1.5,
    ) -> CreditRiskImpact:
        """
        Translate physical risk to credit risk metrics.

        Args:
            year: Projection year
            rcp_scenario: Climate scenario
            baseline_dscr: Baseline DSCR without physical risk

        Returns:
            CreditRiskImpact with PD, LGD, and rating impacts
        """
        compound_risk = self.calculate_compound_risk(year, rcp_scenario)
        eal = compound_risk["total_eal_compound"]
        outage_days = compound_risk["total_outage_days_compound"]

        # Revenue loss rate
        revenue = self.exposure.annual_revenue_usd
        eal_rate = eal / revenue if revenue > 0 else 0

        # DSCR reduction from physical risk
        # Assume DSCR roughly proportional to (1 - cost_rate)
        dscr_reduction = baseline_dscr * eal_rate

        # PD increase (simplified model)
        # Rule of thumb: 1% revenue loss → 10 bps PD increase
        pd_increase_bps = eal_rate * 1000

        # LGD increase
        # Physical damage can increase LGD if collateral is damaged
        pml_100yr = compound_risk["flood_pml_100yr"] + compound_risk["wildfire_pml_100yr"]
        lgd_increase_pct = (pml_100yr / self.exposure.value_usd) * 100

        # Rating impact (simplified)
        # Rule of thumb: Each 0.2x DSCR reduction = 1 notch
        rating_notches = int(dscr_reduction / 0.2)

        return CreditRiskImpact(
            pd_increase_bps=pd_increase_bps,
            lgd_increase_pct=lgd_increase_pct,
            expected_loss_annual=eal,
            dscr_reduction=dscr_reduction,
            rating_notches_down=rating_notches
        )


def create_samcheok_exposure() -> ExposureAsset:
    """Create exposure for Samcheok Blue Power coal plant."""
    return ExposureAsset(
        name="Samcheok Blue Power",
        value_usd=3.2e9,  # $3.2 billion CAPEX
        capacity_mw=2100,
        annual_revenue_usd=2100 * 8760 * 0.65 * 80,  # 65% CF, $80/MWh
        location_lat=37.15,
        location_lon=129.17,
        coastal=True,
        cooling_type="once-through"
    )


if __name__ == "__main__":
    # Demo calculation
    exposure = create_samcheok_exposure()
    engine = ProbabilisticRiskEngine(exposure)

    print("=" * 80)
    print("PROBABILISTIC PHYSICAL RISK ANALYSIS - SAMCHEOK BLUE POWER")
    print("=" * 80)
    print()

    # Individual hazard risks
    for hazard in [HazardType.FLOOD, HazardType.WILDFIRE, HazardType.HEAT_WAVE]:
        for year in [2024, 2040, 2050]:
            result = engine.calculate_annual_risk(hazard, year, "RCP4.5")
            print(f"{hazard.value:15} {year}: EAL=${result.expected_annual_loss/1e6:>8.2f}M, "
                  f"Outage={result.expected_annual_outage_days:>5.1f}d, "
                  f"PML-100yr=${result.pml_100yr/1e6:>8.2f}M")
        print()

    # Compound risk
    print("\nCOMPOUND RISK ANALYSIS (RCP4.5, 2040):")
    compound = engine.calculate_compound_risk(2040, "RCP4.5")
    print(f"  Individual EAL: ${compound['total_eal_individual']/1e6:.2f}M")
    print(f"  Compound EAL:   ${compound['total_eal_compound']/1e6:.2f}M")
    print(f"  Multiplier:     {compound['compound_multiplier']:.2f}x")
    print(f"  Outage days:    {compound['total_outage_days_compound']:.1f} days/year")

    # Credit impact
    print("\nCREDIT RISK IMPACT (RCP4.5, 2040):")
    credit = engine.calculate_credit_impact(2040, "RCP4.5", 1.5)
    print(f"  PD increase:       {credit.pd_increase_bps:.0f} bps")
    print(f"  LGD increase:      {credit.lgd_increase_pct:.1f}%")
    print(f"  DSCR reduction:    {credit.dscr_reduction:.2f}x")
    print(f"  Rating notches:    {credit.rating_notches_down} down")
    print(f"  Spread impact:     {credit.credit_spread_impact_bps:.0f} bps")
