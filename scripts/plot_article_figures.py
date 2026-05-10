"""
Generate Figure 1 (credit rating trajectories) and Figure 2 (utilization rate trajectories)
for the Samcheok Blue Power climate risk article.

Output: results/figures/figure1_credit_ratings.png
        results/figures/figure2_utilization.png
"""
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

BASE = Path(__file__).parent.parent
RESULTS = BASE / "results"
FIGURES = RESULTS / "figures"
FIGURES.mkdir(exist_ok=True)

SCENARIOS = {
    "combined_moderate":   "Combined Moderate Scenario",
    "combined_aggressive": "Combined Aggressive Scenario",
    "enhanced_11th_plan":  "11차 전기본 Scenario",
}
COLORS = {
    "combined_moderate":   "#2196F3",
    "combined_aggressive": "#FF5722",
    "enhanced_11th_plan":  "#9C27B0",
}
# Rating scale — higher numeric = better credit quality
RATING_ORDER = ["D", "BB", "BBB", "A"]
RATING_NUM = {r: i + 1 for i, r in enumerate(RATING_ORDER)}


def _setup_font():
    plt.rcParams["axes.unicode_minus"] = False
    for name in ["Malgun Gothic", "NanumGothic", "AppleGothic"]:
        try:
            import matplotlib.font_manager as fm
            fm.findfont(fm.FontProperties(family=name), fallback_to_default=False)
            plt.rcParams["font.family"] = name
            return
        except Exception:
            continue
    print("경고: 한국어 폰트를 찾지 못했습니다.")


def plot_figure1() -> None:
    """신용등급 히트맵 — 연도×시나리오 색상 매핑 (2027–2050)."""
    import numpy as np
    from matplotlib.colors import BoundaryNorm, ListedColormap

    df = pd.read_csv(RESULTS / "yearly_ratings.csv")
    df = df[df["scenario"].isin(SCENARIOS)].copy()

    RATING_TO_NUM = {"D": 0, "BB": 1, "BBB": 2, "A": 3}
    TEXT_COLORS   = {0: "white", 1: "white", 2: "#333333", 3: "white"}
    df["rating_num"] = df["rating"].map(RATING_TO_NUM)

    scenarios = list(SCENARIOS.keys())
    all_years  = list(range(2027, 2051))   # 표시 범위: 2027–2050
    n_sc, n_yr = len(scenarios), len(all_years)

    matrix = np.full((n_sc, n_yr), np.nan)
    for i, sc in enumerate(scenarios):
        yr_to_rating = {int(r["year"]): r["rating_num"]
                        for _, r in df[df["scenario"] == sc].iterrows()}
        for j, yr in enumerate(all_years):
            if yr in yr_to_rating:
                matrix[i, j] = yr_to_rating[yr]

    CELL_COLORS = {0: "#E53935", 1: "#FB8C00", 2: "#FDD835", 3: "#43A047"}
    cmap = ListedColormap([CELL_COLORS[k] for k in range(4)])
    cmap.set_bad(color="#E0E0E0")
    norm = BoundaryNorm([-0.5, 0.5, 1.5, 2.5, 3.5], ncolors=4)

    fig, ax = plt.subplots(figsize=(13, 7.0))
    plt.subplots_adjust(top=0.90, bottom=0.52, left=0.15, right=0.97)

    X = np.arange(2027, 2052, dtype=float)   # 셀 경계 (25개 = 24열)
    Y = np.arange(n_sc + 1, dtype=float)
    ax.pcolormesh(X, Y, np.ma.masked_invalid(matrix),
                  cmap=cmap, norm=norm, edgecolors="white", linewidth=0.5)

    ax.set_ylim(n_sc, 0)
    ax.set_yticks(np.arange(n_sc) + 0.5)
    ax.set_yticklabels([SCENARIOS[sc] for sc in scenarios], fontsize=10.5)

    ax.set_xlim(2027, 2051)
    # 눈금을 셀 중앙(yr + 0.5)에 배치해야 연도가 정확히 정렬됨
    ax.set_xticks([yr + 0.5 for yr in range(2027, 2051, 2)])
    ax.set_xticklabels([str(y) for y in range(2027, 2051, 2)], fontsize=9)

    # 모든 셀에 등급 텍스트 표시
    yr_to_rating_str = {sc: {int(r["year"]): r["rating"]
                             for _, r in df[df["scenario"] == sc].iterrows()}
                        for sc in scenarios}
    for i, sc in enumerate(scenarios):
        for j, yr in enumerate(all_years):
            rating = yr_to_rating_str[sc].get(yr)
            if rating is not None:
                ax.text(yr + 0.5, i + 0.5, rating,
                        ha="center", va="center", fontsize=8, fontweight="bold",
                        color=TEXT_COLORS[RATING_TO_NUM[rating]])

    ax.set_title("시나리오별 신용등급 연도별 변화 분석",
                 fontsize=13, fontweight="bold", pad=10)

    # 하단 시나리오 주석 블록
    NOTES = [
        ("①", "Combined Moderate Scenario",
         "온건한 탈탄소 정책 전환과 낮은 수준의 물리적 리스크가 복합 적용된 시나리오.\n"
         "       초반 BB 투기등급에서 부채 상환이 진행되며 2041년부터 BBB 투자등급으로 회복."),
        ("②", "Combined Aggressive Scenario",
         "강화된 탄소규제와 높은 물리적 리스크가 복합 적용된 시나리오.\n"
         "       2049년까지 BB 투기등급이 지속되어 사실상 투자등급 회복이 어려운 구조."),
        ("③", "11차 전기본 Scenario",
         "제11차 전력수급기본계획의 석탄 감축 목표를 직접 반영한 시나리오.\n"
         "       이용률 급감에 따른 현금흐름 악화로 2039년 부도(D) 후 2040년 사업 조기종료."),
    ]
    y_start = 0.44   # 히트맵 하단과 간격 확보
    for k, (num, name, body) in enumerate(NOTES):
        prefix = "주: " if k == 0 else "    "
        fig.text(0.05, y_start - k * 0.085,
                 f"{prefix}{num} {name} — {body}",
                 fontsize=13, ha="left", va="top",
                 linespacing=1.5, transform=fig.transFigure)

    out = FIGURES / "figure1_credit_ratings.png"
    fig.savefig(out, dpi=300, bbox_inches="tight")
    plt.close()
    print(f"저장 완료: {out}")


