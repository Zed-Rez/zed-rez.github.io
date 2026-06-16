#!/usr/bin/env python3
"""
Generate figures for the EUCLID autoformalization paper.

Produces two vector PDFs in the same directory:
  fig_grid.pdf   - 3x3 heatmap: compile rate by translation (rows) x prompt (cols)
  fig_contam.pdf - contamination probe (Qwen) + GPT-4o clean reference

Style: standard academic / Computer Modern-ish serif, greyscale-friendly with a
single accent. No website colors imposed. Numbers are exact, not invented.
"""

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager
import matplotlib.colors as mcolors
import numpy as np

# --- typography: serif to sit naturally next to Computer Modern body text ---
plt.rcParams.update({
    "font.family": "serif",
    "font.serif": ["DejaVu Serif", "Times New Roman", "STIXGeneral", "serif"],
    "mathtext.fontset": "dejavuserif",
    "axes.edgecolor": "#333333",
    "axes.linewidth": 0.8,
    "text.color": "#1a1a1a",
    "axes.labelcolor": "#1a1a1a",
    "xtick.color": "#1a1a1a",
    "ytick.color": "#1a1a1a",
    "figure.dpi": 200,
})

OXBLOOD = "#7a2424"

# =====================================================================
# Figure 1: 3x3 heatmap (Book I, GPT-4o)
# rows = translation register, cols = prompt style
# values = compile rate (%)
# =====================================================================
TR = ["Fitzpatrick", "Heath", "Modern"]   # rows  (translation)
PR = ["Fitzpatrick", "Heath", "Modern"]   # cols  (prompt style)
grid = np.array([
    [76.3, 60.0, 45.9],   # Fitzpatrick translation
    [67.9, 65.5, 52.6],   # Heath translation
    [73.5, 63.2, 46.8],   # Modern translation
])

# diverging-ish single-hue ramp: cool grey (low) -> oxblood (high)
cmap = mcolors.LinearSegmentedColormap.from_list(
    "oxblood_ramp", ["#c9d2ce", "#c08a7e", OXBLOOD]
)
norm = mcolors.Normalize(vmin=44, vmax=78)

fig1, ax1 = plt.subplots(figsize=(6.4, 4.4))
im = ax1.imshow(grid, cmap=cmap, norm=norm, aspect="auto")

# cell annotations
for i in range(3):
    for j in range(3):
        v = grid[i, j]
        t = (v - 44) / (78 - 44)
        color = "#1a1a1a" if t < 0.42 else "white"
        weight = "bold" if (i == 0 and j == 0) else "normal"
        ax1.text(j, i, f"{v:.1f}%", ha="center", va="center",
                 color=color, fontsize=13, fontweight=weight)

ax1.set_xticks(range(3))
ax1.set_yticks(range(3))
ax1.set_xticklabels(PR, fontsize=11)
ax1.set_yticklabels(TR, fontsize=11)
ax1.set_xlabel("Prompt style (few-shot example register)", fontsize=11.5, labelpad=8)
ax1.set_ylabel("Translation register (input text)", fontsize=11.5, labelpad=8)
ax1.xaxis.set_label_position("top")
ax1.xaxis.tick_top()

# subtle gridlines between cells
ax1.set_xticks(np.arange(-0.5, 3, 1), minor=True)
ax1.set_yticks(np.arange(-0.5, 3, 1), minor=True)
ax1.grid(which="minor", color="white", linewidth=2.2)
ax1.tick_params(which="minor", length=0)
ax1.tick_params(which="major", length=0)
for spine in ax1.spines.values():
    spine.set_visible(False)

# directional annotations: down = stable, across = collapse
ax1.annotate("", xy=(2.62, 2.45), xytext=(2.62, -0.45),
             annotation_clip=False,
             arrowprops=dict(arrowstyle="-", color="#999", lw=1, ls=(0, (1, 2))))
ax1.text(2.74, 1.0, "down a\ncolumn:\nprompt\nfixed,\ntranslation\nvaries little\n($p=0.603$)",
         fontsize=8.0, va="center", ha="left", color="#444",
         linespacing=1.25, clip_on=False)
