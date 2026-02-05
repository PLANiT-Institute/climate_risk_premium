"""
RCP (Representative Concentration Pathway) Scenarios.

Data from:
- IPCC AR5 Working Group I
- CLIMADA climate module
- KMA Korea-specific downscaling

See docs/sources/CLIMATE_SCENARIOS.md for full citations.
"""
from typing import Dict

from .climate_scenario import RCPScenario, ClimateProjection


# =============================================================================
# RCP SCENARIO DATA
# =============================================================================

RCP_SCENARIOS: Dict[str, RCPScenario] = {
    "RCP2.6": RCPScenario(
        _name="RCP2.6",
        _description="Strong mitigation pathway (Paris-aligned, <2°C)",
        _source="IPCC AR5 WG1, CMIP5 multi-model mean",
        _radiative_forcing=2.6,
        projections={
            2024: ClimateProjection(
                year=2024,
                global_temp_anomaly=1.1,
                regional_temp_anomaly=1.3,  # Korea warms faster
                sea_level_rise=0.10,
                co2_concentration=420,
            ),
            2030: ClimateProjection(
                year=2030,
                global_temp_anomaly=1.3,
                regional_temp_anomaly=1.6,
                sea_level_rise=0.14,
                co2_concentration=435,
            ),
            2050: ClimateProjection(
                year=2050,
                global_temp_anomaly=1.5,
                regional_temp_anomaly=1.9,
                sea_level_rise=0.24,
                co2_concentration=440,
            ),
            2100: ClimateProjection(
                year=2100,
                global_temp_anomaly=1.6,
                regional_temp_anomaly=2.0,
                sea_level_rise=0.44,
                co2_concentration=420,  # Declines after peak
            ),
        }
    ),

    "RCP4.5": RCPScenario(
        _name="RCP4.5",
        _description="Intermediate pathway (moderate mitigation)",
        _source="IPCC AR5 WG1, CMIP5 multi-model mean",
        _radiative_forcing=4.5,
        projections={
            2024: ClimateProjection(
                year=2024,
                global_temp_anomaly=1.1,
                regional_temp_anomaly=1.3,
                sea_level_rise=0.10,
                co2_concentration=420,
            ),
            2030: ClimateProjection(
                year=2030,
                global_temp_anomaly=1.4,
                regional_temp_anomaly=1.7,
                sea_level_rise=0.15,
                co2_concentration=450,
            ),
            2050: ClimateProjection(
                year=2050,
                global_temp_anomaly=1.8,
                regional_temp_anomaly=2.3,
                sea_level_rise=0.28,
                co2_concentration=520,
            ),
            2100: ClimateProjection(
                year=2100,
                global_temp_anomaly=2.4,
                regional_temp_anomaly=3.1,
                sea_level_rise=0.53,
                co2_concentration=540,
            ),
        }
    ),

    "RCP6.0": RCPScenario(
        _name="RCP6.0",
        _description="Higher pathway (delayed mitigation)",
        _source="IPCC AR5 WG1, CMIP5 multi-model mean",
        _radiative_forcing=6.0,
        projections={
            2024: ClimateProjection(
                year=2024,
                global_temp_anomaly=1.1,
                regional_temp_anomaly=1.3,
                sea_level_rise=0.10,
                co2_concentration=420,
            ),
            2030: ClimateProjection(
                year=2030,
                global_temp_anomaly=1.4,
                regional_temp_anomaly=1.8,
                sea_level_rise=0.15,
                co2_concentration=460,
            ),
            2050: ClimateProjection(
                year=2050,
                global_temp_anomaly=2.0,
                regional_temp_anomaly=2.6,
                sea_level_rise=0.30,
                co2_concentration=570,
            ),
            2100: ClimateProjection(
                year=2100,
                global_temp_anomaly=2.9,
                regional_temp_anomaly=3.8,
                sea_level_rise=0.58,
                co2_concentration=670,
            ),
        }
    ),

    "RCP8.5": RCPScenario(
        _name="RCP8.5",
        _description="High emissions pathway (no mitigation)",
        _source="IPCC AR5 WG1, CMIP5 multi-model mean, KMA Korea downscaling",
        _radiative_forcing=8.5,
        projections={
            2024: ClimateProjection(
                year=2024,
                global_temp_anomaly=1.1,
                regional_temp_anomaly=1.3,
                sea_level_rise=0.10,
                co2_concentration=420,
            ),
            2030: ClimateProjection(
                year=2030,
                global_temp_anomaly=1.5,
                regional_temp_anomaly=1.9,
                sea_level_rise=0.16,
                co2_concentration=480,
            ),
            2050: ClimateProjection(
                year=2050,
                global_temp_anomaly=2.3,
                regional_temp_anomaly=3.0,
                sea_level_rise=0.34,
                co2_concentration=600,
            ),
            2100: ClimateProjection(
                year=2100,
                global_temp_anomaly=4.3,
                regional_temp_anomaly=5.7,  # Korea: KMA projection
                sea_level_rise=0.82,
                co2_concentration=940,
            ),
        }
    ),
}