def plot_figure2() -> None:
    """이용률 — 실적(월간 실선) + 시나리오 전망(연간 점선) 결합 선그래프.

    실적 데이터 출처: EPSIS/KPX 발전량 통계 (2025.01–2026.02)
    """
    # ── 실측 월간 이용률 (EPSIS/KPX) ─────────────────────────────────────
    # (연도, 월, 이용률%)  — 2025년 1월 상업운전 초기로 0% 기록
    ACTUAL = [
        (2025,  1,  0.000),
        (2025,  2,  9.666),
        (2025,  3, 14.216),
        (2025,  4, 10.211),
        (2025,  5, 12.542),
        (2025,  6, 34.862),
        (2025,  7, 45.242),
        (2025,  8, 40.604),
        (2025,  9, 21.576),
        (2025, 10, 18.173),
        (2025, 11, 23.989),
        (2025, 12,  6.250),
        (2026,  1, 14.588),
        (2026,  2, 20.702),
    ]
    actual_x = list(range(len(ACTUAL)))   # 0, 1, 2 … 13 (균등 1칸)
    actual_y = [util for _, _, util in ACTUAL]

    # ── 시나리오 전망 (cashflow CSV, 2027–) ──────────────────────────────
    cf_files = {
        "combined_moderate":   "cashflow_combined_moderate.csv",
        "combined_aggressive": "cashflow_combined_aggressive.csv",
        "enhanced_11th_plan":  "cashflow_enhanced_11th_plan.csv",
    }

    fig, ax = plt.subplots(figsize=(13, 5))

    # 실적 — 단일 실선
    ax.plot(actual_x, actual_y,
            color="#333333", linewidth=2, marker="o", markersize=4,
            label="실적 (월간, EPSIS/KPX)", zorder=5)

    # ── 인덱스 기반 균등 너비 축 ──────────────────────────────────────────
    # 실적: 0~13 (월별 1칸씩), 간격 1칸, 전망: 15~38 (연별 1칸씩)
    N_ACTUAL = len(ACTUAL)          # 14
    FORECAST_START = N_ACTUAL + 1   # 15 (gap=1)

    def year_to_idx(year: int) -> int:
        return FORECAST_START + (year - 2027)

    # 시나리오 전망 — 점선 3개
    for sc, label in SCENARIOS.items():
        df = pd.read_csv(RESULTS / cf_files[sc])
        if sc == "enhanced_11th_plan":
            df = df[df["year"] >= 2027].copy()          # 2040년 0% 포함
        else:
            df = df[(df["year"] >= 2027) & (df["capacity_factor"] > 0)].copy()
        pct  = df["capacity_factor"] * 100
        xpos = [year_to_idx(int(y)) for y in df["year"]]
        ax.plot(xpos, pct,
                color=COLORS[sc], linewidth=2.5, linestyle="--",
                label=label, zorder=4)

    # ── X축 틱 설정 ───────────────────────────────────────────────────────
    # 실적: 3개월마다 + 마지막 실적월
    act_tick_idx    = [0, 3, 6, 9, 12, 13]
    act_tick_labels = ["2025.1", "2025.4", "2025.7", "2025.10", "2026.1", "2026.2"]

    # 전망: 5년마다
    fcast_years     = [2027, 2030, 2035, 2040, 2045, 2050]
    fcast_tick_idx  = [year_to_idx(y) for y in fcast_years]
    fcast_labels    = [str(y) for y in fcast_years]

    all_ticks  = act_tick_idx  + fcast_tick_idx
    all_labels = act_tick_labels + fcast_labels

    total_end = year_to_idx(2050) + 0.5
    ax.set_xlim(-0.5, total_end)
    ax.set_xticks(all_ticks)
    ax.set_xticklabels(all_labels, fontsize=9, rotation=45, ha="right")

    # 실적/전망 구분 점선
    ax.axvline(N_ACTUAL - 0.5, color="gray", linestyle=":", linewidth=1, alpha=0.7)

    ax.set_ylim(0, 65)
    ax.yaxis.set_major_locator(plt.MultipleLocator(10))
    ax.set_ylabel("이용률 (%)", fontsize=12)
    ax.set_title("삼척블루파워 이용률 추이 및 시나리오 전망", fontsize=14, fontweight="bold")
    ax.legend(fontsize=10, loc="upper right")
    ax.grid(axis="y", linestyle="--", alpha=0.35)

    # 실적/전망 구간 레이블
    ax.text(6.5, 60, "← 실적 (월간)", fontsize=9, color="#555555", ha="center")
    ax.text(FORECAST_START + 3, 60, "시나리오 전망 (연간) →",
            fontsize=9, color="#555555", ha="left")

    out = FIGURES / "figure2_utilization.png"
    fig.savefig(out, dpi=300, bbox_inches="tight")
    plt.close()
    print(f"저장 완료: {out}")



