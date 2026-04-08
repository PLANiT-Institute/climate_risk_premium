"""
WRI Thermal Power Plant Vulnerability Models.

Implements water temperature and air temperature disruption models using
static vulnerability curves from WRI (World Resources Institute), extracted
from the os-climate/physrisk repository.

Curves are loaded from data/physical/wri_vulnerability_curves.json and apply
to Samcheok Blue Power (삼척블루파워) as a Steam/OnceThrough USC coal plant.

References:
    WRI thermal power plant physical climate vulnerability factors
    (via os-climate/physrisk), asset_type: Steam/OnceThrough
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import List

import numpy as np

from .temperature import CoolingType, SAMCHEOK_SST, TemperatureModel

# ---------------------------------------------------------------------------
# Path to static curve data
# ---------------------------------------------------------------------------
# src/models/physical/wri_thermal.py → 4 parents up → project root
_CURVES_PATH = (
    Path(__file__).parent.parent.parent.parent
    / "data"
    / "physical"
    / "wri_vulnerability_curves.json"
)


def _load_curves() -> dict:
    """Load WRI vulnerability curves JSON.

    Returns:
        Parsed JSON dict with keys: source, asset_type, plant, curves.

    Raises:
        FileNotFoundError: If wri_vulnerability_curves.json is not found.
    """
    if not _CURVES_PATH.exists():
        raise FileNotFoundError(
            f"WRI vulnerability curves not found at {_CURVES_PATH}. "
            "Expected data/physical/wri_vulnerability_curves.json in project root."
        )
    with _CURVES_PATH.open(encoding="utf-8") as f:
        return json.load(f)


class WaterTemperatureModel:
    """WRI-based water temperature disruption model for once-through cooling.

    Estimates the annual fraction of time Samcheok Blue Power is forced to
    curtail or shut down due to intake seawater temperature exceeding design
    limits or regulatory discharge limits.

    Two curves are applied and the more restrictive result is returned:

    1. **WaterTemperature curve** (ΔT above design intake temp):
       Maps delta between projected summer peak SST and the plant's design
       intake temperature to a disruption fraction. ΔT is relative to
       ``DESIGN_INTAKE_TEMP_C`` (23.5°C, the 90th-percentile historical
       Samcheok summer SST), *not* the historical mean SST baseline used by
       ``TemperatureModel.cooling_water_derate``. This avoids double-counting:

       - ``cooling_water_derate`` (TemperatureModel) → SST rise from baseline
         → reduced thermal gradient → efficiency loss on the **fuel cost**
         channel.
       - ``WaterTemperatureModel`` → SST rise above *design limit* → forced
         curtailment on the **revenue** channel.

    2. **RegulatoryDischargeWaterLimit curve** (absolute intake temp °C):
       Maps projected absolute summer peak SST to regulatory shutdown risk
       (Korean environmental discharge temperature limits).

    Attributes:
        DESIGN_INTAKE_TEMP_C: Design intake temperature threshold (°C).
            Set to the 90th-percentile historical Samcheok summer SST.
        SUMMER_WARMING_FACTOR: Summer SST warming amplification relative to
            annual mean delta_t_sst (~20% greater warming in summer months).
    """

    DESIGN_INTAKE_TEMP_C: float = 23.5
    SUMMER_WARMING_FACTOR: float = 1.2

    def __init__(self, scenario: str = "RCP8.5") -> None:
        """Initialise the water temperature disruption model.

        Args:
            scenario: Climate scenario label passed to TemperatureModel.
                Supported values: ``"RCP4.5"``, ``"RCP8.5"``.
                Unknown values fall back to RCP8.5 (TemperatureModel default).
        """
        curves = _load_curves()["curves"]

        wt = curves["water_temperature"]
        self._wt_intensity: List[float] = wt["intensity"]
        self._wt_impact: List[float] = wt["impact_mean"]

        reg = curves["regulatory_discharge_limit"]
        self._reg_intensity: List[float] = reg["intensity"]
        self._reg_impact: List[float] = reg["impact_mean"]

        self._temp_model = TemperatureModel(
            rcp=scenario,
            cooling_type=CoolingType.ONCE_THROUGH,
        )

    def calculate_disruption(self, year: int) -> float:
        """Calculate annual water-temperature disruption fraction.

        Combines thermal exceedance and regulatory limit curves and returns
        the more restrictive result.

        Args:
            year: Projection year (e.g. 2030, 2050).

        Returns:
            Annual disruption fraction in [0.0, 1.0].
            0.0 means no water-temperature-driven curtailment; 1.0 means
            full-year forced shutdown.

        Example:
            >>> model = WaterTemperatureModel("RCP8.5")
            >>> model.calculate_disruption(2050)  # doctest: +SKIP
            0.0  # near-zero at current calibration
        """
        # Step 1: Get projected delta_t_sst for the year
        delta_t_sst = self._temp_model.get_delta_t_sst(year)

        # Step 2: Project summer peak SST
        # Summer warming is ~20% greater than the annual mean delta_t_sst
        projected_summer_peak = (
            SAMCHEOK_SST["summer_max"]
            + delta_t_sst * self.SUMMER_WARMING_FACTOR
        )

        # Step 3: Exceedance above design intake temperature
        delta_above_design = max(0.0, projected_summer_peak - self.DESIGN_INTAKE_TEMP_C)

        # Step 4: Thermal disruption from WaterTemperature curve
        # impact_mean is in disruption days/year → divide by 365 for fraction
        thermal_disruption = float(
            np.interp(delta_above_design, self._wt_intensity, self._wt_impact)
        ) / 365.0

        # Step 5: Regulatory disruption from RegulatoryDischargeWaterLimit curve
        regulatory_disruption = float(
            np.interp(projected_summer_peak, self._reg_intensity, self._reg_impact)
        ) / 365.0

        # Step 6: Return the binding (more restrictive) constraint
        return max(thermal_disruption, regulatory_disruption)


class AirTemperatureWRI:
    """WRI-based air temperature disruption model for cross-validation.

    Estimates annual disruption fraction from air temperature exceedance using
    the WRI AirTemperature vulnerability curve (Steam/Dry, closest available
    for USC coal — no OnceThrough-specific air temp curve exists in WRI).

    This class is intended for **cross-validation** against the existing
    ``TemperatureModel.calculate_efficiency_loss()`` which models air and
    cooling-water temperature effects on thermal efficiency (fuel cost channel).
    They measure related but distinct phenomena:

    - ``TemperatureModel`` → marginal efficiency loss from mean temperature
      rise → higher heat rate → higher fuel cost per MWh generated.
    - ``AirTemperatureWRI`` → peak temperature exceedance above design limit
      → forced curtailment events → revenue loss.

    .. warning::
        This class is **not wired into the cashflow engine** in the current
        implementation. It is provided for diagnostic comparison only.

    Attributes:
        DESIGN_AIR_TEMP_C: Design air temperature threshold (°C).
            Set to Samcheok's historical extreme heat threshold.
    """

    DESIGN_AIR_TEMP_C: float = 33.0

    def __init__(self, scenario: str = "RCP8.5") -> None:
        """Initialise the air temperature disruption model.

        Args:
            scenario: Climate scenario label passed to TemperatureModel.
                Supported values: ``"RCP4.5"``, ``"RCP8.5"``.
        """
        curves = _load_curves()["curves"]

        air = curves["air_temperature"]
        self._air_intensity: List[float] = air["intensity"]
        self._air_impact: List[float] = air["impact_mean"]

        self._temp_model = TemperatureModel(rcp=scenario)

    def calculate_disruption(self, year: int) -> float:
        """Calculate annual air-temperature disruption fraction.

        Uses the projected increase in maximum (peak) air temperature to
        estimate how often the plant is forced to curtail due to design air
        temperature limits being exceeded.

        Args:
            year: Projection year (e.g. 2030, 2050).

        Returns:
            Annual disruption fraction in [0.0, 1.0].

        Example:
            >>> model = AirTemperatureWRI("RCP8.5")
            >>> model.calculate_disruption(2050)  # doctest: +SKIP
            0.003  # illustrative
        """
        # Step 1: Get max_temp_increase for the year from projection table
        proj = self._temp_model._interpolate_projection(year)
        max_temp_increase = proj.max_temp_increase

        # Step 2: Projected peak temperature
        projected_peak = self.DESIGN_AIR_TEMP_C + max_temp_increase

        # Step 3: Exceedance above design air temperature
        # projected_peak - DESIGN_AIR_TEMP_C simplifies to max_temp_increase,
        # but written explicitly for clarity.
        delta_above_design = max(0.0, projected_peak - self.DESIGN_AIR_TEMP_C)

        # Step 4: Disruption fraction from AirTemperature curve
        # impact_mean is in disruption days/year → divide by 365 for fraction
        return float(
            np.interp(delta_above_design, self._air_intensity, self._air_impact)
        ) / 365.0
