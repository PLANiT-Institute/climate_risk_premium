"""
Reporting and visualization helpers.
"""
from __future__ import annotations

from typing import Dict
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots


def plot_spreads(spread_table: pd.DataFrame):
    """
    Bar chart for debt spreads and CRP by scenario.
    Expects columns: scenario, debt_spread_bps, crp_bps.
    """
    fig = go.Figure()

    fig.add_trace(go.Bar(
        name="Debt Spread",
        x=spread_table["scenario"],
        y=spread_table["debt_spread_bps"],
        marker_color="indianred"
    ))

    if "crp_bps" in spread_table.columns:
        fig.add_trace(go.Bar(
            name="Climate Risk Premium",
            x=spread_table["scenario"],
            y=spread_table["crp_bps"],
            marker_color="lightseagreen"
        ))

    fig.update_layout(
        title="Debt Spreads and Climate Risk Premium by Scenario",
        xaxis_title="Scenario",
        yaxis_title="Basis Points (bps)",
        barmode="group",
        height=500,
    )

    return fig


def plot_cashflow_waterfall(cashflow_df: pd.DataFrame, scenario_name: str = ""):
    """
    Waterfall chart showing revenue breakdown to EBITDA.
    Expects columns: revenue, fuel_costs, variable_opex, fixed_opex, carbon_costs, lost_revenue_from_outages, ebitda
    """
    # Use first year or average
    if len(cashflow_df) > 0:
        row = cashflow_df.iloc[0]
    else:
        return go.Figure()

    revenue = row.get("revenue", 0) / 1e6
    fuel = -row.get("fuel_costs", 0) / 1e6
    var_opex = -row.get("variable_opex", 0) / 1e6
    fixed = -row.get("fixed_opex", 0) / 1e6
    carbon = -row.get("carbon_costs", 0) / 1e6
    outage = -row.get("lost_revenue_from_outages", 0) / 1e6
    ebitda = row.get("ebitda", 0) / 1e6

    fig = go.Figure(go.Waterfall(
        name="Cashflow", orientation="v",
        measure=["relative", "relative", "relative", "relative", "relative", "relative", "total"],
        x=["Revenue", "Fuel Costs", "Variable O&M", "Fixed O&M", "Carbon Costs", "Outage Costs", "EBITDA"],
        y=[revenue, fuel, var_opex, fixed, carbon, outage, ebitda],
        connector={"line": {"color": "rgb(63, 63, 63)"}},
    ))

    fig.update_layout(
        title=f"Annual Cash Flow Breakdown{' - ' + scenario_name if scenario_name else ''} (USD Million)",
        showlegend=False,
        height=500,
    )

    return fig


def plot_capacity_factor_trajectory(results_dict: Dict[str, pd.DataFrame]):
    """
    Line plot of capacity factor over time for multiple scenarios.
    results_dict: {scenario_name: cashflow_df}
    """
    fig = go.Figure()

    for scenario_name, df in results_dict.items():
        if "year" in df.columns and "capacity_factor" in df.columns:
            fig.add_trace(go.Scatter(
                x=df["year"],
                y=df["capacity_factor"] * 100,
                mode="lines+markers",
                name=scenario_name,
            ))

    fig.update_layout(
        title="Capacity Factor Trajectory by Scenario",
        xaxis_title="Year",
        yaxis_title="Capacity Factor (%)",
        height=500,
        hovermode="x unified",
    )

    return fig


def plot_npv_comparison(metrics_df: pd.DataFrame):
    """
    Bar chart comparing NPV and IRR across scenarios.
    Expects columns: scenario, npv_million, irr_pct
    """
    fig = make_subplots(
        rows=1, cols=2,
        subplot_titles=("NPV Comparison", "IRR Comparison"),
        specs=[[{"type": "bar"}, {"type": "bar"}]]
    )

    # NPV
    fig.add_trace(
        go.Bar(
            x=metrics_df["scenario"],
            y=metrics_df["npv_million"],
            name="NPV",
            marker_color="steelblue",
        ),
        row=1, col=1
    )

    # IRR
    fig.add_trace(
        go.Bar(
            x=metrics_df["scenario"],
            y=metrics_df["irr_pct"],
            name="IRR",
            marker_color="darkorange",
        ),
        row=1, col=2
    )

    fig.update_xaxes(title_text="Scenario", row=1, col=1)
    fig.update_xaxes(title_text="Scenario", row=1, col=2)
    fig.update_yaxes(title_text="NPV (USD Million)", row=1, col=1)
    fig.update_yaxes(title_text="IRR (%)", row=1, col=2)

    fig.update_layout(
        height=400,
        showlegend=False,
    )

    return fig


def plot_dscr_trajectory(results_dict: Dict[str, pd.DataFrame]):
    """
    Plot DSCR over time (if available in future enhancements).
    For now, placeholder.
    """
    fig = go.Figure()
    fig.update_layout(
        title="DSCR Trajectory (Future Enhancement)",
        xaxis_title="Year",
        yaxis_title="DSCR",
    )
    return fig


def plot_sensitivity_analysis(base_npv: float, sensitivities: Dict[str, float]):
    """
    Tornado chart for sensitivity analysis.
    sensitivities: {parameter_name: npv_impact}
    """
    params = list(sensitivities.keys())
    impacts = list(sensitivities.values())

    fig = go.Figure(go.Bar(
        x=impacts,
        y=params,
        orientation='h',
        marker_color='lightblue',
    ))

    fig.update_layout(
        title="NPV Sensitivity Analysis",
        xaxis_title="NPV Impact (USD Million)",
        yaxis_title="Parameter",
        height=400,
    )

    return fig
