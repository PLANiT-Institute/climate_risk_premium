"""
CRP Model Flow — top-to-bottom layout  v2
Output: results/figures/crp_model_flow_en_v2.png
"""
from pathlib import Path
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Rectangle

# ── Canvas ───────────────────────────────────────────────────────────────────
# S=3 scales all geometry 3x vs. the original draft; DPI=300 gives print quality.
S     = 3
DPI   = 300
SVG_W = 680 * S   # 2040
SVG_H = 700 * S   # 2100

fig, ax = plt.subplots(figsize=(SVG_W / DPI, SVG_H / DPI), dpi=DPI)
ax.set_xlim(0, SVG_W)
ax.set_ylim(SVG_H, 0)   # y=0 at top
ax.set_aspect("auto")
ax.axis("off")
fig.patch.set_facecolor("white")
plt.subplots_adjust(left=0, right=1, top=1, bottom=0)

# ── Palette ──────────────────────────────────────────────────────────────────
BLUE  = "#2A72BA"
BG    = "#EBF4FD"
DARK  = "#1A3A5C"
WHITE = "#FFFFFF"

FS_TITLE = 22
FS_HDR   = 17
FS_BUL   = 12
DY       = 14 * S   # 42  — line spacing
HDR_H    = 30 * S   # 90  — header strip height
PAD      = 10 * S   # 30  — top/bottom padding inside box

# Full-width box geometry
BW  = 540 * S   # 1620
BX  = 70  * S   # 210
BCX = BX + BW / 2   # 1020  (centre of full-width boxes)

# Row-2 split box geometry
BW2   = 255 * S              # 765
B2A_X = BX                   # 210  (Physical Risk)
B2B_X = BX + BW2 + 30 * S   # 1065 (Transition Risk)
B2A_CX = B2A_X + BW2 / 2    # 592.5
B2B_CX = B2B_X + BW2 / 2    # 1447.5

# ── Drawing helpers ──────────────────────────────────────────────────────────
def rrect(x, y, w, h, fc=BG, ec=BLUE, lw=4.5, z=2):
    r = 3 * S
    ax.add_patch(FancyBboxPatch(
        (x + r, y + r), w - 2*r, h - 2*r,
        boxstyle=f"round,pad={r}",
        facecolor=fc, edgecolor=ec, linewidth=lw, zorder=z,
    ))

def fillrect(x, y, w, h, fc, z=3):
    ax.add_patch(Rectangle((x, y), w, h, facecolor=fc, edgecolor="none", zorder=z))

def t(x, y, s, ha="left", va="top", fs=FS_BUL, fw="normal", color=DARK, z=5):
    ax.text(x, y, s, ha=ha, va=va, fontsize=fs, fontweight=fw,
            color=color, fontfamily="DejaVu Sans", zorder=z, clip_on=False)

def hln(x1, x2, y, z=4):
    ax.plot([x1, x2], [y, y], color=BLUE, lw=4.5, solid_capstyle="butt", zorder=z)

def vln(x, y1, y2, z=4):
    ax.plot([x, x], [y1, y2], color=BLUE, lw=4.5, solid_capstyle="butt", zorder=z)

def arrowv(x, y1, y2, z=4):
    """Downward vertical arrow."""
    ax.annotate("", xy=(x, y2), xytext=(x, y1),
                arrowprops=dict(arrowstyle="-|>", color=BLUE,
                                lw=4.0, mutation_scale=18),
                zorder=z)

def box(x, y, w, h, title, cx, bx, bullets):
    rrect(x, y, w, h)
    fillrect(x, y, w, HDR_H, BLUE)
    t(cx, y + HDR_H / 2, title, ha="center", va="center",
      fs=FS_HDR, fw="bold", color=WHITE)
    y0 = y + HDR_H + PAD
    for i, line in enumerate(bullets):
        t(bx, y0 + i * DY, line)

# ── Title ────────────────────────────────────────────────────────────────────
t(BCX, 16 * S, "PLANiT Credit Risk Premium (CRP) Model",
  ha="center", va="center", fs=FS_TITLE, fw="bold", color=DARK)

# ── Box 1 — Plant Inputs (4 lines) ───────────────────────────────────────────
B1_Y = 30 * S                              # 90
B1_H = HDR_H + PAD + 4*DY + PAD           # 318
box(BX, B1_Y, BW, B1_H, "Plant Inputs", BCX, BX + 8*S, [
    "· Installed Capacity  ·  Operating Years",
    "· Capital Investment  ·  Capital Structure",
    "· Baseline Capacity Factor",
    "· Fuel Cost  ·  Power Price",
])

