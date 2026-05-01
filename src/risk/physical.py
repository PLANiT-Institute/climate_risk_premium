"""Physical risk data structures and CSV fallback loader.

Hazard computation is done via the PLANiT integration layer (src/planit/).
"""
from typing import Optional
from dataclasses import dataclass
import csv as _csv
from pathlib import Path as _Path
import numpy as np
import logging as _logging

_planit_logger = _logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Core data structures
# ---------------------------------------------------------------------------

@dataclass
class PhysicalAdjustments:
    """Physical risk adjustments for a single year/scenario."""
    outage_rate: float              # Fraction of time plant unavailable (wildfire/CLIMADA)
    capacity_derate: float          # Asset damage rate → O&M cost increase (drought/PhysRisk)
    efficiency_loss: float          # Heat rate increase fraction (temperature)
    water_constrained_capacity: float = 1.0  # Max CF from water availability (PhysRisk)
    notes: str = ""


@dataclass
class YearlyPhysicalAdjustments:
    """Year-by-year physical risk adjustments."""
    years: np.ndarray
    outage_rates: np.ndarray
    capacity_derates: np.ndarray
    efficiency_losses: np.ndarray
    water_constraints: np.ndarray
    scenario_name: str = ""

    def get_adjustment_for_year(self, year: int) -> PhysicalAdjustments:
        if year in self.years:
            idx = np.where(self.years == year)[0][0]
            return PhysicalAdjustments(
                outage_rate=self.outage_rates[idx],
                capacity_derate=self.capacity_derates[idx],
                efficiency_loss=self.efficiency_losses[idx],
                water_constrained_capacity=self.water_constraints[idx],
                notes=f"{self.scenario_name} year {year}"
            )
        return PhysicalAdjustments(0, 0, 0, 1.0, "Out of range")



def load_yearly_from_output_csv(
    start_year: int = 2025,
    end_year: int = 2060,
    csv_path: Optional[str] = None,
) -> YearlyPhysicalAdjustments:
    """Build YearlyPhysicalAdjustments by interpolating physical_risk_output.csv.

    Reads anchor rows (2024/2030/2050/2100) and linearly interpolates
    outage_rate and efficiency_loss for every year in [start_year, end_year].
    Falls back to zero adjustments if the file is missing.
    """
    if csv_path is None:
        csv_path = str(
            _Path(__file__).parent.parent.parent.parent
            / "data" / "physical_risk_steps" / "output" / "physical_risk_output.csv"
        )

    anchor_years: list = []
    anchor_outage: list = []
    anchor_efficiency: list = []

    try:
        with open(csv_path, newline="") as f:
            for row in _csv.DictReader(f):
                anchor_years.append(int(row["year"]))
                anchor_outage.append(float(row["total_acute_pct"]))
                anchor_efficiency.append(float(row["temp_total_pct"]))
    except FileNotFoundError:
        _planit_logger.warning(
            "physical_risk_output.csv not found at %s; returning zero adjustments", csv_path
        )
        years = np.arange(start_year, end_year + 1)
        n = len(years)
        return YearlyPhysicalAdjustments(
            years=years, outage_rates=np.zeros(n), capacity_derates=np.zeros(n),
            efficiency_losses=np.zeros(n), water_constraints=np.ones(n),
            scenario_name="physical_risk_output.csv not found",
        )

    all_years = np.arange(start_year, end_year + 1)
    outage_rates = np.interp(all_years, anchor_years, anchor_outage)
    efficiency_losses = np.interp(all_years, anchor_years, anchor_efficiency)
    n = len(all_years)

    return YearlyPhysicalAdjustments(
        years=all_years, outage_rates=outage_rates, capacity_derates=np.zeros(n),
        efficiency_losses=efficiency_losses, water_constraints=np.ones(n),
        scenario_name="physical_risk_output.csv (RCP8.5 interpolated)",
    )
