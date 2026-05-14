"""
Table: Physical Risk Summary — 4 scenarios x 3 reference years
McKinsey-style: white rows, horizontal rules only, right-aligned numbers.
Output: results/figures/table_physical_risk_summary.png
Source: results/physical/physical_risk_summary.csv
"""
from pathlib import Path

import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import pandas as pd

BASE   = Path(__file__).parent.parent
INPUT  = BASE / "results" / "physical" / "physical_risk_summary.csv"
OUTPUT = BASE / "results" / "figures" / "table_physical_risk_summary.png"
OUTPUT.parent.mkdir(parents=True, exist_ok=True)

plt.rcParams.update({"font.family": "DejaVu Sans", "axes.unicode_minus": False})

# ─── Data ─────────────────────────────────────────────────────────────────────
df = pd.read_csv(INPUT)

SCENARIO_LABELS = {
    "baseline":          "Baseline",
    "moderate_physical": "Moderate\nPhysical",
    "high_physical":     "High\nPhysical",
    "severe_drought":    "Severe\nDrought",
}
SCENARIOS = ["baseline", "moderate_physical", "high_physical", "severe_drought"]
REF_YEARS = [2030, 2040, 2050]

rows: list = []
for scen in SCENARIOS:
    for yr in REF_YEARS:
        sub = df[(df.scenario == scen) & (df.ref_year == yr)]
        if sub.empty:
            continue
        r = sub.iloc[0]
        rows.append({
            "scenario":    scen,
            "label":       SCENARIO_LABELS[scen],
            "ref_year":    int(r.ref_year),
            "outage_rate": float(r.total_outage_rate_pct),
            "derate":      float(r.capacity_derate_pct),
            "npv_loss_b":  float(r.npv_physical_loss_krw) / 1e9,
            "npv_loss_pct": (
                float(r.npv_physical_loss_pct_baseline)
                if pd.notna(r.npv_physical_loss_pct_baseline) else 0.0
            ),
            "credit":      str(r.credit_rating_change),
            "crp_bps":     float(r.crp_bps),
        })

# ─── Canvas ───────────────────────────────────────────────────────────────────
DPI    = 150
N      = len(rows)
HDR_H  = 0.70   # header row height (inches = canvas units)
ROW_H  = 0.52   # data row height
PAD_T  = 1.00   # above table (title area)
PAD_B  = 0.65   # below table (footnote)
FIG_W  = 14.5
FIG_H  = PAD_T + HDR_H + N * ROW_H + PAD_B

TABLE_TOP = FIG_H - PAD_T

# Column layout: (x_start, width)  — must sum to TABLE_W = TABLE_R - TABLE_L
TABLE_L = 0.25
TABLE_R = 14.25
TABLE_W = TABLE_R - TABLE_L

_cols = [
    (TABLE_L,        2.50),   # 0  Scenario
    (TABLE_L + 2.50, 0.90),   # 1  Ref Year
    (TABLE_L + 3.40, 1.65),   # 2  Outage Rate (%)
    (TABLE_L + 5.05, 1.45),   # 3  Derate (%)
    (TABLE_L + 6.50, 2.00),   # 4  NPV Loss (KRW B)
    (TABLE_L + 8.50, 2.05),   # 5  NPV Loss (% Base)
    (TABLE_L + 10.55,1.45),   # 6  Credit Rating
    (TABLE_L + 12.00,2.00),   # 7  CRP (bps)
]
COL_X = [x for x, _ in _cols]
COL_W = [w for _, w in _cols]

# ─── Palette ──────────────────────────────────────────────────────────────────
C_HDR_BG = "#1E2B3A"
C_HDR_FG = "#FFFFFF"
C_BG_ODD = "#FFFFFF"
C_BG_EVN = "#F5F7FA"
C_LINE_LT = "#E0E0E0"
C_LINE_HD = "#1E2B3A"
C_LINE_GR = "#9AA5B1"
C_TEXT    = "#1A1A1A"
C_ZERO    = "#C8C8C8"

FS_TITLE = 15
FS_SUB   =  9
FS_HDR   = 10
FS_SCEN  = 10
FS_VAL   =  9.5
FS_NOTE  =  8.0


def rx(i: int) -> float:
    return COL_X[i] + COL_W[i] - 0.07


def lx(i: int) -> float:
    return COL_X[i] + 0.07


def hline(ax, y: float, lw: float, color: str) -> None:
    ax.plot([TABLE_L, TABLE_R], [y, y],
            color=color, linewidth=lw, solid_capstyle="butt", zorder=5)


def fmt_pct(v: float) -> str:
    return f"{v:.4f}%"


def fmt4(v: float) -> str:
    return f"{v:.4f}"


def fmt_b(v: float) -> str:
    """NPV in billions KRW, 4 decimal places."""
    return f"{v:.4f}"


# ─── Figure ───────────────────────────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(FIG_W, FIG_H), dpi=DPI)
ax.set_xlim(0, FIG_W)
ax.set_ylim(0, FIG_H)
ax.axis("off")
fig.patch.set_facecolor("white")
fig.subplots_adjust(left=0, right=1, top=1, bottom=0)

# ─── Title ────────────────────────────────────────────────────────────────────
ax.text(FIG_W / 2, TABLE_TOP + 0.65,
        "Physical Risk Summary — Climate Risk Premium Model",
        ha="center", va="center",
        fontsize=FS_TITLE, fontweight="bold", color=C_TEXT)
ax.text(FIG_W / 2, TABLE_TOP + 0.30,
        "4 Physical Scenarios  ×  Reference Years 2030 / 2040 / 2050  |  "
        "Source: results/physical/physical_risk_summary.csv",
        ha="center", va="center",
        fontsize=FS_SUB, color="#888888", style="italic")

