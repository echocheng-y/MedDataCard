"""Generate the paper-grade representation-gap heatmap (Figure 5).

Source of truth: audit_experiments.csv (26 datasets, 5 diversity sub-indicators).
Reproducible; run with: python figures/generate_representation_gap.py
"""
import csv
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

SRC = "audit_experiments.csv"
OUT = "figures/fig_representation_gap.png"
SUBS = ["GEO", "POP", "SKIN", "ANN", "GEN"]
SUBS_LABEL = {
    "GEO": "GEO\n(geographic\nrepresentativeness)",
    "POP": "POP\n(population\nsubgroup report)",
    "SKIN": "SKIN\n(skin tone /\nFitzpatrick)",
    "ANN": "ANN\n(annotation\nprovenance)",
    "GEN": "GEN\n(generalizability\nstatement)",
}

rows = list(csv.DictReader(open(SRC, encoding="utf-8")))
def f(x):
    try:
        return float(x)
    except Exception:
        return 0.0

# sort by composite diversity ascending -> worst at top
rows = sorted(rows, key=lambda r: f(r["diversity_index"]))
names = [r["dataset"] for r in rows]
mat = np.array([[f(r[s]) for s in SUBS] for r in rows])
means = [float(np.mean(mat[:, i])) for i in range(len(SUBS))]
div = np.array([f(r["diversity_index"]) for r in rows])
# append composite Diversity Index as a 6th column
mat6 = np.hstack([mat, div.reshape(-1, 1)])
COLS = SUBS + ["DIV"]
COLS_LABEL = SUBS_LABEL.copy()
COLS_LABEL["DIV"] = "DIV\n(composite\nDiversity Index)"

fig, (axA, axB) = plt.subplots(
    1, 2, figsize=(11.5, 9), gridspec_kw={"width_ratios": [3.0, 1.05]}
)

# ---- Panel A: per-dataset heatmap ----
cmap = plt.cm.RdYlGn  # 0=red (gap), 1=green (covered)
im = axA.imshow(mat6, aspect="auto", cmap=cmap, vmin=0, vmax=1)
axA.set_xticks(range(len(COLS)))
axA.set_xticklabels([COLS_LABEL[c] for c in COLS], fontsize=8)
axA.set_yticks(range(len(names)))
axA.set_yticklabels(names, fontsize=7)
# value annotations
for i in range(len(names)):
    for j in range(len(COLS)):
        v = mat6[i, j]
        axA.text(j, i, f"{v:.2f}", ha="center", va="center",
                 fontsize=6.2, color="black" if 0.25 < v < 0.75 else "white")
axA.set_title("A. Representation-gap heatmap across 26 medical-AI datasets\n"
              "(sorted by composite Diversity Index, worst at top)",
              fontsize=9.5)
cbar = fig.colorbar(im, ax=axA, shrink=0.55, pad=0.02)
cbar.set_label("sub-indicator coverage (0 = gap, 1 = covered)", fontsize=8)

# ---- Panel B: mean gap per dimension ----
ypos = np.arange(len(SUBS))
axB.barh(ypos, means, color=[cmap(m) for m in means])
axB.set_yticks(ypos)
axB.set_yticklabels(SUBS, fontsize=8)
axB.invert_yaxis()
for i, m in enumerate(means):
    axB.text(m + 0.01, i, f"{m:.2f}", va="center", fontsize=8)
axB.set_xlim(0, 1.05)
axB.set_xlabel("mean coverage", fontsize=8)
axB.set_title("B. Mean gap by dimension\n(n=26)", fontsize=9.5)
axB.axvline(0.5, color="grey", ls="--", lw=0.8)

fig.suptitle("Figure 5. Representation gaps in medical-AI datasets: "
             "geographic (GEO 0.21) and skin-tone (SKIN 0.12) reporting are "
             "the dominant blind spots", fontsize=11, fontweight="bold", y=0.99)
fig.tight_layout(rect=[0, 0, 1, 0.95])
fig.savefig(OUT, dpi=300, bbox_inches="tight")
print("WROTE", OUT)
print("mean sub-indicators:", dict(zip(SUBS, [round(m, 3) for m in means])))
