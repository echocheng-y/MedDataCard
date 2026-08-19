"""generate_coder_b_template.py — Produce blank Coder-B annotation templates.

Outputs (under coder_b_template/):
  * coder_b_blank.csv        — one row per (dataset, scored field); columns:
        dataset_id, field_path, field_type, definition, source_ref, coder_b_value
      `coder_b_value` is left EMPTY for the human coder to fill.
  * <name>.json              — one blank JSON per dataset, same structure as
        gold/<name>.json but with the 5 scored fields emptied:
            modality.modalities      -> []
            modality.sample_counts   -> {}
            geography.countries      -> []
            tasks_and_use.intended_tasks -> []
            metadata.source_type     -> ""

This script does NOT annotate anything; it only scaffolds the form a second
independent coder fills in. See IAA_PROTOCOL.md for the encoding rules.

Standard library only.
"""
from __future__ import annotations

import csv
import json
from pathlib import Path

ROOT = Path(__file__).parent
GOLD = ROOT / "gold"
OUTDIR = ROOT / "coder_b_template"

SCORED_FIELDS = [
    "modality.modalities",
    "modality.sample_counts",
    "geography.countries",
    "tasks_and_use.intended_tasks",
    "metadata.source_type",
]
FIELD_TYPE = {
    "modality.modalities": "set",
    "geography.countries": "set",
    "tasks_and_use.intended_tasks": "set",
    "modality.sample_counts": "counts",
    "metadata.source_type": "categorical",
}
DEFINITION = {
    "modality.modalities":
        "SET. List every atomic modality EXPLICITLY stated or directly derivable from the "
        "source text (e.g. X-ray, MRI, EHR, text, genomic). Normalize casing; merge obvious "
        "synonyms to the gold vocabulary. Do NOT infer from the catalogue.",
    "modality.sample_counts":
        "COUNTS dict. Keys MUST match the gold key names EXACTLY (e.g. patients, images, "
        "admissions, questions, cells). Report only counts explicitly stated or directly "
        "computable. Omit a key if not stated; never guess.",
    "geography.countries":
        "SET. List countries explicitly named for data collection / subject source. Leave [] "
        "if none stated. Do NOT infer region from institution alone.",
    "tasks_and_use.intended_tasks":
        "SET. List intended tasks explicitly stated (e.g. classification, segmentation, qa, "
        "retrieval, causal). Use the gold vocabulary; do not invent tasks.",
    "metadata.source_type":
        "CATEGORICAL, exactly one of: repository / challenge / paper-supplement / registry / "
        "other. Choose the single best label for how the dataset is distributed/published.",
}
EMPTY_VALUE = {
    "modality.modalities": [],
    "geography.countries": [],
    "tasks_and_use.intended_tasks": [],
    "modality.sample_counts": {},
    "metadata.source_type": "",
}


def main():
    OUTDIR.mkdir(parents=True, exist_ok=True)
    csv_path = OUTDIR / "coder_b_blank.csv"
    rows = []
    n_json = 0
    for gpath in sorted(GOLD.glob("*.json")):
        d = json.loads(gpath.read_text(encoding="utf-8"))
        ds_id = d.get("dataset_id", gpath.stem)
        source_ref = f"sources/{gpath.name.replace('.json', '.txt')}"
        # blank JSON skeleton
        blank = {
            "dataset_id": ds_id,
            "comparable": {f: EMPTY_VALUE[f] for f in SCORED_FIELDS},
        }
        (OUTDIR / gpath.name).write_text(
            json.dumps(blank, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        n_json += 1
        # CSV rows
        for f in SCORED_FIELDS:
            rows.append({
                "dataset_id": ds_id,
                "field_path": f,
                "field_type": FIELD_TYPE[f],
                "definition": DEFINITION[f],
                "source_ref": source_ref,
                "coder_b_value": "",
            })

    with csv_path.open("w", encoding="utf-8-sig", newline="") as fh:
        w = csv.DictWriter(
            fh,
            fieldnames=["dataset_id", "field_path", "field_type",
                        "definition", "source_ref", "coder_b_value"],
        )
        w.writeheader()
        w.writerows(rows)

    print(f"Wrote {n_json} blank JSON files -> {OUTDIR}/")
    print(f"Wrote template CSV       -> {csv_path}  ({len(rows)} rows = 26 datasets x 5 fields)")
    print("Next: second coder fills coder_b_value in the CSV (or the JSON files), then")
    print("       copies the filled JSONs into coder_b/ and runs: python compute_iaa.py")


if __name__ == "__main__":
    main()
