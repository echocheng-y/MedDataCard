# IAA Protocol — Second-Coder Inter-Annotator Agreement for the MedDataCard Gold Standard

*Status: protocol, encoding guide, and computation script are READY. All IAA numbers are
**PENDING** until a real second human coder (Coder B) completes `coder_b/`. Nothing here is
fabricated; this document is written to be dropped into the manuscript's Methods / Limitations.*

---

## 1. Research question and motivation

The MedDataCard M4 validation measures **LLM-vs-gold** agreement: how well the hybrid
extraction pipeline recovers structured metadata from source text relative to a human gold
standard (`gold/<id>.json`). M4 answers *"does the pipeline match the gold?"*.

It does **not** answer a different, complementary question: *"is the gold standard itself
reliable?"* The current gold standard was authored by a **single coder (Coder A)**. A single
coder's labels can contain systematic interpretation bias even when the extraction target is
well-defined. To make a defensible reliability claim at submission time, we add a **second
independent coder (Coder B)** who re-encodes the same 26 datasets from the same source texts,
and we quantify human-human agreement with **Cohen's κ** (and field-appropriate companions).

> IAA is therefore the *reliability of the gold*, a distinct construct from M4's
> *LLM fidelity to the gold*. The two are reported separately and never conflated. M4's
> published numbers (90.0% exact-match; source-type κ = 0.675) are **LLM-vs-gold** and are
> untouched by this protocol.

---

## 2. Sampling plan — full double-coding (no sampling)

We double-code **all 26 datasets × 5 scored fields = 130 cells** rather than drawing a sample.

**Rationale.** The corpus is small (n = 26 datasets). A random subset would only shrink an
already small base and widen every confidence interval for no material saving. Full
double-coding gives the most stable κ estimates and lets us report per-field agreement without
aggregation assumptions.

**Degradation path (if time-constrained).** If a full second pass is not feasible before
submission, we fall back to a **random subset** of datasets, but then we **explicitly report
the coverage ratio** (datasets double-coded / 26) and flag any field-level κ computed on
fewer than 20 datasets as *exploratory*. The bootstrap CI already surfaces instability; we
add the coverage statement so reviewers can judge generalizability. The default and
recommended path remains full 130-cell double-coding.

The 5 scored fields (dotted paths) are fixed and identical to `evaluate_m4.SCORED_FIELDS`:

| Field | Type | Role in IAA |
|---|---|---|
| `modality.modalities` | set | binary-expansion κ + mean Jaccard |
| `modality.sample_counts` | counts dict | per-key exact-match rate |
| `geography.countries` | set | binary-expansion κ + mean Jaccard |
| `tasks_and_use.intended_tasks` | set | binary-expansion κ + mean Jaccard |
| `metadata.source_type` | categorical (5) | Cohen's κ |

---

## 3. Double-blind procedure

1. **Coder A** = the existing `gold/<id>.json` author. Their labels are frozen and treated as
   one of the two human annotations.
2. **Coder B** = a second annotator, independent of Coder A, with no access to Coder A's labels.
3. Both coders work **only** from `sources/<id>.txt` (the same abstract/README excerpts used to
   build the gold). Neither sees the other's output, and Coder B does **not** see Coder A's gold
   while coding.
4. Coder B records annotations either in `coder_b_template/coder_b_blank.csv` (one row per
   cell) or by filling the per-dataset blank JSONs in `coder_b_template/` and copying the
   completed files into `coder_b/`.
5. Only after both sets exist does `compute_iaa.py` compare them. The script reads
   `gold/<id>.json` (Coder A) and `coder_b/<id>.json` (Coder B) and never modifies either.

---

## 4. Encoding guide (Coder B decision rules)

Coder B must follow the **same conservative principle** used to build the gold: *include only
facts explicitly stated in, or directly computable by a reviewer from, the source text; never
infer from the catalogue.* Below are the operational rules per field.

