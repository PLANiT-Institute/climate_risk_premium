"""
Figure 5 (v5): Physical Climate Risk — Power Plant Impact Pathway
Output spec: 1200×700 px, 150 dpi, PNG, white background
"""
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

plt.rcParams["font.family"] = "Malgun Gothic"
plt.rcParams["axes.unicode_minus"] = False

# ─── Canvas: 1200×700 px @ 150 dpi ───
DPI = 150
FIG_W_PX, FIG_H_PX = 1200, 700
fig, ax = plt.subplots(figsize=(FIG_W_PX / DPI, FIG_H_PX / DPI))  # (8.0, 4.667 in)
ax.set_xlim(0, 14)
ax.set_ylim(0, 9)
ax.axis("off")
fig.patch.set_facecolor("white")
fig.subplots_adjust(left=0.01, right=0.99, top=0.97, bottom=0.01)

# ─── Colors ───
BOX_BG = "#F2F2F2"
BOX_EC = "#666666"
C_ARR  = "#888888"

C_H_HDR = "#C00000"
C_P_HDR = "#2E75B6"
C_F_HDR = "#595959"

# ─── Geometry (same coordinate system as before) ───
W_H, W_P, W_F = 1.90, 2.70, 2.20
X_H = 2.30
X_P = X_H + W_H + 1.30   # 5.50
X_F = X_P + W_P + 1.30   # 10.10

X_HC = X_H + W_H / 2     # 3.25
X_PC = X_P + W_P / 2     # 6.85
X_FC = X_F + W_F / 2     # 11.20

X_HR = X_H + W_H         # 4.20
X_PR = X_P + W_P         # 8.20

ITEM_H = 1.85
GAP    = 0.50

Y  = [0.55 + i * (ITEM_H + GAP) for i in range(3)]
YM = [y + ITEM_H / 2 for y in Y]

HI = 0.78
LO = 0.36

F_CAP_BOT = Y[2]
F_CAP_MID = YM[2]
F_REV_MID = (YM[0] + YM[1]) / 2
F_REV_BOT = F_REV_MID - ITEM_H / 2


def rbox(x, y, w, h, lw=1.2):
    ax.add_patch(FancyBboxPatch(
        (x, y), w, h, boxstyle="round,pad=0.08",
        facecolor=BOX_BG, edgecolor=BOX_EC, linewidth=lw, zorder=2,
    ))


def arr(x1, y1, x2, y2, rad=0.0):
    ax.annotate(
        "", xy=(x2, y2), xytext=(x1, y1),
        arrowprops=dict(
            arrowstyle="-|>", color=C_ARR, lw=1.3,
            mutation_scale=11,
            connectionstyle=f"arc3,rad={rad}",
        ),
        zorder=1,
    )


# ═══ TITLE ═══
ax.text(7, 8.55, "물리적 리스크의 발전소 영향 경로",
        ha="center", va="center", fontsize=12, fontweight="bold",
        color="#1A1A1A", zorder=3)

# ═══ COLUMN HEADERS ═══
HDR_Y = 7.80
for cx, txt, c in [
    (X_HC, "위험 요인(Hazard)",    C_H_HDR),
    (X_PC, "피해 경로(Pathway)",   C_P_HDR),
    (X_FC, "재무 영향(Impact)",    C_F_HDR),
]:
    ax.text(cx, HDR_Y, txt, ha="center", va="center",
            fontsize=9, fontweight="bold", color=c, zorder=3)

for xl, xr, c in [
    (X_H,      X_HR,      C_H_HDR),
    (X_P,      X_PR,      C_P_HDR),
    (X_F, X_F + W_F,      C_F_HDR),
]:
    ax.plot([xl, xr], [HDR_Y - 0.28] * 2, color=c, lw=1.0, alpha=0.55, zorder=1)

# ═══ HAZARD BOXES (3) ═══
for row, txt in [
    (2, "산불 · 태풍\n홍수 · 폭풍해일"),
    (1, "가뭄\n냉각수 부족"),
    (0, "기온 상승\n수온 상승"),
]:
    rbox(X_H, Y[row], W_H, ITEM_H)
    ax.text(X_HC, YM[row], txt,
            ha="center", va="center", fontsize=10, fontweight="bold",
            color="#333333", multialignment="center", linespacing=1.4, zorder=3)

# ═══ PATHWAY BOXES (3) ═══
for row, txt in [
    (2, "설비 복구 · 교체"),
    (1, "운영 중단 · 발전 불가"),
    (0, "효율 저하 · 발전량 감소"),
]:
    rbox(X_P, Y[row], W_P, ITEM_H)
    ax.text(X_PC, YM[row], txt,
            ha="center", va="center", fontsize=10, fontweight="bold",
            color="#333333", multialignment="center", zorder=3)

# ═══ FINANCIAL BOXES (2) ═══
for y_bot, txt in [
    (F_CAP_BOT, "자본지출 증가"),
    (F_REV_BOT, "영업이익 감소"),
]:
    rbox(X_F, y_bot, W_F, ITEM_H)
    ax.text(X_FC, y_bot + ITEM_H / 2, txt,
            ha="center", va="center", fontsize=10, fontweight="bold",
            color="#333333", zorder=3)

# ═══ ARROWS: Hazard → Pathway ═══
arr(X_HR, YM[2],               X_P, YM[2])
arr(X_HR, YM[2],               X_P, Y[1] + ITEM_H * HI)
arr(X_HR, Y[1] + ITEM_H * HI,  X_P, Y[1] + ITEM_H * LO)
arr(X_HR, Y[0] + ITEM_H * HI,  X_P, YM[1])    # 기온·수온 → 운영중단 (대각 상향)
arr(X_HR, Y[0] + ITEM_H * LO,  X_P, YM[0])    # 기온·수온 → 효율저하

# ═══ ARROWS: Pathway → Financial ═══
arr(X_PR, YM[2],               X_F, F_CAP_MID)
arr(X_PR, Y[1] + ITEM_H * HI,  X_F, F_REV_BOT + ITEM_H * HI)
arr(X_PR, YM[0],               X_F, F_REV_BOT + ITEM_H * LO)

# ═══ SAVE ═══
out = Path(r"c:\dev\climate_risk_premium\results\figures\figure5_physical_risk_pathway.png")
out.parent.mkdir(parents=True, exist_ok=True)
plt.savefig(out, dpi=DPI, facecolor="white")   # bbox_inches 생략 → 정확히 1200×700 px
plt.close()
print(f"Saved → {out}  (target {FIG_W_PX}×{FIG_H_PX} px @ {DPI} dpi)")
