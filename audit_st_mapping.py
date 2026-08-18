"""ST recommendation → schema mapping + standard-fidelity coverage.

The published STANDING Together consensus (Lancet Digit Health / NEJM AI, 2024-12-18)
contains 29 recommendations total: 18 for *Documentation* (items 1.1a–1.4c) and 11 for
*Use*. A data card can only operationalise the 18 Documentation items; the 11 Use items
are governance-level (evaluation/deployment) and are referenced, not cardable.

This script:
  (1) maps each of the 18 Documentation recommendations to schema field(s);
  (2) confirms the schema implements each (schema-level fidelity);
  (3) measures the empirical fill rate of each recommendation across the 26 generated
      ST data cards (card-level fidelity).
Outputs: st_mapping.csv + a markdown table printed to console.
"""
from __future__ import annotations

import csv
import json
from pathlib import Path

from schema_utils import load_schema

HERE = Path(__file__).parent
CARDS = HERE / "datacards"
SCHEMA = load_schema()

# 18 Documentation recommendations (items 1.1a–1.4c) → schema field(s).
# primary = field used for the card-level fill-rate metric.
ST_DOC = [
    ("1.1a", "Dataset summary", "①", ["metadata.summary"], "metadata.summary"),
    ("1.1b", "Dataset identity and access", "①",
     ["metadata.persistent_identifier", "metadata.access_method", "metadata.version", "metadata.custodian"],
     "metadata.access_method"),
    ("1.1c", "Reasons for creation & purpose(s)", "①",
     ["metadata.purpose", "metadata.creators", "metadata.funders", "metadata.avoided_uses"],
     "metadata.purpose"),
    ("1.1d", "Data origin", "①", ["data_origin.origin_type", "data_origin.selection_rationale"],
     "data_origin.origin_type"),
    ("1.1e", "Data sampling & aggregation from multiple sources", "①",
     ["data_origin.sampling_strategy", "data_origin.aggregation_multisource"], "data_origin.sampling_strategy"),
    ("1.1f", "Data shifts over time", "①", ["data_origin.data_shifts_overtime"], "data_origin.data_shifts_overtime"),
    ("1.2a", "Composition of groups within dataset", "②",
     ["population.target_population", "population.age_reported", "population.sex",
      "population.ethnicity_reported", "population.missing_groups"], "population.target_population"),
    ("1.2b", "Attributes of individuals (recording method)", "②", ["population.attribute_recording"],
     "population.attribute_recording"),
    ("1.2c", "Attributes of individuals (subgroups & disparate outcomes)", "②",
     ["population.subgroups_disparate_outcomes"], "population.subgroups_disparate_outcomes"),
    ("1.3a", "Declared limitations / sources of bias", "③", ["bias_and_limitations.known_limitations"],
     "bias_and_limitations.known_limitations"),
    ("1.3b", "Modifications & synthetic data", "③", ["bias_and_limitations.modifications"],
     "bias_and_limitations.modifications"),
    ("1.3c", "Sampling bias", "③", ["bias_and_limitations.bias_sources"], "bias_and_limitations.bias_sources"),
    ("1.3d", "Aggregation bias", "③", ["bias_and_limitations.bias_sources", "data_origin.aggregation_multisource"],
     "bias_and_limitations.bias_sources"),
    ("1.3e", "Missing data", "③", ["bias_and_limitations.missing_data"], "bias_and_limitations.missing_data"),
    ("1.3f", "Label noise / provenance", "③", ["annotation.known_label_noise", "annotation.labeling_provenance"],
     "annotation.known_label_noise"),
    ("1.4a", "Ethics & governance", "④",
     ["ethics.consent", "ethics.irb_approval", "ethics.license", "ethics.legal_compliance",
      "ethics.data_protection_impact_assessment"], "ethics.consent"),
    ("1.4b", "Patient & public participation (PPIE)", "④", ["ethics.public_participation"],
     "ethics.public_participation"),
    ("1.4c", "Bias & impact assessments", "④",
     ["ethics.bias_impact_assessment", "bias_and_limitations.representativeness_concerns"],
     "ethics.bias_impact_assessment"),
]


def schema_has(path: str) -> bool:
    node = SCHEMA.get("properties", {})
    for p in path.split("."):
        if isinstance(node, dict) and p in node:
            node = node[p]
            props = node.get("properties") if isinstance(node, dict) else None
            node = props if props is not None else node
        else:
            return False
    return True


def get_path(card: dict, path: str):
    cur = card
    for p in path.split("."):
        if isinstance(cur, dict) and p in cur:
            cur = cur[p]
        else:
            return None
    return cur


def present(card: dict, path: str) -> bool:
    """A recommendation is 'addressed' if the mapped field exists in the card
    (booleans True/False both count as addressed — the dataset made a statement)."""
    v = get_path(card, path)
    return v is not None


def main():
    cards = []
    for f in sorted(CARDS.glob("*.json")):
        try:
            cards.append(json.loads(f.read_text(encoding="utf-8")))
        except Exception:
            pass
    n = len(cards)
    rows = []
    implemented = 0
    fill_rates = []
    for rid, title, pillar, fields, primary in ST_DOC:
        ok_schema = schema_has(primary)
        if ok_schema:
            implemented += 1
        filled = sum(1 for c in cards if present(c, primary))
        rate = round(100.0 * filled / n, 1) if n else 0.0
        fill_rates.append(rate)
        rows.append({
            "rec_id": rid, "pillar": pillar, "recommendation": title,
            "schema_field": primary, "schema_implemented": "Y" if ok_schema else "N",
            "cards_filled": filled, "n_cards": n, "fill_rate_pct": rate,
            "all_mapped_fields": "; ".join(fields),
        })
    out = HERE / "st_mapping.csv"
    with open(out, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader(); w.writerows(rows)

    mean_fill = round(sum(fill_rates) / len(fill_rates), 1) if fill_rates else 0.0
    print(f"Cards analysed: {n}")
    print(f"Schema implements {implemented}/{len(ST_DOC)} Documentation recommendations at field level.")
    print(f"Mean card-level fill rate across 18 Documentation recommendations: {mean_fill}%")
    print(f"Mapping table → {out}\n")
    print(f"{'ID':5s} {'P':2s} {'schema':6s} {'fill%':6s}  recommendation")
    for r in rows:
        print(f"{r['rec_id']:5s} {r['pillar']:2s} {r['schema_implemented']:6s} {r['fill_rate_pct']:6.1f}  {r['recommendation']}")


if __name__ == "__main__":
    main()
