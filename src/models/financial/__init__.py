"""
Financial Risk Module.

Translates physical climate risk to financial metrics following:
- CLIMADA framework (Aznar-Siguan & Bresch, 2019)
- Bressan et al. (2024) asset-level methodology
- NGFS transmission channels
- WRI-EBRD power generation loss models

Structure:
- asset_exposure.py: Asset-level financial exposure
- climate_var.py: Climate Value-at-Risk calculations
- generation_loss.py: Power generation loss model
- transmission_channels.py: NGFS/Basel transmission framework
- calibration.py: Historical data calibration
- cddm.py: Climate Dividend Discount Model
- credit_risk.py: Credit risk translation
- stress_test.py: Climate stress testing
"""

from .asset_exposure import (
    AssetLevelExposure,
    AssetType,
    OwnershipChain,
    InsuranceCoverage,
    DebtProfile,
    KOREAN_COAL_FLEET,
    get_korean_coal_exposure,
    get_portfolio_by_region,
)
from .climate_var import (
    ClimateVaR,
    LossDistribution,
    MonteCarloEngine,
    DistributionType,
    calculate_climate_var,
    KOREA_HAZARD_DISTRIBUTIONS,
)
from .generation_loss import (
    GenerationLossModel,
    GenerationLossResult,
    PlantTechnology,
    CoolingType,
    WaterStressImpact,
    TemperatureImpact,
    GENERATION_LOSS_FACTORS,
    analyze_korean_coal_fleet,
)
from .transmission_channels import (
    TransmissionChannel,
    ChannelImpact,
    TransmissionModel,
    TransmissionResult,
    ImpactType,
    Reversibility,
)
from .calibration import (
    DamageFunctionCalibrator,
    CalibrationResult,
    HistoricalEvent,
    KOREAN_TYPHOONS,
    KOREAN_FLOODS,
    KOREAN_WILDFIRES,
)
from .cddm import (
    ClimateDiscountModel,
    CashFlowProjection,
    EquityValuation,
    calculate_korean_coal_equity_impact,
)
from .credit_risk import (
    CreditRiskModel,
    CreditImpact,
    CreditRating,
    DSCRModel,
    SpreadCurve,
    calculate_climate_credit_adjustment,
    RATING_PD_10Y,
)
from .stress_test import (
    ClimateStressTest,
    StressScenario,
    StressTestResult,
    ScenarioType,
    NGFS_SCENARIOS,
    run_korean_coal_stress_test,
)

__all__ = [
    # Asset Exposure
    "AssetLevelExposure",
    "AssetType",
    "OwnershipChain",
    "InsuranceCoverage",
    "DebtProfile",
    "KOREAN_COAL_FLEET",
    "get_korean_coal_exposure",
    "get_portfolio_by_region",
    # Climate VaR
    "ClimateVaR",
    "LossDistribution",
    "MonteCarloEngine",
    "DistributionType",
    "calculate_climate_var",
    "KOREA_HAZARD_DISTRIBUTIONS",
    # Generation Loss
    "GenerationLossModel",
    "GenerationLossResult",
    "PlantTechnology",
    "CoolingType",
    "WaterStressImpact",
    "TemperatureImpact",
    "GENERATION_LOSS_FACTORS",
    "analyze_korean_coal_fleet",
    # Transmission Channels
    "TransmissionChannel",
    "ChannelImpact",
    "TransmissionModel",
    "TransmissionResult",
    "ImpactType",
    "Reversibility",
    # Calibration
    "DamageFunctionCalibrator",
    "CalibrationResult",
    "HistoricalEvent",
    "KOREAN_TYPHOONS",
    "KOREAN_FLOODS",
    "KOREAN_WILDFIRES",
    # CDDM
    "ClimateDiscountModel",
    "CashFlowProjection",
    "EquityValuation",
    "calculate_korean_coal_equity_impact",
    # Credit Risk
    "CreditRiskModel",
    "CreditImpact",
    "CreditRating",
    "DSCRModel",
    "SpreadCurve",
    "calculate_climate_credit_adjustment",
    "RATING_PD_10Y",
    # Stress Test
    "ClimateStressTest",
    "StressScenario",
    "StressTestResult",
    "ScenarioType",
    "NGFS_SCENARIOS",
    "run_korean_coal_stress_test",
]
