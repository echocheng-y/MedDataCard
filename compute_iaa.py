"""compute_iaa.py — Second-coder Inter-Annotator Agreement (IAA) for the MedDataCard gold standard.

====================================================================================
HONESTY CONSTRAINT (DO NOT VIOLATE)
------------------------------------------------------------------------------------
This script NEVER fabricates a Coder B annotation or any IAA number.

  * Real Coder B annotations live in  coder_b/<name>.json  (same structure as
    gold/<name>.json: {"dataset_id", "comparable": {...}}).
  * If coder_b/ is absent or incomplete, the script FAILS GRACEFULLY and prints
    instructions to the operator. It never invents numbers.
  * `--selftest` runs gold-vs-gold purely as a MATH SANITY CHECK. It asserts
    kappa == 1.0 etc. It is explicitly labeled "selftest: gold-vs-gold sanity
    check (not real IAA)" and MUST NOT be reported as real IAA.

All IAA numbers produced for the manuscript are therefore PENDING until a real
second human coder fills coder_b/ and this script is run in real mode.
====================================================================================

Metrics (see IAA_PROTOCOL.md for full rationale):
  * metadata.source_type  -> Cohen's kappa over the 5 observed categories.
  * 3 set fields (modalities / countries / intended_tasks)
                          -> binary (present/absent) expansion across all atomic
                             values -> Cohen's kappa, plus mean Jaccard.
  * modality.sample_counts -> per-key exact-match rate + overall exact-match rate
                             (no kappa is forced onto a count dict).
  * 95% confidence intervals via 2000-draw bootstrap over datasets (kappa metrics)
    or over (dataset, key) cells (sample_counts).

Standard library only (json, csv, random, math, pathlib, argparse).
"""
from __future__ import annotations

import json
import math
import random
import argparse
from pathlib import Path

ROOT = Path(__file__).parent
GOLD = ROOT / "gold"
CODER_B = ROOT / "coder_b"
OUT = ROOT / "iaa_report.json"

# --- Scored fields (identical to evaluate_m4.SCORED_FIELDS) ---------------------
SCORED_FIELDS = [
    "modality.modalities",
    "modality.sample_counts",
    "geography.countries",
    "tasks_and_use.intended_tasks",
    "metadata.source_type",
]
SET_FIELDS = ["modality.modalities", "geography.countries", "tasks_and_use.intended_tasks"]
SOURCE_TYPE_FIELD = "metadata.source_type"
COUNTS_FIELD = "modality.sample_counts"

# The 5-category space actually observed in gold/. (The JSON schema enum additionally
# lists "commercial", but no dataset in the current corpus is labeled commercial, so
# IAA is computed on the 5 categories that occur; see IAA_PROTOCOL.md.)
SOURCE_TYPE_CATS = ["repository", "challenge", "paper-supplement", "registry", "other"]

N_BOOT = 2000

_FIELD_TYPE = {
    "modality.modalities": "set",
    "geography.countries": "set",
    "tasks_and_use.intended_tasks": "set",
    "modality.sample_counts": "counts",
    "metadata.source_type": "categorical",
}


# --- Reused helpers (semantics copied from evaluate_m4.py) ----------------------
def get_path(card: dict, path: str):
    cur = card
    for p in path.split("."):
        if isinstance(cur, dict) and p in cur:
            cur = cur[p]
        else:
            return None
    return cur


def get_field(comp: dict, field: str):
    """The gold/coder_b `comparable` dict uses the DOTTED PATH as a LITERAL KEY
    (e.g. comparable["modality.modalities"]), so we read it directly rather than
    via nested traversal."""
    return comp.get(field)


def _as_set(v):
    return set(v) if isinstance(v, list) else (set() if v is None else {v})


