"""
Table: Wildfire Annual Revenue Loss Rate — Physical Risk (RCP 8.5)
McKinsey-style: white rows, horizontal rules only, right-aligned numbers.
Output: results/figures/table_physical_risk_loss_rates_en.png
Source: data/physical_risk_steps/output/physical_risk_output.csv
"""
from pathlib import Path

import matplotlib.patches as mpatches
import matplotlib.pyplot as plt

BASE   = Path(__file__).parent.parent
OUTPUT = BASE / "results" / "figures" / "table_physical_risk_loss_rates_en.png"
OUTPUT.parent.mkdir(parents=True, exist_ok=True)

plt.rcParams.update({"font.family": "DejaVu Sans", "axes.unicode_minus": False})

# ─── Scale factor (4× pixels = high-res print quality) ───────────────────────
S = 4

# ─── Data ─────────────────────────────────────────────────────────────────────
# From data/physical_risk_steps/output/physical_risk_output.csv (RCP8.5)
# (hazard, sub_component, 2024, 2030, 2050, 2100)
ROWS = [
    ("Wildfire", "—", 0.000082, 0.000164, 0.000164, 0.000329),
]

HDR_LABELS = ["Hazard", "Sub-Component", "2024", "2030", "2050", "2100"]

# ─── Layout ───────────────────────────────────────────────────────────────────
DPI       = 150
FIG_W     = 12 * S    # 48
FIG_H     = 3.6 * S   # 14.4

TABLE_TOP = 2.90 * S
HDR_H     = 0.52 * S
ROW_H     = 0.66 * S

# Columns: [Hazard, Sub-Component, 2024, 2030, 2050, 2100]
_cx = [0.15, 2.65, 5.65, 7.20, 8.75, 10.30]
_cw = [2.50, 3.00, 1.55, 1.55, 1.55,  1.55]
COL_X = [x * S for x in _cx]
COL_W = [w * S for w in _cw]

TABLE_L = COL_X[0]
TABLE_R = COL_X[-1] + COL_W[-1]
TABLE_W = TABLE_R - TABLE_L

# McKinsey palette
C_HDR_BG  = "#1E2B3A"
C_HDR_FG  = "#FFFFFF"
C_BODY_BG = "#FFFFFF"
C_LINE_LT = "#E0E0E0"
C_LINE_HD = "#1E2B3A"
C_TEXT    = "#1A1A1A"
C_ZERO    = "#C8C8C8"

# Font sizes (base × S)
FS_TITLE = 14 * S
FS_SUB   =  9 * S
FS_HDR   = 11 * S
FS_HAZ   = 11 * S
FS_SUBC  = 10.5 * S
FS_VAL   = 11 * S
FS_NOTE  =  9 * S


def cx(i: int) -> float:
    return COL_X[i] + COL_W[i] / 2


def rx(i: int) -> float:
    return COL_X[i] + COL_W[i] - 0.10 * S


def hline(ax, y, x0, x1, color, lw):
    ax.plot([x0, x1], [y, y], color=color, linewidth=lw * S,
            solid_capstyle="butt", zorder=5)


def fmt(v: float) -> str:
    return "0.0000%" if v == 0.0 else f"{v * 100:.4f}%"


# ─── Canvas ───────────────────────────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(FIG_W, FIG_H))
ax.set_xlim(0, FIG_W)
ax.set_ylim(0, FIG_H)
ax.axis("off")
fig.patch.set_facecolor("white")
fig.subplots_adjust(left=0.01, right=0.99, top=0.95, bottom=0.05)

# ─── Title ────────────────────────────────────────────────────────────────────
ax.text(FIG_W / 2, 3.40 * S,
        "Wildfire Revenue Loss Rate  —  Physical Risk (RCP 8.5)",
        ha="center", va="center", fontsize=FS_TITLE, fontweight="bold", color=C_TEXT)