ax1.annotate("", xy=(2.45, 2.78), xytext=(-0.45, 2.78),
             annotation_clip=False,
             arrowprops=dict(arrowstyle="->", color=OXBLOOD, lw=1.4))
ax1.text(1.0, 3.05, "across a row: prompt changes  $\\Rightarrow$  72.6% $\\to$ 48.4% collapse ($p<0.001$)",
         fontsize=8.8, va="top", ha="center", color=OXBLOOD,
         clip_on=False)

cbar = fig1.colorbar(im, ax=ax1, fraction=0.045, pad=0.30)
cbar.set_label("Compile rate (%)", fontsize=10)
cbar.ax.tick_params(labelsize=9)
cbar.outline.set_linewidth(0.6)

fig1.subplots_adjust(left=0.16, right=0.82, top=0.74, bottom=0.16)
fig1.savefig("fig_grid.pdf", bbox_inches="tight")
plt.close(fig1)

# =====================================================================
# Figure 2: contamination probe
# Qwen2.5-Coder-7B compile rate by input type + GPT-4o clean reference
# =====================================================================
qwen_labels = ["Full Heath\ntext", 'Empty\n("Prop. N")', "Garbled\nvocabulary", "Shuffled\nclauses"]
qwen_vals   = [60.5, 62.8, 60.5, 60.5]
gpt_labels  = ["Empty\ninput", "Full\nproof"]
gpt_vals    = [10.0, 67.9]

fig2, (axa, axb) = plt.subplots(1, 2, figsize=(7.2, 3.7),
                                gridspec_kw={"width_ratios": [4, 2.2], "wspace": 0.32})

# --- Qwen panel ---
xq = np.arange(len(qwen_vals))
colors_q = ["#b9b3a7", OXBLOOD, "#b9b3a7", "#b9b3a7"]
bars_q = axa.bar(xq, qwen_vals, color=colors_q, width=0.66, edgecolor="#5a544a", linewidth=0.5)
axa.set_xticks(xq)
axa.set_xticklabels(qwen_labels, fontsize=9.5)
axa.set_ylim(0, 75)
axa.set_ylabel("Compile rate (%)", fontsize=11)
axa.set_title("Qwen2.5-Coder-7B (contaminated)", fontsize=11.5, pad=10)
for x, v in zip(xq, qwen_vals):
    axa.text(x, v + 1.4, f"{v:.1f}%", ha="center", va="bottom", fontsize=9.5)
axa.axhline(qwen_vals[0], color="#999", lw=0.7, ls=(0, (2, 3)))
axa.text(3.45, 64.5, "empty input\nscores highest",
         fontsize=8.6, color=OXBLOOD, ha="right", va="bottom", style="italic")
for s in ["top", "right"]:
    axa.spines[s].set_visible(False)

# --- GPT-4o panel ---
xg = np.arange(len(gpt_vals))
colors_g = ["#b9b3a7", OXBLOOD]
axb.bar(xg, gpt_vals, color=colors_g, width=0.56, edgecolor="#5a544a", linewidth=0.5)
axb.set_xticks(xg)
axb.set_xticklabels(gpt_labels, fontsize=9.5)
axb.set_ylim(0, 75)
axb.set_title("GPT-4o (clean)", fontsize=11.5, pad=10)
for x, v in zip(xg, gpt_vals):
    axb.text(x, v + 1.4, f"{v:.0f}%" if v == 10.0 else f"{v:.1f}%",
             ha="center", va="bottom", fontsize=9.5)
axb.text(0.5, -14, "compiles only from\nthe real proof",
         fontsize=8.6, color=OXBLOOD, ha="center", va="top", style="italic",
         clip_on=False)
for s in ["top", "right"]:
    axb.spines[s].set_visible(False)

fig2.savefig("fig_contam.pdf", bbox_inches="tight")
plt.close(fig2)

print("Wrote fig_grid.pdf and fig_contam.pdf")