def cohen_kappa(labels_a: list, labels_b: list) -> float:
    """Cohen's kappa over paired categorical labels (pure-python, no numpy)."""
    n = len(labels_a)
    if n == 0:
        return 1.0
    cats = sorted(set(labels_a) | set(labels_b))
    cm = {(a, b): 0 for a in cats for b in cats}
    for a, b in zip(labels_a, labels_b):
        cm[(a, b)] += 1
    po = sum(cm[(c, c)] for c in cats) / n if n else 1.0
    row = {c: sum(cm[(c, x)] for x in cats) for c in cats}
    col = {c: sum(cm[(x, c)] for x in cats) for c in cats}
    pe = sum(row[c] * col[c] for c in cats) / (n * n) if n else 1.0
    if pe >= 1.0:
        return 1.0
    return (po - pe) / (1 - pe)


def _jaccard(a: set, b: set) -> float:
    union = a | b
    if not union:
        return 1.0
    return len(a & b) / len(union)


# --- Loading --------------------------------------------------------------------
def load_comparable(path: Path):
    d = json.loads(Path(path).read_text(encoding="utf-8"))
    return d.get("dataset_id"), d.get("comparable", {})


def list_gold_files():
    return sorted(GOLD.glob("*.json"))


# --- Core metric builders --------------------------------------------------------
def build_source_type_pairs(pairs):
    """pairs: list of (a_label, b_label). Returns the paired label lists."""
    a = [str(x[0]) for x in pairs]
    b = [str(x[1]) for x in pairs]
    return a, b


def build_set_binary(pairs):
    """pairs: list of (a_set, b_set). Expand to binary present/absent decisions
    over the union of atomic values. Returns (labels_a, labels_b) for kappa."""
    universe = sorted({v for a, b in pairs for v in (a | b)})
    la, lb = [], []
    for v in universe:
        for a, b in pairs:
            la.append(1 if v in a else 0)
            lb.append(1 if v in b else 0)
    return la, lb


def build_counts_cells(pairs):
    """pairs: list of (a_dict, b_dict). Returns list of match booleans over the
    union of keys, plus per-key aggregation."""
    cells = []
    per_key = {}
    for a, b in pairs:
        a = a or {}
        b = b or {}
        keys = sorted(set(a) | set(b))
        for k in keys:
            av = a.get(k)
            bv = b.get(k)
            ok = (av is not None) and (bv is not None) and (av == bv)
            cells.append(ok)
            per_key.setdefault(k, []).append(ok)
    return cells, per_key


# --- Bootstrap -------------------------------------------------------------------
def _bootstrap_kappa(pairs, builder, n_boot=N_BOOT, seed=20260819):
    """Bootstrap CI for a kappa-style metric. `pairs` are the per-dataset units;
    `builder` turns (possibly resampled) pairs into (la, lb) label lists."""
    rng = random.Random(seed)
    base_la, base_lb = builder(pairs)
    base = cohen_kappa(base_la, base_lb)
    m = len(pairs)
    stats = []
    for _ in range(n_boot):
        idx = [rng.randrange(m) for _ in range(m)]
        samp = [pairs[i] for i in idx]
        la, lb = builder(samp)
        stats.append(cohen_kappa(la, lb))
    stats.sort()
    lo = stats[int(0.025 * (n_boot - 1))]
    hi = stats[int(0.975 * (n_boot - 1))]
    return base, (lo, hi)


def _bootstrap_rate(cells, n_boot=N_BOOT, seed=20260819):
    rng = random.Random(seed)
    base = sum(cells) / len(cells) if cells else 1.0
    m = len(cells)
    stats = []
    for _ in range(n_boot):
        idx = [rng.randrange(m) for _ in range(m)]
        stats.append(sum(cells[i] for i in idx) / m)
    stats.sort()
    lo = stats[int(0.025 * (n_boot - 1))]
    hi = stats[int(0.975 * (n_boot - 1))]
    return base, (lo, hi)


