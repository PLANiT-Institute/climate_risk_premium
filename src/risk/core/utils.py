"""
Utilities and helper functions for risk modeling.

This module provides common mathematical functions, validation utilities,
and helper methods used across multiple risk assessment components.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from typing import Dict, Any, List, Tuple, Optional, Union
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class ValidationResult:
    """Result of input validation."""
    is_valid: bool
    errors: List[str]
    warnings: List[str]
    
    def __bool__(self) -> bool:
        """Return True if validation passed."""
        return self.is_valid


def validate_financial_inputs(
    capacity_mw: float,
    ebitda: float,
    total_debt: float,
    cash_and_equivalents: float,
    total_equity: float,
    total_assets: float,
    fixed_assets: float,
    interest_expense: float,
) -> ValidationResult:
    """
    Validate financial inputs for credit rating assessment.
    
    Args:
        capacity_mw: Installed capacity in MW
        ebitda: Earnings before interest, taxes, depreciation, amortization
        total_debt: Total debt outstanding
        cash_and_equivalents: Cash and liquid assets
        total_equity: Total shareholder equity
        total_assets: Total assets
        fixed_assets: Property, plant & equipment
        interest_expense: Annual interest payments
        
    Returns:
        ValidationResult with any errors or warnings
    """
    errors = []
    warnings = []
    
    # Basic validity checks
    if capacity_mw <= 0:
        errors.append("Capacity must be positive")
    
    if fixed_assets <= 0:
        errors.append("Fixed assets must be positive")
    
    if total_assets <= 0:
        errors.append("Total assets must be positive")
    
    if total_equity <= 0:
        errors.append("Total equity must be positive")
    
    # Warning conditions
    if ebitda < 0:
        warnings.append("Negative EBITDA indicates financial distress")
    
    if total_debt > total_assets:
        warnings.append("Debt exceeds total assets - high leverage")
    
    if interest_expense < 0:
        errors.append("Interest expense cannot be negative")
    
    if cash_and_equivalents < 0:
        errors.append("Cash cannot be negative")
    
    return ValidationResult(
        is_valid=len(errors) == 0,
        errors=errors,
        warnings=warnings,
    )


def interpolate_linear(
    x_values: np.ndarray,
    y_values: np.ndarray,
    x_target: float,
) -> float:
    """
    Perform linear interpolation between points.
    
    Args:
        x_values: Array of x coordinates
        y_values: Array of y coordinates
        x_target: Target x value for interpolation
        
    Returns:
        Interpolated y value at x_target
        
    Raises:
        ValueError: If arrays have different lengths or are empty
    """
    if len(x_values) != len(y_values):
        raise ValueError("x_values and y_values must have same length")
    
    if len(x_values) == 0:
        raise ValueError("Arrays cannot be empty")
    
    # Find the interval containing x_target
    if x_target <= x_values[0]:
        return y_values[0]
    if x_target >= x_values[-1]:
        return y_values[-1]
    
    # Find interpolation interval
    for i in range(len(x_values) - 1):
        if x_values[i] <= x_target <= x_values[i + 1]:
            x1, x2 = x_values[i], x_values[i + 1]
            y1, y2 = y_values[i], y_values[i + 1]
            
            # Linear interpolation
            t = (x_target - x1) / (x2 - x1)
            return y1 + t * (y2 - y1)
    
    # Should not reach here
    raise ValueError(f"Could not interpolate for x_target={x_target}")


def calculate_probability_of_default(
    rating_score: int,
    time_horizon_years: int = 1,
) -> float:
    """
    Convert rating score to probability of default.
    
    Based on historical default rates by rating category.
    Uses typical corporate default rates adjusted for time horizon.
    
    Args:
        rating_score: Rating score (1=AAA, 10=D)
        time_horizon_years: Time horizon for default calculation
        
    Returns:
        Annual probability of default (0-1)
    """
    # Annual default rates by rating (based on Moody's historical data)
    annual_default_rates = {
        1: 0.0001,   # AAA
        2: 0.0003,   # AA
        3: 0.0007,   # A
        4: 0.0020,   # BBB
        5: 0.0100,   # BB
        6: 0.0400,   # B
        7: 0.1500,   # CCC
        8: 0.3500,   # CC
        9: 0.6000,   # C
        10: 1.0000,  # D (already in default)
    }
    
    annual_pd = annual_default_rates.get(rating_score, 1.0)
    
    # Convert to cumulative probability over time horizon
    # Using independence assumption: P(default over N years) = 1 - (1 - PD)^N
    cumulative_pd = 1 - (1 - annual_pd) ** time_horizon_years
    
    return min(1.0, cumulative_pd)


def calculate_recovery_rate(
    rating_score: int,
    is_secured: bool = True,
) -> float:
    """
    Estimate recovery rate given default.
    
    Based on historical recovery rates by rating and security.
    
    Args:
        rating_score: Rating score (1=AAA, 10=D)
        is_secured: Whether debt is secured by assets
        
    Returns:
        Recovery rate (0-1)
    """
    # Base recovery rates by rating
    base_recovery_rates = {
        1: 0.70,   # AAA
        2: 0.65,   # AA
        3: 0.60,   # A
        4: 0.45,   # BBB
        5: 0.35,   # BB
        6: 0.25,   # B
        7: 0.15,   # CCC
        8: 0.10,   # CC
        9: 0.05,   # C
        10: 0.02,  # D
    }
    
    recovery = base_recovery_rates.get(rating_score, 0.10)
    
    # Adjust for security
    if is_secured:
        recovery = min(0.80, recovery * 1.3)  # Secured debt has higher recovery
    
    return max(0.0, min(1.0, recovery))


def calculate_credit_var(
    exposure_at_default: float,
    probability_of_default: float,
    recovery_rate: float,
    confidence_level: float = 0.95,
) -> float:
    """
    Calculate Credit Value at Risk (Credit VaR).
    
    Args:
        exposure_at_default: Exposure at default amount
        probability_of_default: Probability of default (0-1)
        recovery_rate: Recovery rate given default (0-1)
        confidence_level: Confidence level for VaR (0-1)
        
    Returns:
        Credit VaR at specified confidence level
    """
    # Loss given default
    lgd = 1 - recovery_rate
    
    # Expected loss
    expected_loss = exposure_at_default * probability_of_default * lgd
    
    # For Credit VaR, we assume binary outcome (default/no default)
    # VaR at confidence level c:
    # VaR = EAD * LGD if PD > (1-c), else 0
    
    if probability_of_default > (1 - confidence_level):
        # Default falls within tail
        credit_var = exposure_at_default * lgd
    else:
        # Default not in tail at this confidence level
        credit_var = 0.0
    
    return credit_var


def monte_carlo_rating_migration(
    initial_rating: int,
    years: int,
    num_simulations: int = 10000,
    transition_matrix: Optional[np.ndarray] = None,
) -> np.ndarray:
    """
    Simulate rating migrations using Monte Carlo method.
    
    Args:
        initial_rating: Initial rating score (1-10)
        years: Number of years to simulate
        num_simulations: Number of Monte Carlo simulations
        transition_matrix: Optional custom transition matrix
        
    Returns:
        Array of final ratings from simulations
    """
    if transition_matrix is None:
        # Default transition matrix (simplified)
        # Rows: current rating, Columns: next rating
        transition_matrix = np.array([
            # AAA  AA   A   BBB  BB   B    CCC  CC   C    D
            [0.92, 0.07, 0.01, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00],  # AAA
            [0.02, 0.90, 0.07, 0.01, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00],  # AA
            [0.00, 0.03, 0.88, 0.07, 0.01, 0.00, 0.00, 0.00, 0.00, 0.00],  # A
            [0.00, 0.00, 0.04, 0.84, 0.08, 0.02, 0.01, 0.00, 0.00, 0.01],  # BBB
            [0.00, 0.00, 0.00, 0.05, 0.75, 0.10, 0.05, 0.03, 0.01, 0.01],  # BB
            [0.00, 0.00, 0.00, 0.00, 0.06, 0.70, 0.10, 0.08, 0.04, 0.02],  # B
            [0.00, 0.00, 0.00, 0.00, 0.00, 0.07, 0.60, 0.15, 0.10, 0.08],  # CCC
            [0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.08, 0.55, 0.20, 0.17],  # CC
            [0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.10, 0.40, 0.50],  # C
            [0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 1.00],  # D
        ])
    
    # Normalize transition matrix (ensure rows sum to 1)
    transition_matrix = transition_matrix / transition_matrix.sum(axis=1, keepdims=True)
    
    # Array to store final ratings
    final_ratings = np.zeros(num_simulations, dtype=int)
    
    for sim in range(num_simulations):
        current_rating = initial_rating - 1  # Convert to 0-based index
        
        for year in range(years):
            # Sample next rating from transition probabilities
            next_rating = np.random.choice(10, p=transition_matrix[current_rating])
            current_rating = next_rating
            
            # If in default, stay in default
            if current_rating == 9:  # Rating D
                break
        
        final_ratings[sim] = current_rating + 1  # Convert back to 1-based
    
    return final_ratings


def format_financial_value(
    value: float,
    currency: str = "USD",
    units: str = "M",
    decimals: int = 2,
) -> str:
    """
    Format financial values for display.
    
    Args:
        value: Numeric value to format
        currency: Currency code
        units: Units (K=thousands, M=millions, B=billions)
        decimals: Number of decimal places
        
    Returns:
        Formatted string
    """
    if units == "K":
        formatted_value = value / 1_000
    elif units == "M":
        formatted_value = value / 1_000_000
    elif units == "B":
        formatted_value = value / 1_000_000_000
    else:
        formatted_value = value
    
    if abs(formatted_value) >= 1000:
        return f"{currency} {formatted_value:,.0f}{units}"
    else:
        return f"{currency} {formatted_value:,.{decimals}f}{units}"


def calculate_stress_factor(
    base_value: float,
    stress_scenario: str,
    severity_multiplier: float = 1.0,
) -> float:
    """
    Apply stress factor to base financial value.
    
    Args:
        base_value: Base financial value
        stress_scenario: Type of stress scenario
        severity_multiplier: Multiplier for stress severity (0-2+)
        
    Returns:
        Stressed value
    """
    # Base stress factors by scenario type
    stress_multipliers = {
        "mild": 0.95,      # 5% deterioration
        "moderate": 0.85,   # 15% deterioration
        "severe": 0.70,     # 30% deterioration
        "extreme": 0.50,    # 50% deterioration
    }
    
    base_factor = stress_multipliers.get(stress_scenario, 1.0)
    
    # Apply severity multiplier
    adjusted_factor = 1.0 - (1.0 - base_factor) * severity_multiplier
    
    return base_value * adjusted_factor


def validate_scenario_consistency(
    physical_adjustments: Dict[str, float],
    transition_adjustments: Dict[str, float],
) -> ValidationResult:
    """
    Validate consistency between physical and transition risk adjustments.
    
    Args:
        physical_adjustments: Dictionary of physical risk adjustments
        transition_adjustments: Dictionary of transition risk adjustments
        
    Returns:
        ValidationResult with consistency checks
    """
    errors = []
    warnings = []
    
    # Check for contradictory adjustments
    physical_capacity_impact = (
        physical_adjustments.get("capacity_derate", 0) +
        physical_adjustments.get("outage_rate", 0)
    )
    
    transition_capacity_impact = transition_adjustments.get("capacity_factor_reduction", 0)
    
    total_capacity_impact = physical_capacity_impact + transition_capacity_impact
    
    if total_capacity_impact > 0.8:
        warnings.append(f"Very high capacity reduction: {total_capacity_impact:.1%}")
    
    if total_capacity_impact > 1.0:
        errors.append(f"Capacity reduction exceeds 100%: {total_capacity_impact:.1%}")
    
    return ValidationResult(
        is_valid=len(errors) == 0,
        errors=errors,
        warnings=warnings,
    )


def log_risk_assessment(
    plant_id: str,
    scenario_name: str,
    baseline_rating: str,
    risk_rating: str,
    crp_bps: float,
) -> None:
    """
    Log risk assessment results for audit trail.
    
    Args:
        plant_id: Plant identifier
        scenario_name: Scenario name
        baseline_rating: Baseline credit rating
        risk_rating: Risk-adjusted credit rating
        crp_bps: Climate Risk Premium in basis points
    """
    logger.info(
        f"Risk Assessment - Plant: {plant_id}, Scenario: {scenario_name}, "
        f"Rating: {baseline_rating} → {risk_rating}, CRP: {crp_bps:.0f} bps"
    )