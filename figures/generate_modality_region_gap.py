"""Generate Figure 7: modality x geographic-region representation-gap matrix.

Data sources (real artifacts):
  - datacards/*.json  -> dataset_id + modality.modalities + geography.regions
  - audit_experiments.csv -> per-dataset composite diversity_index

Modality groups reuse the transparent rule from generate_modality_gap.py.
Geographic regions are normalized to a fixed column order. Each (dataset, region)
pair expands into the cross table; cells show the mean composite Diversity Index
and the number of datasets n. Empty cells (--) mean no dataset of that modality
is sourced from that region: a hard coverage gap.

Output: figures/fig_modality_region_gap.png
"""
import json, glob, csv
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

SUBS = ["GEO", "POP", "SKIN", "ANN", "GEN"]


def f(x):
    try:
        return float(x)
    except Exception:
        return None


# ---- load datacards: dataset_id -> (modalities, regions) ----
dc = {}
for fp in glob.glob("datacards/*.json"):
    d = json.load(open(fp, encoding="utf-8"))
    dc[d["dataset_id"]] = (
        d.get("modality", {}).get("modalities", []),
        d.get("geography", {}).get("regions", []),
    )


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


REGION_ORDER = ["North America", "Europe", "Asia", "Africa",
                "South America", "Oceania", "Global", "Unspecified"]


def norm_region(r):
    r = (r or "").strip()
    if r.lower() == "global":
        return "Global"
    return r  # North America/Europe/Asia/Africa/South America/Oceania as-is; '' -> ''


# ---- build cross table (group, region) -> [diversity] ----
ct = {}
for r in rows:
    ds = r["dataset"]
    if ds not in dc:
        continue
    mods, regions = dc[ds]
    g = group(mods)
    div = f(r["diversity_index"])
    regs = [norm_region(x) for x in regions] if regions else [""]
    for reg in regs:
        key = (g, reg if reg in REGION_ORDER else "Unspecified")
        ct.setdefault(key, []).append(div)

# ---- group order by dataset count (exclude Other) ----
gsize = {}
for ds, (mods, _) in dc.items():
    gsize[group(mods)] = gsize.get(group(mods), 0) + 1
groups_order = [g for g in sorted(gsize, key=lambda g: -gsize[g]) if g != "Other"]

# ---- matrix ----
mat = np.full((len(groups_order), len(REGION_ORDER)), np.nan)
ns = np.zeros_like(mat, dtype=int)
for i, g in enumerate(groups_order):
    for j, reg in enumerate(REGION_ORDER):
        vals = ct.get((g, reg), [])
        if vals:
            mat[i, j] = np.mean(vals)
            ns[i, j] = len(vals)

# ---- print table for caption / manuscript use ----
print(f"{'Group':20s} | " + " | ".join(f"{r[:6]:>6s}" for r in REGION_ORDER) + "   (n per cell)")
for i, g in enumerate(groups_order):
    cells = []
    for j in range(len(REGION_ORDER)):
        if ns[i, j] > 0:
            cells.append(f"{mat[i,j]:.2f}/{ns[i,j]}")
        else:
            cells.append("  -  ")
    print(f"{g:20s} | " + " | ".join(f"{c:>6s}" for c in cells))

# ---- figure ----
fig, ax = plt.subplots(figsize=(12, max(5, 0.5 * len(groups_order) + 2)))
cmap = plt.cm.RdYlGn
im = ax.imshow(mat, aspect="auto", cmap=cmap, vmin=0, vmax=1)
ax.set_xticks(range(len(REGION_ORDER)))
ax.set_xticklabels(REGION_ORDER, fontsize=9, rotation=30, ha="right")
ax.set_yticks(range(len(groups_order)))
ax.set_yticklabels(groups_order, fontsize=9)
for i in range(len(groups_order)):
    for j in range(len(REGION_ORDER)):
        if ns[i, j] > 0:
            v = mat[i, j]
            ax.text(j, i, f"{v:.2f}\n(n={ns[i,j]})", ha="center", va="center",
                    fontsize=7, color="black" if 0.25 < v < 0.75 else "white")
        else:
            ax.text(j, i, "-", ha="center", va="center", fontsize=11, color="gray")
ax.set_title("Figure 7. Representation gaps by data modality and geographic region\n"
             "(- = no dataset of that modality sourced from that region; red = gap, green = covered)",
             fontsize=10)
cbar = fig.colorbar(im, ax=ax, shrink=0.8)
cbar.set_label("mean composite Diversity Index (0 = gap, 1 = covered)", fontsize=8)
fig.tight_layout()
fig.savefig("figures/fig_modality_region_gap.png", dpi=300, bbox_inches="tight")
print("saved figures/fig_modality_region_gap.png")