### 4.1 `modality.modalities` (set)
- List **atomic** modalities explicitly stated or directly derivable (e.g. `X-ray`, `MRI`,
  `CT`, `EHR`, `text`, `genomic`, `pathology-WSI`, `dermoscopy`, `single-cell`, `fundus`).
- **Normalize**: lowercase; strip plurals/casing variants (`X-Rays` → `X-ray`). Merge obvious
  synonyms to the gold vocabulary (e.g. `chest X-ray` → `X-ray`). Do not split a compound
  phrase into invented atoms, and do not merge distinct atoms.
- Leave `[]` only if the source states no modality.

### 4.2 `modality.sample_counts` (counts dict)
- Keys **MUST match the gold key names exactly** (canonical keys observed: `images`,
  `patients`, `admissions`, `icu_stays`, `questions`, `cells`, `training_images`,
  `gli_post_training`, `gli_pre_training`, `studies`, `samples`, `hospitals`). If the source
  uses a synonymous phrase, map it to the canonical key; if no canonical key fits and the
  count is clearly stated, use the gold's literal key rather than inventing one.
- Report only counts explicitly stated or directly computable; omit a key if not stated.
- Never estimate or round. A missing count ≠ 0; it is "not stated".

### 4.3 `geography.countries` (set)
- List countries **explicitly named** for data collection or subject source (e.g.
  `United States`, `United Kingdom`).
- Leave `[]` if no country is named. **Do not** infer a country from an institution's
  headquarters unless the source text states the subject/collection geography.

### 4.4 `tasks_and_use.intended_tasks` (set)
- List intended tasks explicitly stated (observed vocabulary: `classification`,
  `segmentation`, `qa`, `retrieval`, `causal`, `localization`). Use the gold vocabulary;
  do not invent tasks not supported by the text.

### 4.5 `metadata.source_type` (categorical, exactly one of 5)
Choose the **single best** label for how the dataset is distributed/published:

| Category | Use when the source indicates… |
|---|---|
| `repository` | A maintained data repository / database released for reuse (e.g. PhysioNet, MIMIC, UK Biobank, TCGA dbGaP). |
| `challenge` | Released primarily as a competition/benchmark with a leaderboard (e.g. ISIC, BraTS, BioASQ). |
| `paper-supplement` | Distributed as supplementary material of a specific publication, not a standing repository (e.g. Tabula Sapiens, PubMedQA). |
| `registry` | A curated disease/cohort registry aggregating multiple sites (e.g. TCGA as a registry-style aggregation, UK Biobank-style registries). |
| `other` | None of the above fits (e.g. a one-off NIH Box release with no repository framing, as in NIH ChestX-ray14). |

> **Note on the schema enum.** `st_datacard.schema.json` lists a 6th enum value,
> `commercial`. It is **unused** across all 26 gold files (the observed distribution is
> repository 14 / challenge 4 / paper-supplement 4 / registry 3 / other 1). IAA is therefore
> computed on the 5 categories that actually occur; if Coder B believes `commercial` applies
> to a future dataset, it should be escalated to the authors rather than silently introduced,
> because it would change the category space and the κ base.

---

## 5. Metric design (rigorous, reviewer-ready)

We deliberately use **field-appropriate** agreement statistics and report them **separately**
rather than collapsing into one number.

### 5.1 `metadata.source_type` → Cohen's κ (5 categories)
- 26 paired categorical labels (Coder A vs Coder B).
- Cohen's κ corrects for chance agreement given the marginal distribution.
- Reported with a 95% bootstrap CI (see §5.4).

### 5.2 Three set fields → binary expansion κ + mean Jaccard
For each set field we do **not** force a single κ on variable-length sets. Instead:
- Collect the **union of atomic values** across both coders and all 26 datasets.
- For each atomic value, form a **binary present/absent decision** per coder
  (1 = value present, 0 = absent). This yields a flat binary label pair per atomic value.
