"""Climate Risk Premium — Streamlit Dashboard.

Single-process app: no HTTP server, no build step.
Run with:  uv run streamlit run dashboard/app.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# Ensure repo root is importable
_REPO = Path(__file__).parent.parent
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from dashboard.pipeline import run_pipeline

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

SCENARIO_LABELS: dict[str, str] = {
    "baseline": "Baseline",
    "moderate_transition": "Moderate Transition",
    "aggressive_transition": "Aggressive Transition",
    "korea_ndc": "Korea NDC",
    "net_zero_2050": "Net Zero 2050",
    "delayed_transition": "Delayed Transition",
    "high_ambition": "High Ambition",
    "no_carbon_baseline": "No-Carbon Baseline",
}

RATING_COLORS: dict[str, str] = {
    "AAA": "#16a34a", "AA": "#22c55e", "A": "#86efac",
    "BBB": "#fbbf24", "BB": "#f97316", "B": "#ef4444",
    "CCC": "#dc2626", "CC": "#b91c1c", "C": "#991b1b", "D": "#7f1d1d",
}

RATING_ORDER = ["AAA", "AA", "A", "BBB", "BB", "B", "CCC", "CC", "C", "D"]

SCENARIO_COLORS: dict[str, str] = {
    "baseline": "#0ea5e9",
    "moderate_transition": "#8b5cf6",
    "aggressive_transition": "#ef4444",
    "korea_ndc": "#10b981",
    "net_zero_2050": "#f59e0b",
    "delayed_transition": "#6366f1",
    "high_ambition": "#ec4899",
    "no_carbon_baseline": "#64748b",
}


def label(name: str) -> str:
    return SCENARIO_LABELS.get(name, name.replace("_", " ").title())


# ---------------------------------------------------------------------------
# Page helpers
# ---------------------------------------------------------------------------


def page_overview(data: dict) -> None:
    st.header("Overview")
    st.caption("Samcheok Blue Power — Transition Risk Analysis")

    plant = data["plant"]
    scenarios = data["scenarios"]
    df = pd.DataFrame(scenarios)

    baseline = next((s for s in scenarios if s["scenario"] == "baseline"), scenarios[0])
    no_carbon = next((s for s in scenarios if s["scenario"] == "no_carbon_baseline"), None)
    worst = min(scenarios, key=lambda s: s["npv_million"])
    highest_crp = max(scenarios, key=lambda s: s["crp_bps"])

    # Plant summary strip
    with st.expander("Plant Parameters", expanded=False):
        cols = st.columns(6)
        cols[0].metric("Capacity", f"{plant['capacity_mw']:,.0f} MW")
        cols[1].metric("Base CF", f"{plant['capacity_factor'] * 100:.0f}%")
        cols[2].metric("CAPEX", f"${plant['total_capex_million'] / 1000:.2f}B")
        cols[3].metric("Emissions", f"{plant['emissions_tco2_per_mwh']:.2f} tCO₂/MWh")
        cols[4].metric("Power Price", f"${plant['power_price_usd_per_mwh']:.0f}/MWh")
        cols[5].metric("Discount Rate", f"{plant['discount_rate'] * 100:.0f}%")

    st.divider()

    # Key metrics
    c1, c2, c3, c4 = st.columns(4)
    c1.metric(
        "Baseline NPV",
        f"${baseline['npv_million']:.0f}M",
        delta=f"Rating: {baseline['overall_rating']}",
    )
    c2.metric(
        "No-Carbon NPV",
        f"${no_carbon['npv_million']:.0f}M" if no_carbon else "—",
        delta=f"Rating: {no_carbon['overall_rating']}" if no_carbon else "",
    )
    c3.metric(
        "Worst Scenario NPV",
        f"${worst['npv_million']:.0f}M",
        delta=f"{label(worst['scenario'])}",
        delta_color="inverse",
    )
    c4.metric(
        "Max CRP",
        f"{highest_crp['crp_bps']:.0f} bps",
        delta=f"{label(highest_crp['scenario'])}",
        delta_color="inverse",
    )

    st.divider()

    col_left, col_right = st.columns(2)

    with col_left:
        st.subheader("Climate Risk Premium by Scenario")
        df_plot = df.copy()
        df_plot["label"] = df_plot["scenario"].map(label)
        df_plot["color"] = df_plot["overall_rating"].map(
            lambda r: RATING_COLORS.get(r, "#94a3b8")
        )
        fig = px.bar(
            df_plot.sort_values("crp_bps", ascending=True),
            x="crp_bps",
            y="label",
            orientation="h",
            color="overall_rating",
            color_discrete_map=RATING_COLORS,
            labels={"crp_bps": "CRP (bps)", "label": "", "overall_rating": "Rating"},
            text="crp_bps",
        )
        fig.update_traces(texttemplate="%{text:.0f}", textposition="outside")
        fig.update_layout(
            height=320,
            margin=dict(l=0, r=40, t=10, b=10),
            showlegend=True,
            legend=dict(title="Rating", orientation="h", y=-0.25),
        )
        st.plotly_chart(fig, width="stretch")

    with col_right:
        st.subheader("NPV by Scenario")
        fig2 = px.bar(
            df_plot.sort_values("npv_million", ascending=True),
            x="npv_million",
            y="label",
            orientation="h",
            color="overall_rating",
            color_discrete_map=RATING_COLORS,
            labels={"npv_million": "NPV ($M)", "label": "", "overall_rating": "Rating"},
            text="npv_million",
        )
        fig2.update_traces(texttemplate="%{text:.0f}", textposition="outside")
        fig2.update_layout(
            height=320,
            margin=dict(l=0, r=40, t=10, b=10),
            showlegend=False,
        )
        st.plotly_chart(fig2, width="stretch")


def page_scenarios(data: dict) -> None:
    st.header("Scenario Comparison")
    st.caption("All scenarios ranked by Climate Risk Premium")

    scenarios = data["scenarios"]
    df = pd.DataFrame(scenarios)
    df["Scenario"] = df["scenario"].map(label)
    df["Rating"] = df["overall_rating"]
    df["CRP (bps)"] = df["crp_bps"].round(0).astype(int)
    df["NPV ($M)"] = df["npv_million"].round(1)
    df["IRR (%)"] = df["irr_pct"].round(2)
    df["Avg DSCR"] = df["avg_dscr"].round(2)
    df["Min DSCR"] = df["min_dscr"].round(2)
    df["LLCR"] = df["llcr"].round(2)
    df["Dispatch Penalty"] = df["dispatch_penalty_pct"].apply(lambda x: f"{x:.0f}%")
    df["Carbon Cost ($M)"] = df["total_carbon_cost_million"].round(1)
    df["EBITDA avg ($M)"] = df["avg_ebitda_million"].round(1)
    df["Counterfactual"] = df["counterfactual_rating"]

    display_cols = [
        "Scenario", "Rating", "CRP (bps)", "NPV ($M)", "IRR (%)",
        "Avg DSCR", "Min DSCR", "LLCR", "Dispatch Penalty",
        "Carbon Cost ($M)", "EBITDA avg ($M)", "Counterfactual",
    ]

    # Color-code ratings
    def color_rating(val: str) -> str:
        color = RATING_COLORS.get(val, "#94a3b8")
        return f"background-color: {color}20; color: {color}; font-weight: bold"

    st.dataframe(
        df[display_cols].set_index("Scenario"),
        width="stretch",
    )

    st.divider()
    st.subheader("WACC Impact")
    col1, col2 = st.columns(2)
    with col1:
        fig = px.scatter(
            df,
            x="wacc_baseline_pct",
            y="wacc_adjusted_pct",
            text="Scenario",
            labels={
                "wacc_baseline_pct": "Baseline WACC (%)",
                "wacc_adjusted_pct": "Scenario WACC (%)",
            },
            title="WACC: Baseline vs. Scenario",
        )
        fig.update_traces(textposition="top center")
        fig.add_shape(
            type="line",
            x0=df["wacc_baseline_pct"].min() - 0.5,
            y0=df["wacc_baseline_pct"].min() - 0.5,
            x1=df["wacc_adjusted_pct"].max() + 0.5,
            y1=df["wacc_adjusted_pct"].max() + 0.5,
            line=dict(dash="dash", color="gray"),
        )
        st.plotly_chart(fig, width="stretch")
    with col2:
        fig2 = px.scatter(
            df,
            x="avg_dscr",
            y="crp_bps",
            text="Scenario",
            color="Rating",
            color_discrete_map=RATING_COLORS,
            labels={"avg_dscr": "Avg DSCR", "crp_bps": "CRP (bps)"},
            title="DSCR vs. CRP",
        )
        fig2.update_traces(textposition="top center")
        st.plotly_chart(fig2, width="stretch")


def page_cashflows(data: dict) -> None:
    st.header("Cashflow Analysis")

    debt_payoff_year = data["plant"]["debt_payoff_year"]
    scenario_names = list(data["cashflows"].keys())
    selected = st.selectbox(
        "Scenario",
        scenario_names,
        format_func=label,
        index=0,
    )

    # Clip year-axis charts to 2025–2050; summary metrics still use full life.
    YEAR_MIN, YEAR_MAX = 2025, 2050
    rows = data["cashflows"][selected]
    df_full = pd.DataFrame(rows)
    df = df_full[(df_full["year"] >= YEAR_MIN) & (df_full["year"] <= YEAR_MAX)].copy()

    # Summary metrics (over the full operating life, not the clipped window)
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Revenue", f"${df_full['revenue'].sum() / 1e9:.2f}B")
    c2.metric("Total Carbon Cost", f"${df_full['carbon_costs'].sum() / 1e9:.2f}B")
    c3.metric("Avg EBITDA/yr", f"${df_full['ebitda'].mean() / 1e6:.0f}M")
    c4.metric("Avg DSCR", f"{df_full['dscr'].mean():.2f}x")

    st.divider()

    # Revenue vs. cost waterfall
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Revenue & EBITDA")
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=df["year"], y=df["revenue"] / 1e6,
            name="Revenue", fill="tonexty", line=dict(color="#10b981"),
        ))
        fig.add_trace(go.Scatter(
            x=df["year"], y=df["total_costs"] / 1e6,
            name="Total Costs", fill="tonexty", line=dict(color="#ef4444"),
        ))
        fig.add_trace(go.Scatter(
            x=df["year"], y=df["ebitda"] / 1e6,
            name="EBITDA", line=dict(color="#3b82f6", width=2.5),
        ))
        fig.add_trace(go.Scatter(
            x=df["year"], y=df["free_cash_flow"] / 1e6,
            name="Free Cash Flow", line=dict(color="#8b5cf6", width=2.5, dash="dash"),
        ))
        fig.add_hline(y=0, line_dash="dot", line_color="gray", line_width=1)
        fig.update_layout(
            height=360, margin=dict(l=0, r=0, t=10, b=10),
            yaxis_title="USD million / year",
            legend=dict(orientation="h", y=-0.25),
        )
        st.plotly_chart(fig, width="stretch")

    with col2:
        st.subheader("Cost Breakdown")
        fig2 = go.Figure()
        for col, name, color in [
            ("fuel_costs", "Fuel", "#f97316"),
            ("fixed_opex", "Fixed O&M", "#6366f1"),
            ("variable_opex", "Variable O&M", "#a78bfa"),
            ("carbon_costs", "Carbon (K-ETS)", "#ef4444"),
        ]:
            fig2.add_trace(go.Bar(
                x=df["year"], y=df[col] / 1e6,
                name=name, marker_color=color,
            ))
        fig2.update_layout(
            barmode="stack", height=360,
            margin=dict(l=0, r=0, t=10, b=10),
            yaxis_title="USD million / year",
            legend=dict(orientation="h", y=-0.25),
        )
        st.plotly_chart(fig2, width="stretch")

    st.divider()
    st.subheader("DSCR & Capacity Factor")
    col3, col4 = st.columns(2)
    with col3:
        fig3 = go.Figure()
        fig3.add_trace(go.Scatter(
            x=df["year"], y=df["dscr"],
            name="DSCR", line=dict(color="#0ea5e9", width=2),
            fill="tozeroy", fillcolor="rgba(14,165,233,0.1)",
        ))
        fig3.add_hline(y=1.0, line_dash="dash", line_color="#ef4444",
                       annotation_text="DSCR = 1.0", annotation_position="right")
        fig3.add_hline(y=1.25, line_dash="dot", line_color="#f59e0b",
                       annotation_text="DSCR = 1.25", annotation_position="right")
        fig3.add_vline(
            x=debt_payoff_year + 0.5,
            line_dash="dot", line_color="#64748b", line_width=1,
            annotation_text="Debt fully repaid",
            annotation_position="top left",
            annotation_font_size=10,
        )
        fig3.update_layout(
            height=280, margin=dict(l=0, r=60, t=10, b=10),
            yaxis_title="DSCR (×)",
        )
        st.plotly_chart(fig3, width="stretch")

    with col4:
        fig4 = go.Figure()
        fig4.add_trace(go.Scatter(
            x=df["year"], y=df["capacity_factor"] * 100,
            name="Effective CF", line=dict(color="#8b5cf6", width=2),
            fill="tozeroy", fillcolor="rgba(139,92,246,0.1)",
        ))
        fig4.update_layout(
            height=280, margin=dict(l=0, r=0, t=10, b=10),
            yaxis_title="Capacity Factor (%)",
        )
        st.plotly_chart(fig4, width="stretch")

    # Multi-scenario overlay (clipped to 2025–2050)
    st.divider()
    st.subheader("Multi-Scenario EBITDA Comparison")
    all_dfs = []
    for sname, rows in data["cashflows"].items():
        tmp = pd.DataFrame(rows)
        tmp = tmp[(tmp["year"] >= YEAR_MIN) & (tmp["year"] <= YEAR_MAX)]
        tmp["scenario_label"] = label(sname)
        all_dfs.append(tmp)
    all_cf = pd.concat(all_dfs)
    fig5 = px.line(
        all_cf, x="year", y=all_cf["ebitda"] / 1e6,
        color="scenario_label",
        color_discrete_map={label(k): v for k, v in SCENARIO_COLORS.items()},
        labels={"y": "EBITDA ($M)", "year": "Year", "scenario_label": "Scenario"},
    )
    fig5.add_hline(y=0, line_dash="dot", line_color="gray", line_width=1)
    fig5.update_layout(
        height=340, margin=dict(l=0, r=0, t=10, b=10),
        legend=dict(orientation="h", y=-0.25),
    )
    st.plotly_chart(fig5, width="stretch")


def page_credit(data: dict) -> None:
    st.header("Credit Rating Analysis")
    st.caption("KIS-methodology ratings and DSCR trajectories")

    ratings = data["ratings"]
    scenarios_list = data["scenarios"]
    debt_payoff_year = data["plant"]["debt_payoff_year"]
    df_r = pd.DataFrame(ratings)

    # DSCR trajectories
    st.subheader("DSCR Trajectories")
    all_scenarios = df_r["scenario"].unique().tolist()
    selected_scenarios = st.multiselect(
        "Select scenarios",
        all_scenarios,
        default=all_scenarios,
        format_func=label,
    )
    df_sel = df_r[df_r["scenario"].isin(selected_scenarios)].copy()
    df_sel["label"] = df_sel["scenario"].map(label)

    fig = px.line(
        df_sel, x="year", y="dscr",
        color="label",
        color_discrete_map={label(k): v for k, v in SCENARIO_COLORS.items()},
        labels={"dscr": "DSCR (×)", "year": "Year", "label": "Scenario"},
    )
    fig.add_hline(y=1.0, line_dash="dash", line_color="#ef4444",
                  annotation_text="1.0×", annotation_position="top right")
    fig.add_hline(y=1.25, line_dash="dot", line_color="#f59e0b",
                  annotation_text="1.25×", annotation_position="top right")
    fig.add_vline(
        x=debt_payoff_year + 0.5,
        line_dash="dot", line_color="#64748b", line_width=1,
        annotation_text="Debt fully repaid",
        annotation_position="top left",
        annotation_font_size=10,
    )
    fig.update_layout(
        height=340, margin=dict(l=0, r=60, t=10, b=10),
        legend=dict(orientation="h", y=-0.25),
    )
    st.plotly_chart(fig, width="stretch")

    st.divider()

    # Credit spread over time
    st.subheader("Credit Spread Trajectories")
    fig2 = px.line(
        df_sel, x="year", y="spread_bps",
        color="label",
        color_discrete_map={label(k): v for k, v in SCENARIO_COLORS.items()},
        labels={"spread_bps": "Spread (bps)", "year": "Year", "label": "Scenario"},
    )
    fig2.update_layout(
        height=300, margin=dict(l=0, r=0, t=10, b=10),
        legend=dict(orientation="h", y=-0.25),
    )
    st.plotly_chart(fig2, width="stretch")

    st.divider()

    # Rating component table (scenario-level)
    st.subheader("Rating Component Summary")
    df_s = pd.DataFrame(scenarios_list)
    df_s["Scenario"] = df_s["scenario"].map(label)
    display = df_s[[
        "Scenario", "overall_rating", "dscr_rating",
        "coverage_rating", "profitability_rating", "equity_leverage_rating",
        "avg_dscr", "spread_bps",
    ]].rename(columns={
        "overall_rating": "Overall",
        "dscr_rating": "DSCR",
        "coverage_rating": "Coverage",
        "profitability_rating": "Profitability",
        "equity_leverage_rating": "Leverage",
        "avg_dscr": "Avg DSCR",
        "spread_bps": "Spread (bps)",
    }).set_index("Scenario")
    st.dataframe(display, width="stretch")

    st.divider()

    # Rating migration heatmap — clipped to 2025–2050 per user request
    st.subheader("Rating Migration Heatmap")
    HEATMAP_YEAR_MIN, HEATMAP_YEAR_MAX = 2025, 2050
    df_heatmap = df_r[
        df_r["scenario"].isin(selected_scenarios)
        & (df_r["year"] >= HEATMAP_YEAR_MIN)
        & (df_r["year"] <= HEATMAP_YEAR_MAX)
    ].copy()
    pivot = df_heatmap.pivot(index="year", columns="scenario", values="rating")
    pivot.columns = [label(c) for c in pivot.columns]
    pivot = pivot.sort_index()

    years_str = [str(int(y)) for y in pivot.index]
    scenarios_list_hm = list(pivot.columns)
    n_years = len(years_str)
    n_scens = len(scenarios_list_hm)

    rating_num = {r: i for i, r in enumerate(RATING_ORDER)}
    pivot_num = pivot.map(lambda x: rating_num.get(x, 9) if pd.notna(x) else 9)

    colorscale = [
        [i / max(1, len(RATING_ORDER) - 1), RATING_COLORS[r]]
        for i, r in enumerate(RATING_ORDER)
    ]

    # Use integer x/y positions — Plotly distributes cells evenly.
    # Tick labels are applied separately via tickvals/ticktext.
    # customdata[row, col] = [year_str, scenario_name, rating_str] for hover.
    customdata_3d = np.empty((n_scens, n_years, 3), dtype=object)
    annotations = []
    for r_idx, scen_name in enumerate(scenarios_list_hm):
        for c_idx, year_s in enumerate(years_str):
            text_val = pivot.iloc[c_idx, r_idx]
            rating_s = text_val if pd.notna(text_val) else ""
            customdata_3d[r_idx, c_idx] = [year_s, scen_name, rating_s]
            annotations.append(dict(
                x=c_idx, y=r_idx,
                text=rating_s,
                showarrow=False,
                font=dict(size=8, color="white"),
            ))

    fig3 = go.Figure(data=go.Heatmap(
        z=pivot_num.T.values,        # shape: (n_scens, n_years)
        colorscale=colorscale,
        zmin=0,
        zmax=len(RATING_ORDER) - 1,
        showscale=False,
        customdata=customdata_3d,
        hovertemplate="Year: %{customdata[0]}<br>Scenario: %{customdata[1]}<br>Rating: %{customdata[2]}<extra></extra>",
    ))
    fig3.update_layout(
        height=max(200, n_scens * 40 + 60),
        margin=dict(l=0, r=0, t=10, b=10),
        annotations=annotations,
        xaxis=dict(
            tickmode="array",
            tickvals=list(range(n_years)),
            ticktext=years_str,
            tickangle=45,
            title="Year",
        ),
        yaxis=dict(
            tickmode="array",
            tickvals=list(range(n_scens)),
            ticktext=scenarios_list_hm,
            title="Scenario",
        ),
    )
    st.plotly_chart(fig3, width="stretch")


def page_risk_decomposition(data: dict) -> None:
    st.header("Risk Decomposition")
    st.caption("Transition risk value destruction across policy scenarios")

    scenarios = data["scenarios"]
    cashflows = data["cashflows"]

    no_carbon = next((s for s in scenarios if s["scenario"] == "no_carbon_baseline"), None)
    carbon_scenarios = [s for s in scenarios if s["scenario"] != "no_carbon_baseline"]
    no_carbon_npv = no_carbon["npv_million"] if no_carbon else 0.0

    st.warning(
        "**Why CRP is identical for all carbon scenarios:** The KIS rating model floors at **D** "
        "(default) whenever cumulative EBITDA is negative, regardless of severity. All 7 carbon "
        "scenarios hit this floor, so `spread(D) − spread(A) = 3,950 bps` for every one of them. "
        "The real differentiation is in **NPV loss** and **cumulative carbon cost** — shown below."
    )

    # Key anchors
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("No-Carbon NPV", f"${no_carbon_npv:.0f}M",
              help="Plant without any carbon costs — the structural value floor")
    c2.metric("No-Carbon Rating", no_carbon["overall_rating"] if no_carbon else "—")
    worst = min(carbon_scenarios, key=lambda s: s["npv_million"])
    c3.metric("Worst NPV", f"${worst['npv_million']:.0f}M",
              delta=label(worst["scenario"]), delta_color="inverse")
    c4.metric("Max NPV Destruction",
              f"${no_carbon_npv - worst['npv_million']:.0f}M",
              delta="vs. no-carbon baseline", delta_color="inverse")

    st.divider()

    # --- NPV Loss decomposition (the real differentiation) ---
    st.subheader("NPV Loss vs. No-Carbon Baseline")
    st.caption(
        "How much value each carbon scenario destroys relative to the no-carbon counterfactual. "
        "This is the economically meaningful measure when all scenarios share the same D rating."
    )

    decomp_npv = []
    for s in sorted(carbon_scenarios, key=lambda x: x["npv_million"]):
        npv_loss = no_carbon_npv - s["npv_million"]
        total_carbon = s["total_carbon_cost_million"]
        other_loss = npv_loss - total_carbon  # dispatch penalty / CF reduction
        decomp_npv.append({
            "label": label(s["scenario"]),
            "npv_loss": round(npv_loss, 0),
            "Carbon cost (cumulative)": round(total_carbon, 0),
            "Dispatch penalty / CF loss": round(max(0.0, other_loss), 0),
        })

    df_npv = pd.DataFrame(decomp_npv)

    col_l, col_r = st.columns(2)
    with col_l:
        fig = go.Figure()
        fig.add_trace(go.Bar(
            y=df_npv["label"], x=df_npv["Carbon cost (cumulative)"],
            name="Carbon cost (K-ETS)", orientation="h", marker_color="#ef4444",
        ))
        fig.add_trace(go.Bar(
            y=df_npv["label"], x=df_npv["Dispatch penalty / CF loss"],
            name="Dispatch penalty / lower CF", orientation="h", marker_color="#8b5cf6",
        ))
        fig.update_layout(
            barmode="stack", height=320,
            margin=dict(l=0, r=0, t=10, b=10),
            xaxis_title="NPV loss vs. no-carbon baseline ($M)",
            legend=dict(orientation="h", y=-0.28),
        )
        st.plotly_chart(fig, width="stretch")

    with col_r:
        # Scatter: carbon cost vs dispatch penalty contribution
        fig2 = px.scatter(
            df_npv,
            x="Carbon cost (cumulative)",
            y="Dispatch penalty / CF loss",
            text="label",
            labels={
                "Carbon cost (cumulative)": "Cumulative Carbon Cost ($M)",
                "Dispatch penalty / CF loss": "Dispatch Penalty Loss ($M)",
            },
            color_discrete_sequence=["#8b5cf6"],
        )
        fig2.update_traces(textposition="top center", marker_size=10)
        fig2.update_layout(
            height=320, margin=dict(l=0, r=0, t=10, b=10),
        )
        st.plotly_chart(fig2, width="stretch")

    st.divider()

    # --- Carbon cost time series (clipped to 2025–2050) ---
    st.subheader("Annual Carbon Cost by Scenario")
    YEAR_MIN, YEAR_MAX = 2025, 2050
    all_cf = []
    for sname, rows in cashflows.items():
        if sname == "no_carbon_baseline":
            continue
        for r in rows:
            if YEAR_MIN <= r["year"] <= YEAR_MAX:
                all_cf.append({"year": r["year"], "scenario": label(sname),
                               "carbon_costs": r["carbon_costs"] / 1e6})
    df_cc = pd.DataFrame(all_cf)
    fig3 = px.line(
        df_cc, x="year", y="carbon_costs", color="scenario",
        color_discrete_map={label(k): v for k, v in SCENARIO_COLORS.items()},
        labels={"carbon_costs": "Carbon Cost ($M/yr)", "year": "Year", "scenario": "Scenario"},
    )
    fig3.update_layout(
        height=300, margin=dict(l=0, r=0, t=10, b=10),
        legend=dict(orientation="h", y=-0.25),
    )
    st.plotly_chart(fig3, width="stretch")

    st.divider()

    # --- Year EBITDA first goes negative (scenario stress onset) ---
    st.subheader("Scenario Stress Timeline")
    st.caption("Year in which EBITDA first turns negative — earlier = more severe transition stress")
    onset = []
    for sname, rows in cashflows.items():
        if sname == "no_carbon_baseline":
            continue
        first_neg = next((r["year"] for r in rows if r["ebitda"] < 0), None)
        s = next((x for x in scenarios if x["scenario"] == sname), {})
        onset.append({
            "Scenario": label(sname),
            "EBITDA turns negative": first_neg if first_neg else "Never",
            "Dispatch penalty": f"{s.get('dispatch_penalty_pct', 0):.0f}%",
            "NPV ($M)": f"{s.get('npv_million', 0):.0f}",
            "Carbon cost ($M)": f"{s.get('total_carbon_cost_million', 0):.0f}",
            "CRP (bps)": f"{s.get('crp_bps', 0):.0f}",
            "Rating": s.get("overall_rating", "—"),
        })
    onset.sort(key=lambda x: x["EBITDA turns negative"] if isinstance(x["EBITDA turns negative"], int) else 9999)
    st.dataframe(pd.DataFrame(onset).set_index("Scenario"), width="stretch")


def page_physical_risk(data: dict) -> None:
    """Show wildfire outage trajectories for all physical scenarios side by side."""
    from src.risk.physical import build_physical_adjustments

    st.header("Physical Risk — Wildfire")
    st.caption("Wildfire outage rates across all physical scenarios")

    # Load all 4 physical scenarios directly (no user selector)
    PHYSICAL_SCENARIOS = [
        ("baseline",          "Baseline (SSP1-2.6)",    "#22c55e"),
        ("moderate_physical", "Moderate (SSP2-4.5)",    "#f59e0b"),
        ("high_physical",     "High (SSP5-8.5)",        "#ef4444"),
        ("severe_drought",    "Severe Drought (SSP5-8.5)", "#7c3aed"),
    ]

    # Use start_year and n_years consistent with the pipeline
    plant = data["plant"]
    start_year = 2025
    n_years = plant["operating_years"]
    anchor_years = [2025, 2030, 2050, 2100]

    scenarios_data = {}
    for sc_name, _label, _color in PHYSICAL_SCENARIOS:
        adj = build_physical_adjustments(
            start_year=start_year,
            n_years=n_years,
            physical_scenario=sc_name,
        )
        scenarios_data[sc_name] = adj

    ref_adj = scenarios_data["high_physical"]
    years = ref_adj.years

    def rate_at(adj, field: str, yr: int) -> float:
        arr = getattr(adj, field)
        return float(np.interp(yr, years, arr))

    # ── Key metrics (high_physical at 2050) ─────────────────────────────────
    hp = scenarios_data["high_physical"]
    p50  = rate_at(hp, "outage_rates", 2050)
    t50  = rate_at(hp, "transmission_outage_rates", 2050)
    comb50 = 1 - (1 - p50) * (1 - t50)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Base frequency", "0.30 events/yr", help="6 events / 20-year window (NASA FIRMS)")
    c2.metric("Plant outage 2050 (high)", f"{p50 * 100:.4f}%")
    c3.metric("Transmission outage 2050 (high)", f"{t50 * 100:.4f}%")
    c4.metric("Combined outage 2050 (high)", f"{comb50 * 100:.4f}%",
              help="1 − (1 − plant) × (1 − transmission)")

    st.divider()

    # ── Outage trajectories — all scenarios ─────────────────────────────────
    col_l, col_r = st.columns(2)

    with col_l:
        st.subheader("Plant Outage Rate — All Scenarios")
        fig_p = go.Figure()
        for sc_name, sc_label, color in PHYSICAL_SCENARIOS:
            adj = scenarios_data[sc_name]
            fig_p.add_trace(go.Scatter(
                x=years, y=adj.outage_rates * 100,
                name=sc_label, line=dict(color=color, width=2),
            ))
        fig_p.update_layout(
            height=320, margin=dict(l=0, r=0, t=10, b=10),
            yaxis_title="Outage rate (%/yr)",
            legend=dict(orientation="h", y=-0.3),
        )
        st.plotly_chart(fig_p, width="stretch")

    with col_r:
        st.subheader("Transmission Outage Rate — All Scenarios")
        fig_t = go.Figure()
        for sc_name, sc_label, color in PHYSICAL_SCENARIOS:
            adj = scenarios_data[sc_name]
            fig_t.add_trace(go.Scatter(
                x=years, y=adj.transmission_outage_rates * 100,
                name=sc_label, line=dict(color=color, width=2, dash="dash"),
            ))
        fig_t.update_layout(
            height=320, margin=dict(l=0, r=0, t=10, b=10),
            yaxis_title="Outage rate (%/yr)",
            legend=dict(orientation="h", y=-0.3),
        )
        st.plotly_chart(fig_t, width="stretch")

    st.divider()

    # ── Anchor-year summary table ────────────────────────────────────────────
    st.subheader("Outage Rates at Key Years")
    table_rows = []
    for sc_name, sc_label, _ in PHYSICAL_SCENARIOS:
        adj = scenarios_data[sc_name]
        for yr in anchor_years:
            p = rate_at(adj, "outage_rates", yr)
            t = rate_at(adj, "transmission_outage_rates", yr)
            table_rows.append({
                "Scenario": sc_label,
                "Year": yr,
                "Plant (%/yr)": round(p * 100, 5),
                "Transmission (%/yr)": round(t * 100, 5),
                "Combined (%/yr)": round((1 - (1 - p) * (1 - t)) * 100, 5),
                "Plant hrs/yr": round(p * 8760, 3),
            })
    df_table = pd.DataFrame(table_rows)
    st.dataframe(df_table.set_index(["Scenario", "Year"]), width="stretch")

    st.divider()

    # ── Scenario descriptions ────────────────────────────────────────────────
    st.subheader("Scenario Definitions")
    meta = data.get("physical_meta", [])
    if meta:
        df_meta = pd.DataFrame(meta)
        df_meta.columns = [c.title() for c in df_meta.columns]
        st.dataframe(df_meta.set_index("Scenario"), width="stretch")

    st.divider()

    # ── Data sources ─────────────────────────────────────────────────────────
    with st.expander("Data sources & methodology"):
        st.markdown("""
