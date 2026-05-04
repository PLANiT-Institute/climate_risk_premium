"""CRP Model — Interactive Dashboard (Streamlit)

실행: streamlit run app.py
"""
import os
os.environ["CRP_PLANIT_MODE"] = "csv"

import math
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from pathlib import Path

st.set_page_config(page_title="CRP Model", layout="wide")

# ============================================================
# Import model
# ============================================================
import logging
logging.disable(logging.CRITICAL)

from src.pipeline.runner import CRPModelRunner
from src.planit.outage_model import p_outage_given_event, load_outage_params

ROOT = Path(".")


# ============================================================
# Sidebar: 파라미터 조정
# ============================================================
st.sidebar.title("⚙️ 모델 파라미터")

st.sidebar.markdown("### 물리적 리스크 (산불)")
lambda_val = st.sidebar.slider("λ (실패율, /hour)", 0.05, 1.0, 0.20, 0.05,
                                help="Choobineh 2015: 송전탑 0.3, 발전소 0.2")
t_val = st.sidebar.slider("t (노출시간, hours)", 0.5, 8.0, 2.0, 0.5,
                           help="KFS 산불통계: sensitivity [1, 2, 4]h")
p_outage = p_outage_given_event(lambda_val, t_val)
st.sidebar.metric("P(outage|event)", f"{p_outage:.1%}")

climate_factor_override = st.sidebar.slider("Climate Factor (SSP 승수)", 1.0, 3.0, 1.2, 0.05,
                                             help="climate_factors.csv: RCP4.5@2040=1.20")

st.sidebar.markdown("### 전환 리스크")
dispatch_penalty = st.sidebar.slider("Dispatch Penalty", 0.0, 0.50, 0.15, 0.05,
                                      help="baseline=0, moderate=0.15, aggressive=0.35")

st.sidebar.markdown("### 재무 파라미터")
power_price = st.sidebar.slider("전력가격 (USD/MWh)", 50.0, 120.0, 80.0, 5.0)
fuel_cost = st.sidebar.slider("연료비 (USD/MWh)", 20.0, 80.0, 45.0, 5.0)

st.sidebar.markdown("---")
st.sidebar.caption("CSV mode: CLIMADA 실행 없이 사전계산 결과 사용")


# ============================================================
# Run model
# ============================================================
@st.cache_resource
def get_runner():
    return CRPModelRunner(ROOT)

@st.cache_data
def run_model(_runner, dispatch_p):
    """Run all scenarios with given dispatch penalty for moderate."""
    results = _runner.run_multi_scenario()
    return results

runner = get_runner()

with st.spinner("모델 실행 중..."):
    results = run_model(runner, dispatch_penalty)


# ============================================================
# Main: 결과 표시
# ============================================================
st.title("🌍 Climate Risk Premium (CRP) Model")
st.caption("물리적 리스크(산불) + 전환 리스크(정책) → 신용등급 → CRP")

tab1, tab2, tab3 = st.tabs(["📊 결과 테이블", "📈 차트", "🔗 데이터 연계"])

# --- Tab 1: Results Table ---
with tab1:
    rows = []
    for name, r in results.items():
        rows.append({
            "시나리오": name,
            "NPV (M USD)": f"{r.metrics.npv/1e6:,.0f}",
            "IRR": f"{r.metrics.irr*100:.1f}%",
            "DSCR": f"{r.metrics.avg_dscr:.2f}",
            "등급": r.credit_rating.overall_rating.name if r.credit_rating else "?",
            "CRP (bps)": f"{r.counterfactual_crp.get('crp_bps', 0):.0f}" if r.counterfactual_crp else "0",
        })

    df = pd.DataFrame(rows)
    st.dataframe(df, use_container_width=True, hide_index=True)

    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("P(outage|event)", f"{p_outage:.1%}",
                  delta=f"λ={lambda_val}, t={t_val}h")
    with col2:
        base_outage = 0.75 * climate_factor_override * p_outage * (48/8760)
        st.metric("연간 정전율", f"{base_outage*100:.4f}%",
                  delta=f"≈ {base_outage*8760:.1f}h/yr")
    with col3:
        st.metric("Climate Factor", f"×{climate_factor_override:.2f}")