def plot_figure2b() -> None:
    """월간 실적 이용률 단독 막대그래프 (EPSIS/KPX, 2025.01–2026.02)."""
    ACTUAL = [
        (2025,  1,  0.000),
        (2025,  2,  9.666),
        (2025,  3, 14.216),
        (2025,  4, 10.211),
        (2025,  5, 12.542),
        (2025,  6, 34.862),
        (2025,  7, 45.242),
        (2025,  8, 40.604),
        (2025,  9, 21.576),
        (2025, 10, 18.173),
        (2025, 11, 23.989),
        (2025, 12,  6.250),
        (2026,  1, 14.588),
        (2026,  2, 20.702),
    ]
    labels = [f"{yr}.{mo}월" for yr, mo, _ in ACTUAL]
    values = [util for _, _, util in ACTUAL]
    x = list(range(len(ACTUAL)))

    fig, ax = plt.subplots(figsize=(11, 4.5))

    bars = ax.bar(x, values, color="#4A90D9", edgecolor="white", linewidth=0.5)

    # 막대 위 수치 표시 (0%는 막대 위가 아닌 살짝 위에 표시)
    for bar, val in zip(bars, values):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.5,
                f"{val:.1f}%", ha="center", va="bottom", fontsize=8)

    # 2025년 연간 평균 이용률
    vals_2025 = [util for yr, _, util in ACTUAL if yr == 2025]
    avg_2025  = sum(vals_2025) / len(vals_2025)
    idx_2025  = [i for i, (yr, _, _) in enumerate(ACTUAL) if yr == 2025]
    ax.hlines(avg_2025, idx_2025[0] - 0.4, idx_2025[-1] + 0.4,
              colors="#E53935", linewidth=1.8, linestyle="--", zorder=5)
    ax.text(idx_2025[-1] + 0.5, avg_2025,
            f"2025년 평균\n{avg_2025:.1f}%",
            color="#E53935", fontsize=8.5, va="center")

    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontsize=9, rotation=45, ha="right")
    ax.set_ylim(0, 55)
    ax.yaxis.set_major_locator(plt.MultipleLocator(10))
    ax.set_ylabel("이용률 (%)", fontsize=12)
    ax.set_title("삼척블루파워 월간 이용률 실적 (EPSIS/KPX)",
                 fontsize=13, fontweight="bold")
    ax.grid(axis="y", linestyle="--", alpha=0.4)

    plt.tight_layout()
    out = FIGURES / "figure2b_actual_utilization.png"
    fig.savefig(out, dpi=300, bbox_inches="tight")
    plt.close()
    print(f"저장 완료: {out}")


if __name__ == "__main__":
    _setup_font()
    plot_figure1()
    plot_figure2()
    plot_figure2b()
    print("완료.")
