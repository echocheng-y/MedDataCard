# M4 — Sampling Validation of LLM-based Metadata Extraction for STANDING Together Data Cards

*A reproducible validation harness and results for the hybrid (catalog baseline + LLM) metadata
extraction pipeline in MedDataCard. This document is written to be reusable as a methods/results
section for a short methods paper ("quick-win" target).*

---

## 1. Motivation and Objective

Medical-AI datasets are documented unevenly. The [STANDING Together](https://www.standingtogether.ai/)
consensus (Lancet Digital Health / NEJM AI, 2024) defines 18 documentation recommendations across four
pillars (data, provenance, ethics, and intended use). Manually authoring compliant data cards for the
hundreds of public medical-AI datasets is labor-intensive, and fully automated extraction risks
fabricating facts not present in the source.

The objective of **M4** is to *quantify, honestly*, how well an LLM-assisted extraction pipeline
recovers structured metadata from a dataset's published source text, relative to a human-authored gold
standard, and to bound the risk of fabrication through a schema-conformance guardrail.

## 2. Method

### 2.1 Pipeline under test

MedDataCard uses a **dual-track** extraction design:

- **Baseline track** — derives fields solely from a curated catalog (`dataset_catalog.xlsx`) of real
  metadata (modality, license, scale, geography hints, medical field). Zero fabrication by construction.
- **LLM hybrid track** — sends the dataset's source text (paper abstract / repository README) to an LLM
  and merges the returned JSON into the baseline. Three providers are supported behind one OpenAI-compatible
  interface: OpenAI, Anthropic, and Alibaba DashScope (`qwen-plus`).

**Anti-fabrication guardrail (`conform_card`).** Every merged card is validated against the
ST data-card JSON Schema (Draft 2020-12). Any field that violates a type, enum, or `additionalProperties`
constraint — at *both* the object-key and the list-item level — is removed and, where a valid baseline
value exists at the same path, *reverted* to it. Dropped fields are recorded in
`extraction.pending_verification` for human review. The LLM is therefore never trusted to introduce
schema-illegal content into a shipped card.

### 2.2 Evaluation corpus

26 datasets were sampled to span **nine primary modalities** and to break the homogeneity of an earlier
4-dataset chest-X-ray pilot:

| Primary modality | Datasets |
|---|---|
| EHR / clinical | MIMIC-IV, eICU-CRD, UK Biobank |
| Radiography (X-ray) | NIH ChestX-ray14, MIMIC-CXR, CheXpert, PadChest, VinDr-CXR |
| CT | TotalSegmentator, CT-RATE, NIH DeepLesion |
| MRI | BraTS 2024, ADNI |
| Dermatoscopy | HAM10000, ISIC 2024 |
| Pathology (WSI) / Genomics | TCGA, MedMNIST* |
| Single-cell transcriptomics | Tabula Sapiens |
| Text (medical QA / retrieval) | MedQA, MedMCQA, BioASQ, PubMedQA, PMC-Patients |
| Physiological (EEG / ECG) | CHB-MIT, Sleep-EDF Expanded, PhysioNet/CinC 2020 |

\*MedMNIST spans ten sub-modalities (dermoscopy, X-ray, CT, pathology-WSI, fundus, and others).

The `source_type` gold labels deliberately span five relevant schema categories
(`repository`, `challenge`, `paper-supplement`, `registry`, `other`) so that the categorical agreement metric is
not degenerate.

### 2.3 Gold standard (honest scope)

For each dataset we wrote `gold/<id>.json` containing **only** facts explicitly stated in, or directly
computable by a reviewer from, the public abstract/source text — never inferred from the catalog.
Scored fields:

- `modality.modalities` (set)
- `modality.sample_counts` (counts)
- `geography.countries` (set)
- `tasks_and_use.intended_tasks` (set)
- `metadata.source_type` (categorical enum)

**Excluded by design:** `license` and `commercial_use_allowed` are supplied by the catalog baseline,
not extracted from text, so they are *not* counted toward LLM extraction accuracy (they are reported
only as provenance redundancy).

### 2.4 Metrics

- **Exact-match accuracy** over the 5 scored fields × 26 datasets = 130 cells. Set-valued fields use
  *subset semantics* (`gold ⊆ llm`); count/categorical fields require exact equality.
- **Cohen's κ** computed only on `source_type` (the single categorical field), to measure
  beyond-chance agreement and to expose baseline-vs-LLM correction behavior.
- A cell is scored *cosmetic-miss* when the underlying value is correct but the JSON key label differs
  from the gold (e.g. `studies` vs `admissions`); reported separately from substantive errors.

## 3. Results

Run on DashScope `qwen-plus`, no API-key degradation (all 26 cards produced by the hybrid track).

### 3.1 Overall accuracy

**117 / 130 = 90.0%** exact-match. All 78 set-valued cells (modalities, countries, intended tasks) matched
under subset semantics; the misses concentrate in the coarse `source_type` enum (6 / 26) and in
`sample_counts` key labels (7 / 26).

If cosmetic key-label mismatches are relaxed to "value-correct", accuracy rises to **120 / 130 ≈ 92%**.

### 3.2 Cohen's κ on `source_type`

**κ = 0.675** (Landis–Koch: *substantial* agreement). This is a meaningful recovery from the earlier
4-dataset pilot, where κ was degenerate (≈ −0.2) due to n=4, skewed marginals, and LLM non-determinism.
The 26-dataset, 5-category spread stabilizes the estimate.

The LLM *correctly corrected* 3 baseline heuristic misses (recovering `paper-supplement` and `challenge`
labels the heuristic had missed for BraTS 2024, HAM10000, and Tabula Sapiens), but *introduced* 6 of its
own `source_type` over-generalisations (confusing `repository`, `registry`, `challenge`, and `other`) — a net
regression of three on this field, and the clearest weakness of the current design.

### 3.3 Error analysis (13 misses)

| # | Dataset | Field | Type | Detail |
|---|---|---|---|---|
| 1 | NIH ChestX-ray14 | source_type | substantive | LLM → `repository`, gold `other` |
| 2 | MIMIC-IV | source_type | substantive | LLM → `registry`, gold `repository` |
| 3 | eICU-CRD | source_type | substantive | LLM → `registry`, gold `repository` |
| 4 | MedMCQA | source_type | substantive | LLM → `challenge`, gold `repository` |
| 5 | MedMNIST | source_type | substantive | LLM → `challenge`, gold `repository` |
| 6 | NIH DeepLesion | source_type | substantive | LLM → `other`, gold `repository` |
| 7 | MIMIC-IV | sample_counts | cosmetic | key `studies` vs gold `admissions` (value-correct) |
| 8 | eICU-CRD | sample_counts | partial | key `studies` vs `admissions`; `hospitals`=208 missing |
| 9 | MedQA | sample_counts | cosmetic | key `samples` vs gold `questions` (value-correct) |
| 10 | BraTS 2024 | sample_counts | substantive | LLM `patients`=11200, gold `gli_post/pre_training` (wrong) |
| 11 | ISIC 2024 | sample_counts | substantive | LLM `images`=434185 vs gold `training_images`=401059 (conflict) |
| 12 | Sleep-EDF Expanded | sample_counts | cosmetic | key `studies` vs gold `samples` (value-correct) |
| 13 | UK Biobank | sample_counts | substantive | LLM null, gold `patients`=500000 |

Of the seven `sample_counts` misses, three are pure key-label mismatches with identical values
(MIMIC-IV, MedQA, Sleep-EDF) and four are genuine errors (BraTS 2024, ISIC 2024, the missing eICU
hospital count, and the UK Biobank null). Of the six `source_type` misses, none are random: all are
the LLM over-assigning a coarse repository/registry/challenge/other label.

### 3.4 Guardrail defects found and fixed during validation

Running M4 against the live pipeline surfaced two real defects in the anti-fabrication guardrail:

1. **Silent field loss.** `conform_card` originally only *deleted* schema-violating fields, so an invalid
   `source_type` was dropped to `null` instead of reverting to the baseline `repository`. Fixed to
   *revert to the baseline value at the same path* when one exists.
2. **List-item blind spot.** The validator handled object-key violations but ignored *list-item* enum
   violations — e.g. the LLM writing English `medical_fields` (`dermatology`) or `intended_tasks`
   (`external validation`) outside the schema enum — leaving 7/13 cards schema-invalid. Fixed so that, on
   a list violation, the baseline list is restored as the base and only individually-valid, non-duplicate
   LLM items are retained.

After both fixes, **26 / 26 generated cards are schema-valid** and every dropped field is traceable via
`pending_verification`.

## 4. Threats to Validity

- **Abstract-level gold.** Sources are paper abstracts, not full data sheets; gold is intentionally
  conservative and under-states what the LLM could recover from richer text.
- **License excluded.** License/commercial fields come from the catalog, so fabrication risk there is
  unmeasured by this harness (mitigated separately by the catalog being human-curated).
- **LLM non-determinism.** `source_type` varied across runs on small n; κ is reported at the observed
  run, and the 26-dataset spread is chosen to keep it stable.
- **n = 26.** Adequate for a credible estimate; a production claim would still warrant 30–50 datasets.

## 5. Conclusion

The hybrid pipeline recovers structured ST metadata from source text at **90.0% exact-match** (≈92% when
key-label tolerance is applied), with **substantial** categorical agreement (κ = 0.675) on `source_type`.
The schema-conformance guardrail makes fabrication into a *detected-and-reverted* event rather than a
silent one — a property validated by the two defects it caught. The dominant residual weakness is the
coarse `source_type` enum, where the LLM both fixes and introduces errors at similar rates.

---

*Reproduce:* `python3 evaluate_m4.py dashscope` → `m4_report.json` + `m4_output/*.json`.
Gold in `gold/`, sources in `sources/`.