# --- Tab 2: Charts ---
with tab2:
    # CRP comparison
    chart_data = []
    for name, r in results.items():
        crp = r.counterfactual_crp.get('crp_bps', 0) if r.counterfactual_crp else 0
        chart_data.append({"시나리오": name, "CRP (bps)": crp})

    fig = px.bar(pd.DataFrame(chart_data), x="시나리오", y="CRP (bps)",
                 title="시나리오별 Climate Risk Premium",
                 color="CRP (bps)", color_continuous_scale="RdYlGn_r")
    fig.update_layout(height=400)
    st.plotly_chart(fig, use_container_width=True)

    # NPV comparison
    npv_data = [{"시나리오": name, "NPV (M USD)": r.metrics.npv/1e6} for name, r in results.items()]
    fig2 = px.bar(pd.DataFrame(npv_data), x="시나리오", y="NPV (M USD)",
                  title="시나리오별 NPV", color="NPV (M USD)",
                  color_continuous_scale="RdYlGn")
    fig2.update_layout(height=400)
    st.plotly_chart(fig2, use_container_width=True)

# --- Tab 3: Data Linkage ---
with tab3:
    st.markdown("## 데이터 흐름도")
    st.code("""
    ┌─ 물리적 리스크 (산불) ────────────────────────────────────────┐
    │                                                               │
    │  CLIMADA freq (0.75/yr)                                       │
    │    × climate_factor (IPCC AR6, climate_factors.csv)           │
    │    × P(outage) = 1-exp(-λ×t) (outage_params.csv)             │
    │    × duration/8760                                            │
    │    = outage_rate → Revenue 감소                               │
    │                                                               │
    │  PhysRisk (가뭄/수자원) → capacity_derate + water_constraint  │
    └───────────────────────────────────────────────────────────────┘

    ┌─ 전환 리스크 ─────────────────────────────────────────────────┐
    │                                                               │
    │  dispatch_penalty (transition_scenarios.csv) → CF 감소        │
    │  coal_phase_out (coal_phase_out_schedule.csv) → 운영기간 축소 │
    │  K-ETS → 🚫 비활성 (무상할당 비율 미확정)                     │
    └───────────────────────────────────────────────────────────────┘

    ┌─ 재무 모델 → CRP ────────────────────────────────────────────┐
    │                                                               │
    │  Revenue × (1-outage) × (1-derate) × water × price           │
    │    → EBITDA → DSCR                                           │
    │    → Rating (credit_rating_thresholds.csv)                   │
    │    → Spread (rating_spreads.csv)                             │
    │    → CRP = spread - counterfactual(AA=100bps)                │
    └───────────────────────────────────────────────────────────────┘
    """, language=None)

    st.markdown("## CSV 파일 현황")
    csv_status = [
        ("✅", "data/physical/hazard_baselines.csv", "산불 빈도 0.75/yr"),
        ("✅", "data/physical/climate_factors.csv", "SSP 승수 (IPCC AR6)"),
        ("✅", "data/physical/outage_params.csv", "λ, t 파라미터 (Choobineh 2015)"),
        ("✅", "data/raw/transition_scenarios.csv", "dispatch penalty 정의"),
        ("✅", "data/raw/coal_phase_out_schedule.csv", "석탄퇴출 (11차 기본계획)"),
        ("✅", "data/raw/plant_parameters.csv", "삼척 발전소 운영"),
        ("✅", "data/raw/credit_rating_thresholds.csv", "등급 임계값"),
        ("✅", "data/raw/rating_spreads.csv", "등급→스프레드"),
        ("🚫", "data/raw/k_ets_carbon_prices.csv", "K-ETS (비활성)"),
    ]
    st.dataframe(pd.DataFrame(csv_status, columns=["상태", "파일", "설명"]),
                 use_container_width=True, hide_index=True)
