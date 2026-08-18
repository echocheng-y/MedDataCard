"""Compliance-gap audit + dataset diversity score.

For the 26 generated ST data cards this script computes:
  (A) ST pillar completeness (P1 description/access, P2 population/geography,
      P3 bias/annotation, P4 ethics) and a composite ST Compliance Index;
  (B) a Dataset Diversity Score with five sub-indicators:
        GEO  – geographic representativeness (countries + single-center penalty)
        POP  – demographic reporting (age / sex / ethnicity stated)
        SKIN – skin-tone / Fitzpatrick reporting (0/1 proxy)
        ANN  – annotation provenance (expert/consensus > semi > auto/unknown)
        GEN  – generalizability statement present (0/1)
  (C) weight-sensitivity: rank stability of the composite index and the diversity
      score under 200 random Dirichlet weight vectors (Spearman vs equal-weight base).

Outputs: audit_experiments.csv (per-dataset) + console summary.
"""
from __future__ import annotations

import csv
import json
import math
import random
from pathlib import Path

from schema_utils import load_schema

HERE = Path(__file__).parent
CARDS = HERE / "datacards"
SCHEMA = load_schema()

# ST pillar → schema groups used for completeness.
PILLARS = {
    "P1": ["metadata", "data_origin"],
    "P2": ["population", "geography"],
    "P3": ["bias_and_limitations", "annotation"],
    "P4": ["ethics"],
}
ALL_GROUPS = ["metadata", "data_origin", "population", "geography",
              "modality", "annotation", "ethics", "bias_and_limitations"]


def group_completeness(card: dict, group: str) -> float:
    props = SCHEMA["properties"].get(group, {}).get("properties")
    if not props:
        return 0.0
    filled = 0
    for k in props:
        v = card.get(group, {}).get(k) if isinstance(card.get(group), dict) else None
        if v not in (None, "", [], {}):
            filled += 1
    return 100.0 * filled / len(props)


def get_path(card, path):
    cur = card
    for p in path.split("."):
        if isinstance(cur, dict) and p in cur:
            cur = cur[p]
        else:
            return None
    return cur


def diversity_subindicators(card: dict) -> dict:
    # GEO
    geo = card.get("geography", {})
    countries = geo.get("countries", []) or []
    c = min(len(countries), 3) / 3.0
    if geo.get("data_collection_setting") == "single-center":
        c *= 0.3
    # POP (key presence = the dataset addressed the question)
    pop = card.get("population", {})
    pop_flags = [
        1.0 if "age_reported" in pop else 0.0,
        1.0 if "sex" in pop else 0.0,
        1.0 if "ethnicity_reported" in pop else 0.0,
    ]
    pop_score = sum(pop_flags) / 3.0
    # SKIN (proxy)
    blob = json.dumps(card.get("bias_and_limitations", {}), ensure_ascii=False).lower()
    skin = 1.0 if any(k in blob for k in ("skin", "fitzpatrick", "肤色", "肤色偏倚", "skin tone")) else 0.0
    # ANN
    at = (card.get("annotation", {}).get("annotation_type") or "").lower()
    ann = {"expert": 1.0, "consensus": 1.0, "semi-automatic": 0.5}.get(at, 0.0)
    # GEN
    gen = 1.0 if (card.get("bias_and_limitations", {}).get("generalizability_statement") not in (None, "",)) else 0.0
    return {"GEO": round(c, 3), "POP": round(pop_score, 3),
            "SKIN": skin, "ANN": ann, "GEN": gen}


def spearman(a, b):
    def rank(x):
        order = sorted(range(len(x)), key=lambda i: x[i])
        r = [0.0] * len(x)
        i = 0
        while i < len(x):
            j = i
            while j + 1 < len(x) and x[order[j + 1]] == x[order[i]]:
                j += 1
            avg = (i + j) / 2.0 + 1.0
            for k in range(i, j + 1):
                r[order[k]] = avg
            i = j + 1
        return r
    ra, rb = rank(a), rank(b)
    ma, mb = sum(ra) / len(ra), sum(rb) / len(rb)
    da = [x - ma for x in ra]; db = [x - mb for x in rb]
    num = sum(x * y for x, y in zip(da, db))
    den = math.sqrt(sum(x * x for x in da) * sum(y * y for y in db))
    return num / den if den else 1.0


def weighted(weights, scores):
    return sum(w * s for w, s in zip(weights, scores))


