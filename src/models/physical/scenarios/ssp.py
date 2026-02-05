"""
SSP (Shared Socioeconomic Pathway) Scenarios.

Data from:
- IPCC AR6 Working Group I
- CMIP6 multi-model ensembles
- KMA Korea-specific downscaling

See docs/sources/CLIMATE_SCENARIOS.md for full citations.
"""
from typing import Dict

from .climate_scenario import SSPScenario, ClimateProjection


# =============================================================================
# SSP SCENARIO DATA (IPCC AR6)
# =============================================================================

SSP_SCENARIOS: Dict[str, SSPScenario] = {
    "SSP1-1.9": SSPScenario(
        _name="SSP1-1.9",
        _description="Sustainability (1.5°C pathway)",
        _source="IPCC AR6 WG1, CMIP6 multi-model mean",
        _radiative_forcing=1.9,
        _ssp_number=1,
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
                global_temp_anomaly=1.3,
                regional_temp_anomaly=1.5,
                sea_level_rise=0.13,
                co2_concentration=430,
            ),
            2050: ClimateProjection(
                year=2050,
                global_temp_anomaly=1.4,
                regional_temp_anomaly=1.7,
                sea_level_rise=0.21,
                co2_concentration=420,  # Net zero achieved
            ),
            2100: ClimateProjection(
                year=2100,
                global_temp_anomaly=1.4,
                regional_temp_anomaly=1.7,
                sea_level_rise=0.38,
                co2_concentration=380,
            ),
        }
    ),

    "SSP1-2.6": SSPScenario(
        _name="SSP1-2.6",
        _description="Sustainability (2°C pathway)",
        _source="IPCC AR6 WG1, CMIP6 multi-model mean",
        _radiative_forcing=2.6,
        _ssp_number=1,
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
                regional_temp_anomaly=1.6,
                sea_level_rise=0.14,
                co2_concentration=440,
            ),
            2050: ClimateProjection(
                year=2050,
                global_temp_anomaly=1.6,
                regional_temp_anomaly=2.0,
                sea_level_rise=0.24,
                co2_concentration=450,
            ),
            2100: ClimateProjection(
                year=2100,
                global_temp_anomaly=1.8,
                regional_temp_anomaly=2.2,
                sea_level_rise=0.44,
                co2_concentration=430,
            ),
        }
    ),

    "SSP2-4.5": SSPScenario(
        _name="SSP2-4.5",
        _description="Middle of the Road",
        _source="IPCC AR6 WG1, CMIP6 multi-model mean",
        _radiative_forcing=4.5,
        _ssp_number=2,
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
                co2_concentration=455,
            ),
            2050: ClimateProjection(
                year=2050,
                global_temp_anomaly=2.0,
                regional_temp_anomaly=2.5,
                sea_level_rise=0.28,
                co2_concentration=530,
            ),
            2100: ClimateProjection(
                year=2100,
                global_temp_anomaly=2.7,
                regional_temp_anomaly=3.4,
                sea_level_rise=0.56,
                co2_concentration=560,
            ),
        }
    ),

    "SSP3-7.0": SSPScenario(
        _name="SSP3-7.0",
        _description="Regional Rivalry (high emissions)",
        _source="IPCC AR6 WG1, CMIP6 multi-model mean",
        _radiative_forcing=7.0,
        _ssp_number=3,
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
                co2_concentration=475,
            ),
            2050: ClimateProjection(
                year=2050,
                global_temp_anomaly=2.1,
                regional_temp_anomaly=2.7,
                sea_level_rise=0.32,
                co2_concentration=600,
            ),
            2100: ClimateProjection(
                year=2100,
                global_temp_anomaly=3.6,
                regional_temp_anomaly=4.7,
                sea_level_rise=0.73,
                co2_concentration=850,
            ),
        }
    ),

    "SSP5-8.5": SSPScenario(
        _name="SSP5-8.5",
        _description="Fossil-fueled Development (very high emissions)",
        _source="IPCC AR6 WG1, CMIP6 multi-model mean, KMA Korea downscaling",
        _radiative_forcing=8.5,
        _ssp_number=5,
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
                global_temp_anomaly=1.6,
                regional_temp_anomaly=2.0,
                sea_level_rise=0.17,
                co2_concentration=495,
            ),
            2050: ClimateProjection(
                year=2050,
                global_temp_anomaly=2.4,
                regional_temp_anomaly=3.2,
                sea_level_rise=0.36,
                co2_concentration=650,
            ),
            2100: ClimateProjection(
                year=2100,
                global_temp_anomaly=4.4,
                regional_temp_anomaly=5.9,  # KMA Korea projection
                sea_level_rise=0.83,
                co2_concentration=1000,
            ),
        }
    ),
}
