"""
Render crp_model_flow_en.svg as a PNG using matplotlib.

Coordinate system mirrors the SVG: x ∈ [0, 1100], y ∈ [0, 290] with y=0 at top.
Output: results/figures/crp_model_flow_en.png  (2200×580 px @ 200 dpi)

Font-size budget (fontsize=4.5 pt @ 200 dpi → ~7.5 px/char):
  Available width per box = 190 - 18 (left pad) - 2 (right pad) = 170 px → ~22 chars/line.
  Long strings are split across two lines accordingly.
"""
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Rectangle

# ─── Canvas ──────────────────────────────────────────────────────────────────
DPI   = 200
SVG_W = 1100
SVG_H = 290

fig, ax = plt.subplots(figsize=(SVG_W / DPI, SVG_H / DPI), dpi=DPI)
ax.set_xlim(0, SVG_W)
ax.set_ylim(SVG_H, 0)   # y=0 at top, y=290 at bottom — mirrors SVG
ax.set_aspect("auto")
ax.axis("off")
fig.patch.set_facecolor("white")
plt.subplots_adjust(left=0, right=1, top=1, bottom=0)

# ─── Palette ─────────────────────────────────────────────────────────────────
BLUE  = "#2A72BA"
BG    = "#EBF4FD"
DARK  = "#1A3A5C"
WHITE = "#FFFFFF"

FS_TITLE  = 8.5   # pt — figure title
FS_HDR    = 6.5   # pt — box header labels
FS_BUL    = 4.5   # pt — bullet text  (~7.5 px/char → 22 chars fits in 170 px)
DY        = 14    # vertical spacing between bullet lines (SVG units)

# ─── Drawing helpers ─────────────────────────────────────────────────────────
def rrect(x, y, w, h, fc=BG, ec=BLUE, lw=1.5, z=2):
    """Rounded rectangle; (x,y) is top-left in SVG coordinates."""
    r = 3
    ax.add_patch(FancyBboxPatch(
        (x + r, y + r), w - 2 * r, h - 2 * r,
        boxstyle=f"round,pad={r}",
        facecolor=fc, edgecolor=ec, linewidth=lw, zorder=z,
    ))

def fillrect(x, y, w, h, fc, z=3):
    ax.add_patch(Rectangle((x, y), w, h, facecolor=fc, edgecolor="none", zorder=z))

def t(x, y, s, ha="left", va="top", fs=FS_BUL, fw="normal", color=DARK, z=5):
    ax.text(x, y, s, ha=ha, va=va, fontsize=fs, fontweight=fw,
            color=color, fontfamily="DejaVu Sans", zorder=z, clip_on=False)

def hln(x1, x2, y, z=4):
    ax.plot([x1, x2], [y, y], color=BLUE, lw=1.5, solid_capstyle="butt", zorder=z)

def vln(x, y1, y2, z=4):
    ax.plot([x, x], [y1, y2], color=BLUE, lw=1.5, solid_capstyle="butt", zorder=z)

def arrowh(x1, x2, y, z=4):
    ax.annotate("", xy=(x2, y), xytext=(x1, y),
                arrowprops=dict(arrowstyle="-|>", color=BLUE,
                                lw=1.3, mutation_scale=6),
                zorder=z)

def col_box(x, y, w, h, title, cx, bullets, bx, y0):
    """Full column box with blue header and bullet lines."""
    rrect(x, y, w, h)
    fillrect(x, y, w, 30, BLUE)
    t(cx, y + 15, title, ha="center", va="center",
      fs=FS_HDR, fw="bold", color=WHITE)
    for i, line in enumerate(bullets):
        t(bx, y0 + i * DY, line)

# ─── Title ───────────────────────────────────────────────────────────────────
t(550, 18, "PLANiT Credit Risk Premium (CRP) Model",
  ha="center", va="center", fs=FS_TITLE, fw="bold", color=DARK)

# ─── COL 1 — Plant Inputs ────────────────────────────────────────────────────
# 6 lines × DY=14 = 84 px in content area 177 px → y0 = 68+(177-84)/2+FS_BUL*0.75 ≈ 118
col_box(
    x=10, y=38, w=190, h=207, title="Plant Inputs", cx=105, bx=18, y0=118,
    bullets=[
        "· Installed Capacity",
        "· Operating Years",
        "· Capital Investment",
        "  · Capital Structure",
        "· Baseline Cap. Factor",
        "· Fuel Cost · Power Price",
    ],
)