# ── Fork: Box 1 bottom → Box 2a / 2b tops ────────────────────────────────────
B1_BOT = B1_Y + B1_H                      # 408
FORK_Y = B1_BOT + 14 * S                  # 450
B2_Y   = FORK_Y + 12 * S                  # 486

vln(BCX, B1_BOT, FORK_Y)
hln(B2A_CX, B2B_CX, FORK_Y)
arrowv(B2A_CX, FORK_Y, B2_Y)
arrowv(B2B_CX, FORK_Y, B2_Y)

# ── Box 2a — Physical Risk (4 lines) ─────────────────────────────────────────
B2_H = HDR_H + PAD + 4*DY + PAD           # 318
box(B2A_X, B2_Y, BW2, B2_H, "Physical Risk", B2A_CX, B2A_X + 8*S, [
    "· Wildfire: dom. lit. applied",
    "· Cooling water · flood,",
    "  coastal erosion,",
    "  drought (PhysRisk)",
])

# ── Box 2b — Transition Risk (3 lines) ───────────────────────────────────────
box(B2B_X, B2_Y, BW2, B2_H, "Transition Risk", B2B_CX, B2B_X + 8*S, [
    "· Policy-intensity-based",
    "  capacity factor",
    "· Operating life scenarios",
])

# ── Merge: Box 2a / 2b bottoms → Box 3 top ───────────────────────────────────
B2_BOT  = B2_Y + B2_H                     # 804
MERGE_Y = B2_BOT + 14 * S                 # 846
B3_Y    = MERGE_Y + 12 * S                # 882

vln(B2A_CX, B2_BOT, MERGE_Y)
vln(B2B_CX, B2_BOT, MERGE_Y)
hln(B2A_CX, B2B_CX, MERGE_Y)
arrowv(BCX, MERGE_Y, B3_Y)

# ── Box 3 — Cash Flow Analysis (4 lines) ─────────────────────────────────────
B3_H = HDR_H + PAD + 4*DY + PAD           # 318
box(BX, B3_Y, BW, B3_H, "Cash Flow Analysis", BCX, BX + 8*S, [
    "· Generation  ·  Revenue",
    "· Fuel Cost  ·  Operating Cost",
    "· FCF  ·  EBITDA",
    "· NPV  ·  IRR  ·  DSCR",
])

# ── Arrow: Box 3 → Box 4 ─────────────────────────────────────────────────────
B3_BOT = B3_Y + B3_H                      # 1200
B4_Y   = B3_BOT + 26 * S                  # 1278
arrowv(BCX, B3_BOT, B4_Y)

# ── Box 4 — Credit Rating (7 lines) ──────────────────────────────────────────
B4_H = HDR_H + PAD + 7*DY + PAD           # 444
box(BX, B4_Y, BW, B4_H, "Credit Rating", BCX, BX + 8*S, [
    "· KIS methodology + PLANiT adjustments",
    "· Industry / Policy outlook (AA)  —  qualitative: 50%",
    "· Profitability (EBITDA / Assets): 10%",
    "· Interest coverage (EBITDA / Interest): 12%",
    "· Net Debt leverage: 12%  ·  Asset leverage: 8%  ·  Equity leverage: 8%",
    "",
    "· DSCR-based downgrade / default override",
])

# ── Arrow: Box 4 → Box 5 ─────────────────────────────────────────────────────
B4_BOT = B4_Y + B4_H                      # 1722
B5_Y   = B4_BOT + 26 * S                  # 1800
arrowv(BCX, B4_BOT, B5_Y)

# ── Box 5 — Credit Premium (2 lines) ─────────────────────────────────────────
B5_H = HDR_H + PAD + 2*DY + PAD           # 234
box(BX, B5_Y, BW, B5_H, "Credit Premium", BCX, BX + 8*S, [
    "· CRP (bps) calculation",
    "· WACC premium calculation",
])

# ── Save ──────────────────────────────────────────────────────────────────────
out = Path(__file__).parent.parent / "results" / "figures" / "crp_model_flow_en_v2.png"
out.parent.mkdir(parents=True, exist_ok=True)
fig.savefig(out, dpi=DPI, facecolor="white", bbox_inches="tight")
plt.close()
print(f"Saved: {out}")