# --- Compute over a set of (gold_comparable, coderb_comparable) ------------------
def compute(pairs_by_field, n_datasets, mode):
    metrics = {}

    # source_type
    st_pairs = pairs_by_field[SOURCE_TYPE_FIELD]
    k_base, k_ci = _bootstrap_kappa(st_pairs, build_source_type_pairs)
    metrics[SOURCE_TYPE_FIELD] = {
        "field_type": "categorical",
        "method": "Cohen's kappa over 5 categories (repository/challenge/paper-supplement/registry/other)",
        "cohen_kappa": round(k_base, 6),
        "ci95": [round(k_ci[0], 6), round(k_ci[1], 6)],
        "n": len(st_pairs),
    }

    # set fields
    for f in SET_FIELDS:
        sp = pairs_by_field[f]
        k_base, k_ci = _bootstrap_kappa(sp, build_set_binary)
        jaccards = [_jaccard(a, b) for a, b in sp]
        mean_j = sum(jaccards) / len(jaccards) if jaccards else 1.0
        universe = sorted({v for a, b in sp for v in (a | b)})
        metrics[f] = {
            "field_type": "set",
            "method": "binary (present/absent) expansion across atomic values -> Cohen's kappa; mean Jaccard over datasets",
            "cohen_kappa": round(k_base, 6),
            "ci95": [round(k_ci[0], 6), round(k_ci[1], 6)],
            "mean_jaccard": round(mean_j, 6),
            "n_atomic_values": len(universe),
            "n_datasets": len(sp),
        }

    # sample_counts
    sc_pairs = pairs_by_field[COUNTS_FIELD]
    cells, per_key = build_counts_cells(sc_pairs)
    rate_base, rate_ci = _bootstrap_rate(cells)
    pk = {k: round(sum(v) / len(v), 6) for k, v in sorted(per_key.items())}
    metrics[COUNTS_FIELD] = {
        "field_type": "counts",
        "method": "per-key exact-match (key+value); no kappa forced",
        "overall_agreement": round(rate_base, 6),
        "ci95": [round(rate_ci[0], 6), round(rate_ci[1], 6)],
        "n_cells": len(cells),
        "per_key_agreement": pk,
    }

    report = {
        "mode": mode,
        "note": (
            "selftest: gold-vs-gold sanity check (not real IAA)"
            if mode.startswith("selftest")
            else "REAL IAA: Coder A (gold) vs Coder B (coder_b/). All numbers PENDING until "
                 "a second human coder completes coder_b/ and this script is rerun in real mode."
        ),
        "n_datasets": n_datasets,
        "n_cells": n_datasets * len(SCORED_FIELDS),
        "scored_fields": SCORED_FIELDS,
        "metrics": metrics,
        "overall_conclusion": (
            "PENDING — report after second coder completes; see IAA_PROTOCOL.md. "
            "Do not cite any kappa/agreement value until then."
        ),
    }
    return report


# --- Drivers ---------------------------------------------------------------------
def run_selftest():
    """Use gold as BOTH Coder A and Coder B. Assert kappa == 1.0 etc.
    This only proves the math is correct; it is NOT real IAA."""
    print("=== SELFTEST: gold vs gold (math sanity check, NOT real IAA) ===")
    pairs_by_field = {f: [] for f in SCORED_FIELDS}
    n = 0
    for gpath in list_gold_files():
        _, gcomp = load_comparable(gpath)
        # Coder B == Coder A (gold) for the sanity check
        for f in SCORED_FIELDS:
            gv = get_field(gcomp, f)
            pairs_by_field[f].append((_as_set(gv) if f in SET_FIELDS else (gv or {} if f == COUNTS_FIELD else gv),
                                      _as_set(gv) if f in SET_FIELDS else (gv or {} if f == COUNTS_FIELD else gv)))
        n += 1

    report = compute(pairs_by_field, n, mode="selftest-gold-vs-gold")

    # Assertions — the whole point of the selftest.
    eps = 1e-9
    assert abs(report["metrics"][SOURCE_TYPE_FIELD]["cohen_kappa"] - 1.0) < eps, "source_type kappa != 1.0"
    for f in SET_FIELDS:
        assert abs(report["metrics"][f]["cohen_kappa"] - 1.0) < eps, f"{f} kappa != 1.0"
        assert abs(report["metrics"][f]["mean_jaccard"] - 1.0) < eps, f"{f} jaccard != 1.0"
    assert abs(report["metrics"][COUNTS_FIELD]["overall_agreement"] - 1.0) < eps, "sample_counts agreement != 1.0"

    print(f"Datasets: {n}  Cells: {report['n_cells']}")
    print(f"source_type kappa = {report['metrics'][SOURCE_TYPE_FIELD]['cohen_kappa']:.6f}  "
          f"CI95 = {report['metrics'][SOURCE_TYPE_FIELD]['ci95']}")
    for f in SET_FIELDS:
        m = report["metrics"][f]
        print(f"{f}: kappa = {m['cohen_kappa']:.6f}  mean_jaccard = {m['mean_jaccard']:.6f}  "
              f"atomic_values = {m['n_atomic_values']}")
    sc = report["metrics"][COUNTS_FIELD]
    print(f"sample_counts overall_agreement = {sc['overall_agreement']:.6f}  cells = {sc['n_cells']}")
    print("SELFTEST PASSED: all kappa=1.0, jaccard=1.0, sample_counts=100% (gold vs gold).")
    print("WARNING: this is a sanity check only; it is NOT real Coder-B IAA.")

    OUT.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Report written -> {OUT.name} (mode={report['mode']})")
    return report


