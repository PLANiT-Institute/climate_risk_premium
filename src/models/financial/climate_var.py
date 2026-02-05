"""
Climate Value-at-Risk (Climate VaR) Module.

Implements probabilistic climate risk assessment following:
- Bressan et al. (2024): 82% underestimation without proper tail risk
- TCFD recommendations for climate VaR
- Industry standards from Ortec Finance, MSCI, S&P

Climate VaR measures the potential loss from climate-related events
at specified confidence levels (e.g., 95%, 99%).

Key metrics:
- Expected Annual Loss (EAL/AAL)
- VaR at various confidence levels
- Tail VaR / Conditional VaR (CVaR/ES)
- Probable Maximum Loss (PML)

Sources:
- Bressan et al. (2024) Nature Communications
- TCFD (2017) Technical Supplement
- Swiss Re sigma reports
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Callable
from enum import Enum
import math
import random
from statistics import mean, stdev


class DistributionType(Enum):
    """Probability distribution types for hazard modeling."""
    NORMAL = "normal"
    LOGNORMAL = "lognormal"
    GUMBEL = "gumbel"          # Extreme value Type I
    FRECHET = "frechet"        # Extreme value Type II
    WEIBULL = "weibull"        # Extreme value Type III
    PARETO = "pareto"          # Heavy-tailed
    EMPIRICAL = "empirical"    # From historical data


@dataclass
class LossDistribution:
    """
    Loss distribution from climate hazards.

    Stores simulated or analytical loss distribution
    for VaR calculations.
    """
    losses: List[float]                  # Simulated losses
    n_simulations: int                   # Number of simulations
    distribution_type: DistributionType  # Underlying distribution
    hazard_type: str                     # Hazard that generated losses
    time_horizon_years: int = 1          # Time horizon

    # Distribution parameters
    mean_loss: float = 0.0
    std_loss: float = 0.0
    skewness: float = 0.0
    kurtosis: float = 0.0

    def __post_init__(self):
        """Calculate distribution statistics."""
        if self.losses:
            self.losses.sort()
            self.mean_loss = mean(self.losses)
            if len(self.losses) > 1:
                self.std_loss = stdev(self.losses)

    def get_percentile(self, percentile: float) -> float:
        """Get loss at given percentile (0-100)."""
        if not self.losses:
            return 0.0
        idx = int(len(self.losses) * percentile / 100)
        idx = min(idx, len(self.losses) - 1)
        return self.losses[idx]

    def get_var(self, confidence: float) -> float:
        """Get VaR at confidence level (e.g., 0.95 for 95%)."""
        return self.get_percentile(confidence * 100)

    def get_tail_var(self, confidence: float) -> float:
        """
        Get Tail VaR (CVaR/ES) at confidence level.

        Tail VaR = average of losses exceeding VaR.
        """
        var = self.get_var(confidence)
        tail_losses = [l for l in self.losses if l >= var]
        if tail_losses:
            return mean(tail_losses)
        return var


@dataclass
class ClimateVaR:
    """
    Climate Value-at-Risk results.

    Comprehensive risk metrics following industry standards.
    """
    # Identification
    asset_id: str
    scenario: str
    year: int
    time_horizon_years: int = 1

    # Central estimates
    expected_annual_loss: float = 0.0    # AAL/EAL
    expected_annual_loss_pct: float = 0.0  # As % of asset value

    # VaR metrics
    var_90: float = 0.0                  # 1-in-10 year loss
    var_95: float = 0.0                  # 1-in-20 year loss
    var_99: float = 0.0                  # 1-in-100 year loss
    var_995: float = 0.0                 # 1-in-200 year loss

    # Tail risk (CVaR/ES)
    tail_var_95: float = 0.0             # Expected shortfall at 95%
    tail_var_99: float = 0.0             # Expected shortfall at 99%

    # Probable Maximum Loss
    pml_250: float = 0.0                 # 1-in-250 year
    pml_500: float = 0.0                 # 1-in-500 year

    # NPV of losses
    discount_rate: float = 0.08
    npv_expected_loss: float = 0.0       # NPV of EAL over horizon
    npv_var_95: float = 0.0              # NPV of VaR95 losses

    # Component breakdown
    by_hazard: Dict[str, float] = field(default_factory=dict)

    # Confidence in estimates
    simulation_count: int = 0
    confidence_interval_low: float = 0.0
    confidence_interval_high: float = 0.0

    def to_dict(self) -> Dict[str, float]:
        """Convert to dictionary."""
        return {
            "asset_id": self.asset_id,
            "scenario": self.scenario,
            "year": self.year,
            "expected_annual_loss": self.expected_annual_loss,
            "expected_annual_loss_pct": self.expected_annual_loss_pct,
            "var_95": self.var_95,
            "var_99": self.var_99,
            "tail_var_99": self.tail_var_99,
            "npv_expected_loss": self.npv_expected_loss,
        }


class MonteCarloEngine:
    """
    Monte Carlo simulation engine for Climate VaR.

    Generates loss distributions by:
    1. Sampling hazard intensities from probability distributions
    2. Applying damage functions to get damage ratios
    3. Converting to monetary losses using exposure values
    """

    def __init__(
        self,
        n_simulations: int = 10000,
        seed: Optional[int] = None,
    ):
        self.n_simulations = n_simulations
        if seed is not None:
            random.seed(seed)

    def sample_gumbel(self, loc: float, scale: float) -> float:
        """Sample from Gumbel distribution (extreme value Type I)."""
        u = random.random()
        return loc - scale * math.log(-math.log(u))

    def sample_lognormal(self, mu: float, sigma: float) -> float:
        """Sample from lognormal distribution."""
        return random.lognormvariate(mu, sigma)

    def sample_pareto(self, alpha: float, x_min: float) -> float:
        """Sample from Pareto distribution (heavy-tailed)."""
        u = random.random()
        return x_min / (u ** (1 / alpha))

    def simulate_hazard_losses(
        self,
        hazard_type: str,
        distribution_params: Dict[str, float],
        damage_function: Callable[[float], float],
        exposure_value: float,
        distribution_type: DistributionType = DistributionType.GUMBEL,
    ) -> LossDistribution:
        """
        Simulate losses for a single hazard.

        Args:
            hazard_type: Type of hazard
            distribution_params: Parameters for hazard intensity distribution
            damage_function: Maps intensity to damage ratio (0-1)
            exposure_value: Value at risk (USD)
            distribution_type: Type of probability distribution

        Returns:
            LossDistribution with simulated losses
        """
        losses = []

        for _ in range(self.n_simulations):
            # Sample hazard intensity
            if distribution_type == DistributionType.GUMBEL:
                intensity = self.sample_gumbel(
                    distribution_params.get("loc", 0),
                    distribution_params.get("scale", 1),
                )
            elif distribution_type == DistributionType.LOGNORMAL:
                intensity = self.sample_lognormal(
                    distribution_params.get("mu", 0),
                    distribution_params.get("sigma", 1),
                )
            elif distribution_type == DistributionType.PARETO:
                intensity = self.sample_pareto(
                    distribution_params.get("alpha", 2),
                    distribution_params.get("x_min", 1),
                )
            else:
                # Normal fallback
                intensity = random.gauss(
                    distribution_params.get("mean", 0),
                    distribution_params.get("std", 1),
                )

            # Ensure non-negative intensity
            intensity = max(0, intensity)

            # Apply damage function
            damage_ratio = damage_function(intensity)

            # Calculate monetary loss
            loss = damage_ratio * exposure_value

            losses.append(loss)

        return LossDistribution(
            losses=losses,
            n_simulations=self.n_simulations,
            distribution_type=distribution_type,
            hazard_type=hazard_type,
        )


def calculate_climate_var(
    asset_id: str,
    exposure_value: float,
    hazard_distributions: Dict[str, Dict],
    damage_functions: Dict[str, Callable],
    scenario: str = "RCP8.5",
    year: int = 2050,
    n_simulations: int = 10000,
    time_horizon_years: int = 30,
    discount_rate: float = 0.08,
) -> ClimateVaR:
    """
    Calculate comprehensive Climate VaR for an asset.

    Args:
        asset_id: Asset identifier
        exposure_value: Total value at risk (USD)
        hazard_distributions: Dict of hazard -> distribution parameters
        damage_functions: Dict of hazard -> damage function
        scenario: Climate scenario
        year: Target year
        n_simulations: Number of Monte Carlo simulations
        time_horizon_years: Investment horizon
        discount_rate: Discount rate for NPV

    Returns:
        ClimateVaR with all risk metrics
    """
    engine = MonteCarloEngine(n_simulations=n_simulations)

    # Simulate losses for each hazard
    hazard_losses: Dict[str, LossDistribution] = {}
    for hazard, params in hazard_distributions.items():
        if hazard in damage_functions:
            hazard_losses[hazard] = engine.simulate_hazard_losses(
                hazard_type=hazard,
                distribution_params=params,
                damage_function=damage_functions[hazard],
                exposure_value=exposure_value,
                distribution_type=params.get("type", DistributionType.GUMBEL),
            )

    # Aggregate losses (simple sum - could add correlation)
    total_losses = [0.0] * n_simulations
    for hazard, loss_dist in hazard_losses.items():
        for i, loss in enumerate(loss_dist.losses):
            total_losses[i] += loss

    total_losses.sort()

    # Calculate metrics
    eal = mean(total_losses)
    eal_pct = eal / exposure_value if exposure_value > 0 else 0

    var_90 = total_losses[int(0.90 * n_simulations)]
    var_95 = total_losses[int(0.95 * n_simulations)]
    var_99 = total_losses[int(0.99 * n_simulations)]
    var_995 = total_losses[int(0.995 * n_simulations)]

    # Tail VaR
    tail_95_losses = total_losses[int(0.95 * n_simulations):]
    tail_99_losses = total_losses[int(0.99 * n_simulations):]
    tail_var_95 = mean(tail_95_losses) if tail_95_losses else var_95
    tail_var_99 = mean(tail_99_losses) if tail_99_losses else var_99

    # PML
    pml_250 = total_losses[int(0.996 * n_simulations)]
    pml_500 = total_losses[int(0.998 * n_simulations)]

    # NPV calculations
    npv_eal = sum(
        eal / ((1 + discount_rate) ** t)
        for t in range(1, time_horizon_years + 1)
    )
    npv_var_95 = sum(
        var_95 / ((1 + discount_rate) ** t)
        for t in range(1, time_horizon_years + 1)
    )

    # Component breakdown
    by_hazard = {
        hazard: loss_dist.mean_loss
        for hazard, loss_dist in hazard_losses.items()
    }

    return ClimateVaR(
        asset_id=asset_id,
        scenario=scenario,
        year=year,
        time_horizon_years=time_horizon_years,
        expected_annual_loss=eal,
        expected_annual_loss_pct=eal_pct,
        var_90=var_90,
        var_95=var_95,
        var_99=var_99,
        var_995=var_995,
        tail_var_95=tail_var_95,
        tail_var_99=tail_var_99,
        pml_250=pml_250,
        pml_500=pml_500,
        discount_rate=discount_rate,
        npv_expected_loss=npv_eal,
        npv_var_95=npv_var_95,
        by_hazard=by_hazard,
        simulation_count=n_simulations,
    )


# =============================================================================
# EXAMPLE HAZARD DISTRIBUTIONS FOR KOREA
# =============================================================================

KOREA_HAZARD_DISTRIBUTIONS = {
    "tropical_cyclone": {
        "type": DistributionType.GUMBEL,
        "loc": 25.0,        # Location (mode wind speed m/s)
        "scale": 8.0,       # Scale (spread)
        "source": "KMA typhoon records 1951-2020",
    },
    "wildfire": {
        "type": DistributionType.LOGNORMAL,
        "mu": 2.8,          # Log of median FWI
        "sigma": 0.6,       # Log standard deviation
        "source": "Korea Forest Service 1991-2020",
    },
    "river_flood": {
        "type": DistributionType.GUMBEL,
        "loc": 1.0,         # Mode flood depth (m)
        "scale": 0.5,       # Scale
        "source": "MOLIT flood records",
    },
    "heat_stress": {
        "type": DistributionType.GUMBEL,
        "loc": 32.0,        # Mode max temperature
        "scale": 3.0,       # Scale
        "source": "KMA temperature records",
    },
}