- Compute **Cohen's κ** on these binary labels — a symmetric, chance-corrected measure of
  whether the two coders agree on *which atomic values belong*.
- Additionally report the **mean Jaccard** over the 26 datasets
  (`|A∩B| / |A∪B|`) as an intuitive overlap index (not chance-corrected, so reported
  alongside κ, not instead of it).

### 5.3 `modality.sample_counts` → per-key exact-match (no κ forced)
- A count dict is not naturally a single categorical or set decision; forcing κ would be
  misleading. Instead we compute **exact-match** per key: a (dataset, key) cell agrees iff
  both coders state the key with the **same value**.
- Report **per-key agreement rate** and an **overall agreement rate** over all
  (dataset, key) cells, each with a 95% bootstrap CI.
- This is the same exact-equality semantics M4 uses for `sample_counts`, keeping the two
  validations comparable in spirit.

### 5.4 Confidence intervals — bootstrap
- **κ metrics** (source_type, three set fields): 2000 bootstrap resamples **over the 26
  datasets** (with replacement); recompute κ on each resample; report the 2.5% and 97.5%
  percentiles as the 95% CI.
- **sample_counts** overall rate: 2000 bootstrap resamples **over the (dataset, key) cells**.
- Fixed random seed (20260819) for reproducibility.

### 5.5 Overall IAA reporting
- We report each field's statistic **on its own terms** (κ for categorical/set fields,
  agreement rate for counts) plus its CI. We do **not** merge them into a single composite
  number that would hide field differences.
- A short narrative conclusion summarizes the pattern (e.g. "set fields near-perfect,
  source_type moderate, sample_counts key-label sensitive") once real numbers exist.
- Until then, the manuscript states the design and marks every IAA value **PENDING**.

---

## 6. How to run

### 6.1 Generate the Coder-B template
```bash
python generate_coder_b_template.py
```
Produces `coder_b_template/coder_b_blank.csv` (26×5 = 130 rows) and one blank
`coder_b_template/<name>.json` per dataset. The CSV columns are
`dataset_id, field_path, field_type, definition, source_ref, coder_b_value`
(`coder_b_value` is empty for the human to fill).

### 6.2 Coder B fills the template
Coder B reads `source_ref` (the abstract/README excerpt), applies §4, and writes their value
into `coder_b_value` (CSV) — or fills the JSON `comparable` blocks and saves them under
`coder_b/<name>.json` (same filename as the matching `gold/<name>.json`).

### 6.3 Compute IAA
```bash
python compute_iaa.py            # real mode: gold/ vs coder_b/
python compute_iaa.py --selftest # math sanity check only (NOT real IAA)
```
- **Real mode** writes `iaa_report.json` with per-field κ / agreement, bootstrap CIs, and an
  explicit `PENDING` overall-conclusion placeholder. If `coder_b/` is missing or incomplete,
  the script exits gracefully with instructions and **fabricates no numbers**.
- **`--selftest`** runs gold-vs-gold and asserts κ = 1.0 / Jaccard = 1.0 /
  sample_counts = 100%, proving the math is correct. The report is labeled
  `selftest: gold-vs-gold sanity check (not real IAA)` and must never be cited as real IAA.

### 6.4 Reproducibility notes
- Standard library only (`json`, `csv`, `random`, `math`, `pathlib`, `argparse`); no numpy.
- `cohen_kappa`, `get_path`, and the scored-field definitions reuse the exact semantics from
  `evaluate_m4.py`, so IAA and M4 agree on what "a field" and "a match" mean.
- Python: managed `C:/Users/13757/.workbuddy/binaries/python/versions/3.13.12/python.exe`.

---

## 7. Integrity statement

No second human coder currently exists; their labels cannot be supplied by automation. This
protocol, the template, and `compute_iaa.py` are built so that **the moment a real Coder B
finishes `coder_b/`, the true IAA is one command away**. Until then, every IAA figure in the
manuscript is marked **PENDING** and no κ, Jaccard, or agreement rate is asserted.
