"""Anti-fabrication guardrail quantification.

Aggregates, across the 26 generated ST data cards, the behaviour of the
schema-conformance guardrail (`conform_card`):
  - how many cards are hybrid (LLM-assisted) vs baseline;
  - total pending_verification items;
  - guardrail *captures*: LLM fields auto-dropped for violating the schema
    (the "detected-and-reverted fabrication attempt" events);
  - heuristic geography-inference pending (baseline, not a capture);
  - per-field dropped tally.

Outputs: fabrication_audit.csv + console summary.
"""
from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path

HERE = Path(__file__).parent
CARDS = HERE / "datacards"


def main():
    cards = [json.loads(f.read_text(encoding="utf-8")) for f in sorted(CARDS.glob("*.json"))]
    n = len(cards)
    n_hybrid = sum(1 for c in cards if c.get("extraction", {}).get("method") == "hybrid")
    n_baseline = n - n_hybrid

    total_pending = 0
    captures = 0          # auto-dropped (schema-violating LLM fields reverted)
    geo_heuristic = 0     # baseline heuristic geography inference
    other_pending = 0
    dropped_fields = Counter()

    for c in cards:
        pend = c.get("extraction", {}).get("pending_verification", []) or []
        total_pending += len(pend)
        for p in pend:
            if "auto-dropped" in p or "violating schema" in p:
                captures += 1
                # extract field names listed after the colon
                m = re.search(r"pending manual review:\s*(.+)$", p)
                if m:
                    for fld in m.group(1).split(","):
                        dropped_fields[fld.strip()] += 1
            elif "heuristically inferred" in p:
                geo_heuristic += 1
            else:
                other_pending += 1

    rows = [{
        "metric": "n_cards", "value": n},
        {"metric": "n_hybrid", "value": n_hybrid},
        {"metric": "n_baseline", "value": n_baseline},
        {"metric": "total_pending_items", "value": total_pending},
        {"metric": "guardrail_captures_auto_dropped", "value": captures},
        {"metric": "geo_heuristic_pending", "value": geo_heuristic},
        {"metric": "other_pending", "value": other_pending},
        {"metric": "capture_rate_per_hybrid_card", "value": round(captures / n_hybrid, 3) if n_hybrid else 0.0},
        {"metric": "pending_per_card", "value": round(total_pending / n, 3) if n else 0.0},
    ]
    for fld, cnt in dropped_fields.most_common():
        rows.append({"metric": f"dropped_field:{fld}", "value": cnt})
    out = HERE / "fabrication_audit.csv"
    import csv
    with open(out, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["metric", "value"]); w.writeheader(); w.writerows(rows)

    print(f"Cards: {n} (hybrid={n_hybrid}, baseline={n_baseline})")
    print(f"Total pending_verification items: {total_pending}")
    print(f"  Guardrail captures (LLM fields auto-dropped, reverted): {captures}")
    print(f"  Heuristic geography-inference pending (baseline):       {geo_heuristic}")
    print(f"  Other pending:                                           {other_pending}")
    print(f"Capture rate per hybrid card: {captures / n_hybrid:.3f}" if n_hybrid else "n/a")
    if dropped_fields:
        print("Dropped fields (by frequency):")
        for fld, cnt in dropped_fields.most_common():
            print(f"    {fld}: {cnt}")
    print(f"→ {out}")


if __name__ == "__main__":
    main()