# ─── FORK: Col1 → Col2 ───────────────────────────────────────────────────────
hln(200, 209, 142)
vln(209, 86, 197)
arrowh(209, 218, 86)
arrowh(209, 218, 197)

# ─── COL 2 TOP — Physical Risk ───────────────────────────────────────────────
# 4 lines × 14 = 56 px in content area 66 px → y0 = 68+(66-56)/2+FS_BUL*0.75 ≈ 76
rrect(x=218, y=38, w=190, h=96)
fillrect(218, 38, 190, 30, BLUE)
t(313, 53, "Physical Risk", ha="center", va="center",
  fs=FS_HDR, fw="bold", color=WHITE)
for i, line in enumerate([
    "· Wildfire: dom. lit. applied",
    "· Cooling water · flood,",
    "  coastal erosion,",
    "  drought (PhysRisk)",
]):
    t(226, 76 + i * DY, line)

# ─── COL 2 BOTTOM — Transition Risk ──────────────────────────────────────────
# 3 lines × 14 = 42 px in content area 66 px → y0 = 179+(66-42)/2+FS_BUL*0.75 ≈ 194
rrect(x=218, y=149, w=190, h=96)
fillrect(218, 149, 190, 30, BLUE)
t(313, 164, "Transition Risk", ha="center", va="center",
  fs=FS_HDR, fw="bold", color=WHITE)
for i, line in enumerate([
    "· Policy-intensity-based",
    "  capacity factor",
    "· operating life scenarios",
]):
    t(226, 194 + i * DY, line)

# ─── MERGE: Col2 → Col3 ──────────────────────────────────────────────────────
hln(408, 417, 86)
hln(408, 417, 197)
vln(417, 86, 197)
arrowh(417, 426, 142)

# ─── COL 3 — Cash Flow Analysis ──────────────────────────────────────────────
# 4 lines × 14 = 56 px in content area 177 px → y0 = 68+(177-56)/2+FS_BUL*0.75 ≈ 132
col_box(
    x=426, y=38, w=190, h=207, title="Cash Flow Analysis", cx=521, bx=434, y0=132,
    bullets=[
        "· Generation · Revenue",
        "· Fuel Cost · Op. Cost",
        "· FCF · EBITDA",
        "· NPV · IRR · DSCR",
    ],
)

# ─── Arrow: Col3 → Col4 ──────────────────────────────────────────────────────
arrowh(616, 634, 142)

# ─── COL 4 — Credit Rating ───────────────────────────────────────────────────
# 8 lines × 14 = 112 px in content area 177 px → y0 = 68+(177-112)/2+FS_BUL*0.75 ≈ 104
col_box(
    x=634, y=38, w=190, h=207, title="Credit Rating", cx=729, bx=642, y0=104,
    bullets=[
        "· KIS methodology",
        "  + PLANiT adjustments",
        "· Industry outlook (AA)",
        "  qualitative: 50%",
        "· Profitability &",
        "  fin. stability: 50%",
        "· DSCR-based financing",
        "  risk adjustment",
    ],
)

# ─── Arrow: Col4 → Col5 ──────────────────────────────────────────────────────
arrowh(824, 842, 142)

# ─── COL 5 — Credit Premium ──────────────────────────────────────────────────
# 2 lines × 14 = 28 px in content area 177 px → y0 = 68+(177-28)/2+FS_BUL*0.75 ≈ 146
col_box(
    x=842, y=38, w=190, h=207, title="Credit Premium", cx=937, bx=850, y0=146,
    bullets=[
        "· CRP (bps) calculation",
        "· WACC premium calculation",
    ],
)

# ─── Save ────────────────────────────────────────────────────────────────────
out = Path(__file__).parent.parent / "results" / "figures" / "crp_model_flow_en.png"
out.parent.mkdir(parents=True, exist_ok=True)
fig.savefig(out, dpi=DPI, facecolor="white", bbox_inches="tight")
plt.close()
print(f"Saved: {out}  ({SVG_W * DPI // 100}×{SVG_H * DPI // 100} px @ {DPI} dpi)")