def main():
    random.seed(42)
    cards = [json.loads(f.read_text(encoding="utf-8")) for f in sorted(CARDS.glob("*.json"))]
    names = [c.get("dataset_id") for c in cards]

    # base (equal) pillar weights
    base_pw = [0.25, 0.25, 0.25, 0.25]
    base_dw = [0.2, 0.2, 0.2, 0.2, 0.2]

    rows = []
    p_scores = {p: [] for p in PILLARS}
    d_scores = {k: [] for k in ("GEO", "POP", "SKIN", "ANN", "GEN")}
    for c in cards:
        comp = {p: sum(group_completeness(c, g) for g in gs) / len(gs) for p, gs in PILLARS.items()}
        for p in PILLARS:
            p_scores[p].append(comp[p])
        div = diversity_subindicators(c)
        for k in div:
            d_scores[k].append(div[k])
        pci = weighted(base_pw, [comp[p] for p in PILLARS])
        dci = weighted(base_dw, [div[k] for k in ("GEO", "POP", "SKIN", "ANN", "GEN")])
        rows.append({
            "dataset": c.get("dataset_id"),
            "method": c.get("extraction", {}).get("method"),
            "P1_description": round(comp["P1"], 1), "P2_population": round(comp["P2"], 1),
            "P3_bias": round(comp["P3"], 1), "P4_ethics": round(comp["P4"], 1),
            "st_compliance_index": round(pci, 1),
            "GEO": div["GEO"], "POP": div["POP"], "SKIN": div["SKIN"], "ANN": div["ANN"], "GEN": div["GEN"],
            "diversity_index": round(dci, 3),
        })

    # weight sensitivity
    base_pci_rank = [r["st_compliance_index"] for r in rows]
    base_dci_rank = [r["diversity_index"] for r in rows]
    pci_corrs, dci_corrs = [], []
    for _ in range(200):
        pw = [random.random() for _ in range(4)]; s = sum(pw); pw = [x / s for x in pw]
        dw = [random.random() for _ in range(5)]; s = sum(dw); dw = [x / s for x in dw]
        pci_alt = [weighted(pw, [comp_p, comp_q, comp_r, comp_s])
                   for comp_p, comp_q, comp_r, comp_s in
                   zip(p_scores["P1"], p_scores["P2"], p_scores["P3"], p_scores["P4"])]
        dci_alt = [weighted(dw, [g, po, sk, an, ge])
                   for g, po, sk, an, ge in
                   zip(d_scores["GEO"], d_scores["POP"], d_scores["SKIN"], d_scores["ANN"], d_scores["GEN"])]
        pci_corrs.append(spearman(base_pci_rank, pci_alt))
        dci_corrs.append(spearman(base_dci_rank, dci_alt))
    mean_pci_corr = round(sum(pci_corrs) / len(pci_corrs), 3)
    min_pci_corr = round(min(pci_corrs), 3)
    mean_dci_corr = round(sum(dci_corrs) / len(dci_corrs), 3)
    min_dci_corr = round(min(dci_corrs), 3)

    out = HERE / "audit_experiments.csv"
    with open(out, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)

    n = len(rows)
    print(f"Cards analysed: {n}")
    print(f"Mean ST pillar completeness: "
          + ", ".join(f"{p}={sum(p_scores[p])/n:.1f}" for p in PILLARS))
    print(f"Mean ST Compliance Index (equal weights): "
          + f"{sum(r['st_compliance_index'] for r in rows)/n:.1f}")
    print(f"Mean Diversity Index: {sum(r['diversity_index'] for r in rows)/n:.3f}")
    print(f"  GEO={sum(d_scores['GEO'])/n:.2f} POP={sum(d_scores['POP'])/n:.2f} "
          f"SKIN={sum(d_scores['SKIN'])/n:.2f} ANN={sum(d_scores['ANN'])/n:.2f} "
          f"GEN={sum(d_scores['GEN'])/n:.2f}")
    print(f"Weight sensitivity (200 Dirichlet vectors, Spearman vs equal-weight):")
    print(f"  ST Compliance Index:  mean ρ={mean_pci_corr}  min ρ={min_pci_corr}")
    print(f"  Diversity Index:      mean ρ={mean_dci_corr}  min ρ={min_dci_corr}")
    print(f"→ {out}")


if __name__ == "__main__":
    main()