**Hazard frequency** — NASA FIRMS MODIS active fire detections at Samcheok
(37.44 °N, 129.17 °E), queried via CLIMADA.  6 wildfire events over 20 years
(2001–2020) → 0.30 events/year.  Source: `data/physical_risk/climada_data.csv`.

**Outage probabilities and durations** — from `data/physical_risk/model_assumptions.csv`.
Edit that file to change default values (no code change required).

**Climate amplification factors** — from WWA (2025) analysis of South Korean
wildfire likelihood.  Wildfire is ~2× more likely under current 1.3 °C warming,
and ~4× more likely under end-of-century RCP 8.5.
Anchor values stored in `data/physical_risk/literature_data.csv` (WILDFIRE category).

**SSP wildfire scaling** relative to RCP 8.5 full intensity:
| Scenario | SSP | Scale |
|----------|-----|-------|
| baseline | SSP1-2.6 | 30 % |
| moderate_physical | SSP2-4.5 | 60 % |
| high_physical | SSP5-8.5 | 100 % |
| severe_drought | SSP5-8.5 | 100 % |

Temperature/drought efficiency-loss and capacity-derate channels are not yet
activated — they will be added in a future release.
""")


def page_model_pipeline(data: dict) -> None:
    st.header("Model Pipeline")
    st.caption("End-to-end data flow from input parameters to Climate Risk Premium")

    plant = data["plant"]

    tab1, tab2, tab3, tab4 = st.tabs(["Input Data", "Transition Risk", "Cashflow Model", "Credit & CRP"])

    with tab1:
        st.subheader("Plant Parameters")
        cols = st.columns(3)
        cols[0].metric("Plant", plant["name"])
        cols[0].metric("Capacity", f"{plant['capacity_mw']:,.0f} MW")
        cols[1].metric("Base CF", f"{plant['capacity_factor'] * 100:.0f}%")
        cols[1].metric("Emissions", f"{plant['emissions_tco2_per_mwh']:.2f} tCO₂/MWh")
        cols[2].metric("CAPEX", f"${plant['total_capex_million'] / 1000:.2f}B")
        cols[2].metric("Discount Rate", f"{plant['discount_rate'] * 100:.0f}%")

        st.subheader("Scenario Definitions")
        df_s = pd.DataFrame(data["scenarios"])[["scenario", "description", "dispatch_penalty_pct", "retirement_years"]]
        df_s.columns = ["Scenario", "Description", "Dispatch Penalty (%)", "Life (yrs)"]
        st.dataframe(df_s.set_index("Scenario"), width="stretch")

    with tab2:
        st.subheader("Capacity Factor Adjustment")
        st.latex(r"CF_{eff}(t) = CF_{base} \times (1 - \text{dispatch\_penalty})")
        st.caption("dispatch_penalty is fixed per scenario (from policy.csv)")

        st.subheader("K-ETS Carbon Price Trajectory")
        st.latex(r"P_{carbon}(t) = \text{linear\_interp}(P_{2025}, P_{2030}, P_{2040}, P_{2050})")
        st.latex(r"C_{carbon}(t) = \text{MWh}(t) \times EF \times P_{carbon}(t)")

        st.subheader("Carbon Price Anchors by Scenario")
        anchor_data = [
            {
                "Scenario": label(s["scenario"]),
                "2025 ($/tCO₂)": s.get("carbon_price_2025", 0),
                "2030": s.get("carbon_price_2030", 0),
                "2040": s.get("carbon_price_2040", 0),
                "2050": s.get("carbon_price_2050", 0),
            }
            for s in data["scenarios"]
        ]
        st.dataframe(pd.DataFrame(anchor_data).set_index("Scenario"), width="stretch")

    with tab3:
        st.subheader("Revenue")
        st.latex(r"\text{Revenue}(t) = \text{Capacity} \times CF_{eff}(t) \times 8760 \times P_{elec}")

        st.subheader("Cost Components")
        cost_table = {
            "Component": ["Fuel", "Fixed O&M", "Variable O&M", "Carbon (K-ETS)"],
            "Formula": [
                "MWh × heat_rate × fuel_price",
                "$15 / kW-yr",
                "$3.5 / MWh",
                "MWh × EF × P_carbon(t)",
            ],
        }
        st.dataframe(pd.DataFrame(cost_table).set_index("Component"), width="stretch")

        st.subheader("EBITDA → Free Cash Flow")
        st.latex(r"EBITDA = Revenue - Fuel - O\&M_{fixed} - O\&M_{var} - C_{carbon}")
        st.latex(r"FCF = EBIT \times (1 - \tau) + Depreciation")
        st.latex(r"DSCR = \frac{CFADS}{\text{Debt Service}}")

        st.subheader("NPV")
        st.latex(r"NPV = \sum_{t=1}^{T} \frac{FCF_t}{(1+r)^t} - CAPEX")

    with tab4:
        st.subheader("KIS Rating Methodology")
        st.markdown("""