# ─── Header ───────────────────────────────────────────────────────────────────
hdr_bot = TABLE_TOP - HDR_H

ax.add_patch(mpatches.FancyBboxPatch(
    (TABLE_L, hdr_bot), TABLE_W, HDR_H,
    boxstyle="square,pad=0", facecolor=C_HDR_BG, edgecolor="none", zorder=2))

HDR_DEFS = [
    # (col_idx, label,                  right_align)
    (0, "Scenario",             False),
    (1, "Ref\nYear",            False),
    (2, "Outage\nRate (%)",     True),
    (3, "Derate\n(%)",          True),
    (4, "NPV Loss\n(KRW B)",    True),
    (5, "NPV Loss\n(% Baseline)",True),
    (6, "Credit\nRating",       False),
    (7, "CRP\n(bps)",           True),
]

for col_i, lbl, right in HDR_DEFS:
    x = rx(col_i) if right else lx(col_i)
    ax.text(x, hdr_bot + HDR_H / 2, lbl,
            ha="right" if right else "left", va="center",
            fontsize=FS_HDR, fontweight="bold",
            color=C_HDR_FG, zorder=3, linespacing=1.3)

hline(ax, TABLE_TOP, 2.0, C_LINE_HD)
hline(ax, hdr_bot,   0.8, C_LINE_HD)

# ─── Data rows ────────────────────────────────────────────────────────────────
scen_order: list = []
for r in rows:
    if r["scenario"] not in scen_order:
        scen_order.append(r["scenario"])

for i, row in enumerate(rows):
    y_bot = TABLE_TOP - HDR_H - (i + 1) * ROW_H
    y_mid = y_bot + ROW_H / 2
    y_top = y_bot + ROW_H

    si = scen_order.index(row["scenario"])
    bg = C_BG_EVN if si % 2 == 1 else C_BG_ODD

    ax.add_patch(mpatches.FancyBboxPatch(
        (TABLE_L, y_bot), TABLE_W, ROW_H,
        boxstyle="square,pad=0", facecolor=bg, edgecolor="none", zorder=1))

    hline(ax, y_top, 0.4, C_LINE_LT)

    # Scenario label — only on first row of each group, vertically centered
    first_in_group = (i == 0 or rows[i - 1]["scenario"] != row["scenario"])
    if first_in_group:
        group_n = sum(1 for r in rows if r["scenario"] == row["scenario"])
        group_center_y = y_mid - (group_n - 1) * ROW_H / 2
        ax.text(lx(0), group_center_y, row["label"],
                ha="left", va="center",
                fontsize=FS_SCEN, fontweight="bold",
                color=C_TEXT, zorder=4, linespacing=1.35)

    # Year
    ax.text(lx(1), y_mid, str(row["ref_year"]),
            ha="left", va="center", fontsize=FS_VAL, color=C_TEXT, zorder=4)

    # Outage Rate (%)
    v = row["outage_rate"]
    ax.text(rx(2), y_mid, fmt_pct(v), ha="right", va="center",
            fontsize=FS_VAL, color=C_ZERO if v == 0 else C_TEXT, zorder=4)

    # Derate (%)
    v = row["derate"]
    ax.text(rx(3), y_mid, fmt_pct(v), ha="right", va="center",
            fontsize=FS_VAL, color=C_ZERO if v == 0 else C_TEXT, zorder=4)

    # NPV Loss (KRW B)
    v = row["npv_loss_b"]
    ax.text(rx(4), y_mid, fmt_b(v), ha="right", va="center",
            fontsize=FS_VAL, color=C_ZERO if v == 0 else C_TEXT, zorder=4)

    # NPV Loss (% Baseline)
    v = row["npv_loss_pct"]
    ax.text(rx(5), y_mid, fmt_pct(v), ha="right", va="center",
            fontsize=FS_VAL, color=C_ZERO if v == 0 else C_TEXT, zorder=4)

    # Credit Rating (left-aligned)
    ax.text(lx(6), y_mid, row["credit"],
            ha="left", va="center", fontsize=FS_VAL, color=C_TEXT, zorder=4)

    # CRP (bps)
    v = row["crp_bps"]
    ax.text(rx(7), y_mid, fmt4(v), ha="right", va="center",
            fontsize=FS_VAL, color=C_ZERO if v == 0 else C_TEXT, zorder=4)

    # Thick separator between scenario groups
    if i < N - 1 and rows[i + 1]["scenario"] != row["scenario"]:
        hline(ax, y_bot, 1.2, C_LINE_GR)

# ─── Bottom border ────────────────────────────────────────────────────────────
table_bot = TABLE_TOP - HDR_H - N * ROW_H
hline(ax, table_bot, 2.0, C_LINE_HD)

# ─── Footnote ─────────────────────────────────────────────────────────────────
ax.text(TABLE_L, table_bot - 0.12,
        "Note: NPV Loss discounted from ref_year onward using plant discount rate.  "
        "NPV Loss (% Baseline) = loss ÷ |baseline NPV|.  "
        "CRP = Climate Risk Premium in basis points.  "
        "All numeric values rounded to 4 decimal places.",
        ha="left", va="top", fontsize=FS_NOTE,
        color="#888888", style="italic", linespacing=1.4)

# ─── Save ─────────────────────────────────────────────────────────────────────
plt.savefig(OUTPUT, dpi=DPI, bbox_inches="tight", facecolor="white")
plt.close()
print(f"Saved → {OUTPUT}")
