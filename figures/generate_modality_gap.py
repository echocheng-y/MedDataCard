"""Generate Figure 6: modality-stratified representation-gap view.

Data sources (real artifacts):
  - datacards/*.json  -> dataset_id + modality.modalities (primary modality label)
  - audit_experiments.csv -> per-dataset GEO/POP/SKIN/ANN/GEN + diversity_index

Groups are assigned by a transparent rule:
  >=3 distinct modality tokens -> "Multi-modal"
  else by dominant family (pathology-WSI / text / imaging / genomics / physio / EHR).

Outputs figures/fig_modality_gap.png (1x2 panel).
"""
import json, glob, csv
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

SUBS = ["GEO", "POP", "SKIN", "ANN", "GEN"]
SUBS_LABEL = {"GEO": "Geography", "POP": "Population",
              "SKIN": "Skin/Fitzpatrick", "ANN": "Annotation", "GEN": "Generalizability"}

def f(x):
    try:
        return float(x)
    except Exception:
        return None

# ---- load datacards: dataset_id -> modalities ----
dc = {}
for fp in glob.glob("datacards/*.json"):
    d = json.load(open(fp, encoding="utf-8"))
    dc[d["dataset_id"]] = d.get("modality", {}).get("modalities", [])

# ---- load audit ----
rows = list(csv.DictReader(open("audit_experiments.csv", encoding="utf-8")))

def group(ms):
    s = set(ms)
    if len(s) >= 3:
        return "Multi-modal"
    if "pathology-WSI" in s:
        return "Pathology"
    if s <= {"text"}:
        return "Text/NLP"
    if s & {"MRI", "CT", "X-ray", "ultrasound", "fundus", "dermoscopy"}:
        return "Radiology/Imaging"
    if s & {"genomic", "single-cell"}:
        return "Genomics"
    if s & {"EEG", "ECG"}:
        return "Physio time-series"
    if "EHR" in s:
        return "EHR/Tabular"
    return "Other"

gmap = {r["dataset"]: group(dc[r["dataset"]]) for r in rows}
groups = {}
for r in rows:
    groups.setdefault(gmap[r["dataset"]], []).append(r)

# ---- compute group means ----
order = sorted([g for g in groups if g != "Other"],
               key=lambda g: -len(groups[g]))
stats = {}
print(f"{'Group':20s} {'n':>3s}  GEO   POP   SKIN  ANN   GEN   DIV")
for g in order:
    rs = groups[g]
    means = [np.mean([f(r[s]) for r in rs]) for s in SUBS]
    div = np.mean([f(r["diversity_index"]) for r in rs])
    stats[g] = (len(rs), means, div)
    print(f"{g:20s} {len(rs):3d}  " + "  ".join(f"{m:.2f}" for m in means) + f"  {div:.3f}")

# ---- figure ----
mat = np.array([stats[g][1] for g in order])           # groups x 5
ns = [stats[g][0] for g in order]
divs = [stats[g][2] for g in order]

fig, (axA, axB) = plt.subplots(1, 2, figsize=(12, max(5, 0.42*len(order)+2)),
                               gridspec_kw={"width_ratios": [2.3, 1.4]})

cmap = plt.cm.RdYlGn
im = axA.imshow(mat, aspect="auto", cmap=cmap, vmin=0, vmax=1)
axA.set_xticks(range(len(SUBS)))
axA.set_xticklabels([SUBS_LABEL[s] for s in SUBS], fontsize=8.5)
ylab = [f"{g}\n(n={n})" for g, n in zip(order, ns)]
axA.set_yticks(range(len(order)))
axA.set_yticklabels(ylab, fontsize=8.5)
for i in range(len(order)):
    for j in range(len(SUBS)):
        v = mat[i, j]
        axA.text(j, i, f"{v:.2f}", ha="center", va="center",
                 fontsize=7.5, color="black" if 0.25 < v < 0.75 else "white")
axA.set_title("A. Mean representation-gap sub-indicator by data modality\n"
              "(red = gap, green = covered; n per group annotated)", fontsize=10)
cbar = fig.colorbar(im, ax=axA, shrink=0.7, pad=0.02)
cbar.set_label("mean sub-indicator coverage (0=gap, 1=covered)", fontsize=8)

# Panel B: composite Diversity Index per modality group
order_b = [g for g, _ in sorted(stats.items(), key=lambda kv: kv[1][2])]
divs_b = [stats[g][2] for g in order_b]
ns_b = [stats[g][0] for g in order_b]
yp = np.arange(len(order_b))
bars = axB.barh(yp, divs_b, color=[cmap(v) for v in divs_b])
axB.set_yticks(yp)
axB.set_yticklabels([f"{g} (n={n})" for g, n in zip(order_b, ns_b)], fontsize=8.5)
axB.set_xlim(0, 1)
axB.set_xlabel("composite Diversity Index", fontsize=9)
axB.set_title("B. Composite Diversity Index by modality", fontsize=10)
for i, v in enumerate(divs_b):
    axB.text(v + 0.01, i, f"{v:.2f}", va="center", fontsize=8)

fig.suptitle("Figure 6. Representation gaps are uneven across data modalities",
             fontsize=11, fontweight="bold")
fig.tight_layout(rect=[0, 0, 1, 0.96])
fig.savefig("figures/fig_modality_gap.png", dpi=300, bbox_inches="tight")
print("saved figures/fig_modality_gap.png")