def run_real():
    print("=== REAL IAA: Coder A (gold/) vs Coder B (coder_b/) ===")
    if not CODER_B.exists():
        raise SystemExit(
            "\n[ERROR] coder_b/ directory not found.\n"
            "        Real IAA cannot run. Please have the second independent coder fill\n"
            "        coder_b/<name>.json for every dataset (same structure as gold/), then rerun:\n"
            "            python compute_iaa.py\n"
            "        No IAA numbers are fabricated in the meantime — all values remain PENDING.\n"
        )
    pairs_by_field = {f: [] for f in SCORED_FIELDS}
    n = 0
    for gpath in list_gold_files():
        name = gpath.name
        bpath = CODER_B / name
        if not bpath.exists():
            raise SystemExit(
                f"\n[ERROR] Missing Coder B file: {bpath}\n"
                f"        The second coder has not annotated '{name}' yet.\n"
                f"        All 26 datasets must be double-coded before IAA can be computed.\n"
                f"        (No numbers are fabricated — IAA remains PENDING.)\n"
            )
        _, gcomp = load_comparable(gpath)
        _, bcomp = load_comparable(bpath)
        for f in SCORED_FIELDS:
            if f not in gcomp or f not in bcomp:
                raise SystemExit(
                    f"\n[ERROR] Field '{f}' missing in gold or coder_b for '{name}'.\n"
                    f"        Coder B must provide all 5 scored fields. IAA remains PENDING.\n"
                )
            gv = get_field(gcomp, f)
            bv = get_field(bcomp, f)
            if f in SET_FIELDS:
                pairs_by_field[f].append((_as_set(gv), _as_set(bv)))
            elif f == COUNTS_FIELD:
                pairs_by_field[f].append((gv or {}, bv or {}))
            else:
                pairs_by_field[f].append((gv, bv))
        n += 1

    report = compute(pairs_by_field, n, mode="real-coder-b")
    OUT.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Datasets: {n}  Cells: {report['n_cells']}")
    print(f"source_type kappa = {report['metrics'][SOURCE_TYPE_FIELD]['cohen_kappa']:.4f}  "
          f"CI95 = {report['metrics'][SOURCE_TYPE_FIELD]['ci95']}")
    for f in SET_FIELDS:
        m = report["metrics"][f]
        print(f"{f}: kappa = {m['cohen_kappa']:.4f}  mean_jaccard = {m['mean_jaccard']:.4f}")
    sc = report["metrics"][COUNTS_FIELD]
    print(f"sample_counts overall_agreement = {sc['overall_agreement']:.4f}  cells = {sc['n_cells']}")
    print(f"Report written -> {OUT.name} (mode={report['mode']})")
    return report


def main():
    ap = argparse.ArgumentParser(description="MedDataCard second-coder IAA (Cohen's kappa).")
    ap.add_argument("--selftest", action="store_true",
                    help="Run gold-vs-gold math sanity check (NOT real IAA).")
    args = ap.parse_args()
    # Bootstrap resampling uses a fixed internal seed for reproducible CIs.
    if args.selftest:
        run_selftest()
    else:
        run_real()


if __name__ == "__main__":
    main()