ax.text(FIG_W / 2, 3.22 * S,
        "Samcheok Blue Power Plant (2.1 GW Coal)  |  "
        "Sources: WWA (2025), CLIMADA API / NASA FIRMS (ETH Zürich)",
        ha="center", va="center", fontsize=FS_SUB, color="#888888", style="italic")

# ─── Header ───────────────────────────────────────────────────────────────────
hdr_bot = TABLE_TOP - HDR_H

ax.add_patch(mpatches.FancyBboxPatch(
    (TABLE_L, hdr_bot), TABLE_W, HDR_H,
    boxstyle="square,pad=0", facecolor=C_HDR_BG, edgecolor="none", zorder=2))

for i, lbl in enumerate(HDR_LABELS):
    is_num = i >= 2
    x_pos  = rx(i) if is_num else (COL_X[i] + 0.12 * S)
    ax.text(x_pos, hdr_bot + HDR_H / 2, lbl,
            ha="right" if is_num else "left",
            va="center", fontsize=FS_HDR, fontweight="bold", color=C_HDR_FG, zorder=3)

hline(ax, TABLE_TOP, TABLE_L, TABLE_R, C_LINE_HD, lw=2.0)
hline(ax, hdr_bot,   TABLE_L, TABLE_R, C_LINE_HD, lw=0.8)

# ─── Data rows ────────────────────────────────────────────────────────────────
for row_i, (hazard, sub, v24, v30, v50, v100) in enumerate(ROWS):
    y_bot  = TABLE_TOP - HDR_H - (row_i + 1) * ROW_H
    y_mid  = y_bot + ROW_H / 2
    y_top  = y_bot + ROW_H
    values = [v24, v30, v50, v100]

    ax.add_patch(mpatches.FancyBboxPatch(
        (TABLE_L, y_bot), TABLE_W, ROW_H,
        boxstyle="square,pad=0", facecolor=C_BODY_BG, edgecolor="none", zorder=1))

    hline(ax, y_top, TABLE_L, TABLE_R, C_LINE_LT, lw=0.5)

    # Hazard
    ax.text(COL_X[0] + 0.12 * S, y_mid, hazard,
            ha="left", va="center", fontsize=FS_HAZ, color=C_TEXT, zorder=4)

    # Sub-Component
    if sub == "—":
        ax.text(cx(1), y_mid, "—",
                ha="center", va="center", fontsize=FS_HAZ, color=C_ZERO, zorder=4)
    else:
        ax.text(COL_X[1] + 0.10 * S, y_mid, sub,
                ha="left", va="center", fontsize=FS_SUBC,
                color="#555555", style="italic", zorder=4)

    # Values
    for ci, val in enumerate(values):
        is_zero = val == 0.0
        ax.text(rx(2 + ci), y_mid, fmt(val),
                ha="right", va="center", fontsize=FS_VAL,
                color=C_ZERO if is_zero else C_TEXT, zorder=4)

# ─── Bottom border ────────────────────────────────────────────────────────────
table_bot = TABLE_TOP - HDR_H - len(ROWS) * ROW_H
hline(ax, table_bot, TABLE_L, TABLE_R, C_LINE_HD, lw=2.0)

# ─── Footnote ─────────────────────────────────────────────────────────────────
ax.text(TABLE_L, table_bot - 0.14 * S,
        "Note: Revenue base = $881.6M/yr (baseline scenario).  "
        "Base outage rate: 6 events / 20 yr (NASA FIRMS) × P(outage|fire)=0.10 × 24 h/8760 h.\n"
        "Climate factors: 2.0× at current warming (2030–2050), 4.0× at +2.6°C above pre-industrial (2100) — WWA (2025).",
        ha="left", va="top", fontsize=FS_NOTE,
        color="#888888", style="italic", linespacing=1.4)

# ─── Save ─────────────────────────────────────────────────────────────────────
plt.savefig(OUTPUT, dpi=DPI, bbox_inches="tight", facecolor="white")
plt.close()
print(f"Saved → {OUTPUT}  ({int(FIG_W * DPI)} × {int(FIG_H * DPI)} px @ {DPI} dpi)")
