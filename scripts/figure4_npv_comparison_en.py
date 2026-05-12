from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker

plt.rcParams['font.family'] = 'DejaVu Sans'
plt.rcParams['axes.unicode_minus'] = False

# Bottom to top: most negative (worst) at bottom, least negative (best) at top
data = [
    ("Enhanced Combined",   -2791.3),
    ("Combined Aggressive",  -2505.2),
    ("Combined Moderate",    -1753.2),
]

labels = [d[0] for d in data]
values = [d[1] for d in data]
bar_color = "#2E75B6"

fig, ax = plt.subplots(figsize=(12, 7))

ax.barh(range(len(labels)), values, color=bar_color, height=0.45,
        edgecolor='white', linewidth=0.5)

# Vertical reference line (baseline scenario)
baseline_npv = -1268.2
ax.axvline(x=baseline_npv, color='#595959', linestyle='--', linewidth=1.3, zorder=5)
ax.text(baseline_npv - 35, 2.58, 'Baseline Scenario',
        ha='right', va='bottom', fontsize=9, color='#595959', style='italic')

# NPV labels inside bars, near the outer (left) tip
for i, val in enumerate(values):
    ax.text(val + 45, i, f'-{abs(val):,.0f}M',
            ha='left', va='center', fontsize=10, color='white', fontweight='bold')

# Y-axis: scenario names
ax.set_yticks(range(len(labels)))
ax.set_yticklabels(labels, fontsize=12)

# X-axis
ax.set_xlim(-3200, 0)
ax.set_xlabel('Net Present Value (USD million)', fontsize=11, labelpad=8)
ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f'{int(x):,}'))
ax.tick_params(axis='x', labelsize=9.5)

# Title
ax.set_title('NPV Comparison by Scenario',
             fontsize=14, fontweight='bold', pad=14)

# Grid and spines
ax.xaxis.grid(True, linestyle=':', alpha=0.4, color='lightgray')
ax.set_axisbelow(True)
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)

# Footnote
fig.text(0.01, 0.012, 'Source: PLANiT CRP Model — results/scenario_comparison.csv',
         ha='left', va='bottom', fontsize=8, color='gray', style='italic')

plt.tight_layout(rect=[0, 0.03, 1, 1])

output_path = Path(__file__).parent.parent / 'results' / 'figures' / 'figure4_npv_comparison_en.png'
plt.savefig(output_path, dpi=300, bbox_inches='tight', facecolor='white')
plt.close()
print(f"Saved: {output_path}")