| Criterion | Weight | Key Metric |
|-----------|--------|-----------|
| Capacity / Scale | 15% | Plant MW → AAA for 2,100 MW |
| Profitability | 10% | EBITDA / Fixed Assets |
| Coverage | 12% | EBITDA / Interest |
| DSCR | 28% | CFADS / Debt Service |
| Net Debt Leverage | 15% | Net Debt / EBITDA |
| Equity Leverage | 20% | Debt / Equity |
        """)

        st.subheader("Climate Risk Premium")
        st.latex(r"CRP_{bps} = (WACC_{scenario} - WACC_{counterfactual}) \times 10^4")
        st.latex(
            r"WACC = d \times k_d(rating) + e \times k_e(\text{notch premium})"
        )
        st.caption(
            "Counterfactual = A-rated entity (no climate risk). "
            "Each notch downgrade adds ~0.5% equity premium and re-prices the debt spread."
        )

        st.subheader("Rating → Spread Mapping")
        spread_data = data["plant"]["rating_spreads"]
        df_sp = pd.DataFrame(
            [(r, s, "Investment" if r in ("AAA", "AA", "A", "BBB") else "Speculative/Default")
             for r, s in spread_data.items()],
            columns=["Rating", "Spread (bps)", "Grade"],
        )
        st.dataframe(df_sp.set_index("Rating"), width="stretch")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    st.set_page_config(
        page_title="Climate Risk Premium — Samcheok Blue Power",
        page_icon="🌏",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    with st.sidebar:
        st.title("🌏 CRP Dashboard")
        st.caption("Samcheok Blue Power\n2,100 MW Supercritical Coal")
        st.divider()

        page = st.radio(
            "Navigation",
            [
                "Overview",
                "Scenarios",
                "Cashflows",
                "Credit Rating",
                "Physical Risk",
                "Risk Decomposition",
                "Model Pipeline",
            ],
            label_visibility="collapsed",
        )
        st.divider()
        st.caption("Transition + Wildfire physical risk · v2.1")

    with st.spinner("Running pipeline…"):
        data = run_pipeline(
            risk_mode="all",
            physical_scenario="high_physical",
        )

    pages = {
        "Overview": page_overview,
        "Scenarios": page_scenarios,
        "Cashflows": page_cashflows,
        "Credit Rating": page_credit,
        "Physical Risk": page_physical_risk,
        "Risk Decomposition": page_risk_decomposition,
        "Model Pipeline": page_model_pipeline,
    }
    pages[page](data)


if __name__ == "__main__":
    main()
