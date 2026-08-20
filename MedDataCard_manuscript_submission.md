*Author note (not for submission): target journals are npj Digital Medicine, Lancet Digital Health, or Scientific Data. A structured-abstract variant can be produced for Scientific Data. Every number traces to m4_report.json, audit_experiments.csv, st_mapping.csv, or fabrication_audit.csv.*

# MedDataCard: an automated framework for generating STANDING Together-compliant medical-AI data cards and auditing representation gaps

## Abstract

Algorithmic bias in medical artificial intelligence propagates through training and evaluation data and amplifies health inequities. In 2024, the STANDING Together (ST) consensus established the first unified reporting standard for dataset diversity, inclusivity, and generalizability, but no machine-readable implementation exists and automated metadata extraction risks fabrication. Here we present MedDataCard, a framework that translates the 18 ST documentation recommendations into a constrained JSON schema (38 fields, 6 required) and generates compliant data cards through a dual-track pipeline. A baseline track uses only a curated catalogue (zero fabrication); a hybrid track adds large-language-model completion gated by a schema guardrail. Across 26 flagship datasets and 130 scored cells, the hybrid pipeline reached 90.0% exact-match accuracy (117/130) against a human gold standard, with source-type Cohen's kappa of 0.675. Per-dataset ST pillar completeness was 63.2%, 54.7%, 79.3%, and 59.6%, and the composite compliance index was 64.2. The five-indicator diversity score (0.485) exposed a core representation gap: geographic representativeness (0.21) and skin-tone reporting (0.12) were markedly lower than annotation provenance (0.77) and generalizability statements (0.85). The guardrail intercepted 14 out-of-schema fields with no fabricated content escaping. MedDataCard operationalizes the ST consensus as computable, auditable data cards and provides a reproducible foundation metric for fairness assessment.

## Introduction

Algorithmic bias in medical AI depends heavily on the training and evaluation data. Bias encoded at the data level propagates through models and amplifies health inequities. On 18 December 2024, the STANDING Together international consensus was published simultaneously in *The Lancet Digital Health* and *NEJM AI* [1]. The consensus convened more than 350 representatives from 58 countries and used a Delphi process (194 participants, three rounds of electronic voting plus one in-person meeting) to produce 29 recommendations. These recommendations provided the first unified reporting standard for dataset diversity, inclusivity, and generalizability.

After the consensus, dataset disclosure shifted from soft recommendation to hard constraint. Regulators have authorized hundreds of AI-enabled medical devices, yet most do not disclose training data or architecture. Three gaps remain. First, flagship templates such as Model Cards [3] and Datasheets for Datasets [4] provide conceptual frameworks but lack a machine-readable, ST-aligned implementation. Second, manual data-card authoring is costly and uneven, making systematic audits of many datasets impractical. Third, automated metadata extraction with large language models can fabricate facts absent from source text, threatening the compliance bottom line that disclosure must be truthful.

These gaps remained open at the time of this study (August 2026). No automated tool maps the 18 ST documentation recommendations to machine-verifiable data cards, and no pipeline audits public medical-AI datasets at the metadata level without a data-use agreement. MedDataCard addresses this gap.

We posed one central question (RQ0): can ST-compliant data cards be generated automatically, and can existing medical-AI datasets be audited systematically and reproducibly for diversity, inclusivity, and generalizability? Four sub-questions follow. RQ1 asks whether an LLM-assisted pipeline extracts structured metadata from public abstracts or repository READMEs at publishable accuracy under a zero-fabrication constraint. RQ2 asks whether the schema fully covers the 18 documentation recommendations and quantifies the actual disclosure completeness and compliance index of 26 flagship datasets across the four ST pillars. RQ3 asks the extent to which the guardrail intercepts out-of-scope or fabricated LLM output. RQ4 asks whether the compliance index and diversity score are robust to weight choice.

MedDataCard delivers four artifacts: a machine-readable ST data-card schema; an LLM-assisted, human-reviewed dual-track extraction pipeline with zero GPU dependency; computable inclusivity and generalizability scores with a leaderboard; and an open-source web generator and audit dashboard (Streamlit, three tabs). The audit covers all 26 surveyed datasets at the metadata level only, needs no raw data, and therefore requires no data-use agreement.

**Contributions.** First, we provide an executable ST data-card schema (38 fields, 6 required, strongly constrained). Second, we provide an empirically validated zero-fabrication dual-track pipeline. Third, we provide a reproducible compliance and diversity leaderboard over 26 datasets, a foundation metric for downstream fairness auditing. Fourth, we release an open-source web tool and audit dashboard.

## Related work

### The lineage of data documentation standards

Model Cards [3] introduced the model-report-card paradigm, advocating transparent disclosure of model use, bias, and ethics. Datasheets for Datasets [4] argued that data deserve a datasheet and exposed provenance, collection, ethics, and limitations through a questionnaire. STANDING Together [1] is the standard ontology this work aligns to. It consolidates documentation requirements into 18 cardable recommendations and adds 11 use-governance recommendations.

### Automated dataset metadata extraction

ChatPD [2] uses LLMs to extract dataset information from papers and builds a paper-dataset network, reaching roughly 90% precision and recall on entity resolution. MedDataCard borrows its dataset-information-template idea but differs in three ways. It uses the ST consensus as a hard constraint ontology rather than a generic template. It introduces a schema guardrail for anti-fabrication rather than extraction alone. It targets compliance auditing of medical datasets rather than paper-dataset link discovery. HuggingFace Datasets [5] and Google Dataset Search [6] represent community-level dataset cards and general dataset discovery, respectively, but neither builds in ST compliance checking.

### Audited foundation-model exemplars

A cluster of medical foundation models released in 2024 show narrow training domains and under-reported population representation, exactly the gaps an ST audit exposes. MedSAM [7] is a general medical image segmentation model with 1,570,263 image-mask pairs across 10 modalities, but with uneven modality distribution (CT/MRI dominated). UNI [8], CONCH [9], Prov-GigaPath [10], and Virchow [11] are computational-pathology foundation models with limited reported demographic scope. MONET [12] is included as a complementary exemplar of a concept-level auditable imaging-text model.

## Methods

### Terminology

We use the following terms consistently. STANDING Together (ST) denotes the 2024 consensus (29 recommendations: 18 documentation recommendations numbered 1.1a-1.4c, cardable; plus 11 use recommendations at the governance level, not directly cardable). The four ST pillars are dataset description and access; population composition and geography; bias, limitations, and annotation; and ethics and governance. A data card is a machine-readable JSON object conforming to `st_datacard.schema.json` (JSON Schema Draft 2020-12, v0.2). A baseline card uses only real metadata from the curated catalogue `dataset_catalog.xlsx`, with zero LLM use and zero fabrication by construction. A hybrid card layers LLM-completed fields onto the baseline and is then validated by the schema guardrail. The guardrail (`conform_card`) performs schema-consistency checks on every merged card; any LLM field violating type, enum, or `additionalProperties` constraints is deleted or rolled back to a valid baseline value. A capture is an LLM field deleted or rolled back by the guardrail, that is, one intercepted out-of-scope output.

### Standard operationalization

We translated the 18 ST documentation recommendations (1.1a-1.4c, spanning the four pillars) into a machine-readable JSON schema. The schema defines 38 leaf fields grouped by the four pillars, of which 6 are required, and enforces `additionalProperties: false` at every node, structurally preventing undeclared fields from entering a data card. The 11 use recommendations are governance-level and not directly cardable; by design they fall outside the schema scope but are referenced.

### Dual-track extraction pipeline

The baseline track takes fields only from the curated catalogue (`dataset_catalog.xlsx`, containing modality, license, scale, geographic cues, and medical field), guaranteeing zero fabrication by construction. The hybrid track sends each dataset's source text (paper abstract or repository README) through a single OpenAI-compatible interface (OpenAI, Anthropic, or Alibaba Bailian `qwen-plus`) to the LLM, merges the returned partial card with the baseline, and keeps only non-empty baseline or LLM values.

### Anti-fabrication guardrail

Every merged card is schema-validated. Any field violating type, enum, or additional-property constraints at the object-key or list-item level is deleted; if a valid baseline value exists at the same path, the field rolls back to it. Deleted fields are recorded in `extraction.pending_verification` for human review, so the LLM can never write schema-illegal content into a published card.

### Evaluation corpus and gold standard

We sampled 26 flagship medical-AI datasets spanning nine major modalities: radiology, pathology, genomics, physiological time series, clinical text, and question answering. The set includes NIH ChestX-ray14, MIMIC-CXR, CheXpert, PadChest, VinDr-CXR, BraTS 2024, ISIC 2024, HAM10000, MedMNIST, TotalSegmentator, CT-RATE, DeepLesion, UK Biobank, TCGA, ADNI, Tabula Sapiens, MIMIC-IV, eICU-CRD, Sleep-EDF, CHB-MIT, PhysioNet/CinC 2020, PMC-Patients, MedQA, MedMCQA, PubMedQA, and BioASQ. The gold standard records only facts explicitly stated in or directly computable from public abstracts or READMEs, and never infers from the catalogue. Scored fields are modality, sample counts, countries, intended tasks, and source type; license and commercial-use fields come from the catalogue and are excluded from extraction accuracy.

### Metrics

Extraction fidelity is exact-match accuracy over scored fields; set fields use `gold ⊆ llm` subset semantics and counts or categorical source types use exact equality. We report Cohen's kappa for source type to expose baseline versus LLM correction behavior. Standard fidelity is the field-level implementation rate of the schema against each documentation recommendation and the empirical fill rate over 26 cards. Compliance and diversity use per-pillar completeness plus a composite ST compliance index, and a five-indicator dataset diversity score (geographic representativeness, population-subgroup reporting, skin-tone/Fitzpatrick reporting, annotation provenance, generalizability statement). Weight sensitivity draws 200 Dirichlet weight vectors and computes the Spearman rank correlation between alternative-weight and equal-weight rankings.

### Planned second-coder inter-annotator agreement (IAA)

M4 measures LLM-versus-gold fidelity; it does not by itself establish that the gold standard is reliable, because the current gold was authored by a single coder. To certify the gold, we plan a second independent coder (Coder B) who re-encodes all 26 datasets × 5 scored fields = 130 cells from the same `sources/<id>.txt` excerpts under a double-blind procedure and a shared encoding guide (IAA_PROTOCOL.md). Agreement is quantified with field-appropriate statistics, reported separately and never collapsed into one composite: Cohen's kappa on `source_type` (5 categories); for the three set fields (modalities, countries, intended tasks), a binary present/absent expansion across atomic values with Cohen's kappa plus mean Jaccard; and for `sample_counts`, per-key exact-match and overall agreement rates (no kappa forced onto a count dict). Each kappa/rate carries a 95% confidence interval from 2000 bootstrap resamples. The computation script (`compute_iaa.py`) reuses the exact field definitions and comparison semantics of M4. **All IAA values are PENDING** until the second coder completes `coder_b/`; the protocol and script are in place so the true figures are produced by a single command once annotation finishes. IAA (human-human reliability of the gold) is a distinct construct from the LLM-versus-gold numbers above (90.0% exact-match; source-type κ = 0.675) and is reported separately.

### Implementation and availability

MedDataCard runs without GPU. Data cards are produced by `generate_all.py --llm --provider dashscope`; M4 evaluation by `evaluate_m4.py`; audits by `audit_st_mapping.py`, `audit_fabrication.py`, and `audit_compliance_diversity.py`. The web tool is a Streamlit application with three tabs (card generation, compliance and diversity audit, publication figures). Source code, schemas, audit scripts, generated cards, and figures are released under the repository license; the dashboard is deployed at https://meddatacard.streamlit.app.

## Results

### RQ1: Extraction fidelity

Across all 26 datasets, the hybrid pipeline achieved 90.0% exact-match accuracy (117/130) over 130 scored cells (Fig. 1). Relaxing sample-count key labels to numeric equivalence (the model records the same number under a synonymous key such as `studies` instead of `admissions`) raised agreement to 120/130 (about 92%). Cohen's kappa for source type was 0.675 (substantial, Landis and Koch 0.61-0.80), based on the full 26-dataset marginal distribution across repository, challenge, paper supplement, registry, and other. All 26 generated cards passed schema validation; every deleted field is traceable through `pending_verification`. The 13 residual errors were non-dispersed. Modality, countries, and intended tasks had zero errors under subset semantics. Six were source-type over-generalization (confusing repository, registry, and challenge), and seven were sample-count key-label discrepancies (three synonymous-key numeric-correct, four genuine errors: BraTS 2024 wrong patient count, ISIC 2024 conflicting image total, eICU-CRD missing hospital count, UK Biobank empty extraction). The error map shows the pipeline is reliable on free-text set fields and weakest on coarse categorical labels and numeric count keys, and all errors were contained by the guardrail and gold standard.

### RQ2: Standard fidelity and compliance gaps

The schema achieved 100% structural coverage of all 18 documentation recommendations at the field level. The recommendation-level mean field coverage of the 26 hybrid cards (from `st_mapping.csv`) was 70.3% (pillars 77.6%, 65.4%, 82.1%, 37.2%). The per-dataset pillar completeness (from `audit_experiments.csv`, Fig. 2) was 63.2% for description and access, 54.7% for population and geography, 79.3% for bias and annotation, and 59.6% for ethics; the composite ST compliance index mean was 64.2 (Fig. 2). The two metrics differ in caliber but are complementary: the first measures whether the schema maps to each recommendation, and the second measures how much each card actually fills per pillar. The per-dataset completeness leaderboard (Fig. 4) showed large cross-dataset variation (39.1%-76.8%). The dataset diversity score (five-indicator mean, Fig. 3) was 0.485 (0-1): geographic representativeness 0.21, population-subgroup reporting 0.49, skin-tone/Fitzpatrick reporting 0.12, annotation provenance 0.77, and generalizability statement 0.85. Geographic (0.21) and skin-tone (0.12) exposed the core representation gap (per-dataset distribution in Fig. 5), while annotation provenance and generalizability statement were better covered. Compared with the catalogue-only baseline, hybrid completion raised the mean overall field fill across all 38 schema fields by about 52.9 percentage points (hybrid 63.4% versus baseline 10.5%), confirming that LLM completion substantially fills ST fields the manual catalogue missed. This 63.4% overall fill is distinct from the 63.2% mean of the four pillar-completeness values reported above; both are real but measured at different granularity. Stratified by data modality (Fig. 6), the skin-tone/Fitzpatrick sub-indicator was near-zero in every group (0.00 for text, multi-modal, physiological, EHR and genomics resources; 0.27 for radiology), indicating that the skin-representation gap is modality-agnostic rather than confined to imaging. Extending the cross-tabulation to modality by geographic region (Fig. 7) shows the gap compounds along both axes: EHR/tabular resources appeared only from North America (Diversity 0.31) and genomics only from an unspecified region (0.53), while radiology/imaging spanned all six continent-level regions (0.42-0.67). EHR/tabular resources uniquely omitted annotation provenance (0.00), whereas multi-modal resources attained the highest composite diversity (0.60) yet still reported skin-tone at 0.00. The most prominent gaps were data drift over time (23.1% card coverage), subgroups and differential outcomes (11.5%), patient and public involvement (PPIE) (0.0%), and bias and impact assessment (11.5%); these reflect genuine under-reporting in source documents, not schema omission.

### RQ3: Anti-fabrication behavior

Across the 26 hybrid cards, the guardrail captured 14 schema-violating LLM fields and deleted or rolled them back, a capture rate of 0.54 per card. The 14 capture events deleted 21 field mentions across 7 schema fields: over-enumerated medical-field labels (7), source type (4), modality (3), intended tasks (3), data-collection setting (2), method (1), and annotation type (1). A further 10 items were baseline heuristic geographic inferences pending confirmation (distinct from LLM overreach, routed to human confirmation). No fabricated field entered any published card.

### RQ4: Weight sensitivity

Under 200 random Dirichlet weight vectors, the Spearman rank correlation between alternative-weight and equal-weight rankings was 0.92 (minimum 0.705) for the compliance index and 0.937 (minimum 0.745) for the diversity score. Dataset rankings were robust to reasonable weight choices.

## Discussion

### Operationalizing the representation gap

Geographic representativeness (0.21) and skin-tone/Fitzpatrick reporting (0.12) reveal that current flagship medical-AI training and evaluation data are highly concentrated in source, and minority and dark-skinned populations are nearly invisible at the documentation level. MedDataCard converts this qualitative concern into a quantifiable metric comparable across datasets and rankable on a leaderboard. Figure 5 renders the gap structure per dataset: the skin-tone column is nearly all red and the geographic column is broadly low. This directly answers the STANDING Together core demand to disclose transparently who is represented and how. The gap is not remedied by changing data type. Figure 6 stratifies the five sub-indicators by modality and shows that skin-tone reporting stays at or near zero in all seven modality groups, while EHR/tabular resources uniquely fail to report annotation provenance. Multi-modal resources reach the highest composite diversity (0.60) but still omit skin-tone, so adding modalities does not by itself close the representation gap. The modality-by-region cross-tabulation (Fig. 7) shows the gap also compounds geographically: EHR/tabular coverage is confined to North America and genomics to an unspecified region, whereas radiology/imaging reaches all six continent-level regions (0.42-0.67), so neither modality breadth nor geography alone closes the gap.

### Anti-fabrication as a compliance trust mechanism

RQ3 shows that under the constraint of zero fabricated fields escaping, disclosure becomes trustworthy. This is fundamentally different from purely generative data-card tools, which may use fluent text to mask facts unsupported by source files. The guardrail decouples how much the LLM can fill from what the LLM cannot invent, making automated extraction acceptable in regulatory and journal-review settings.

### The value and boundary of LLM completion

Hybrid cards raised overall completeness from 10.5% (baseline) to 63.4%, confirming that LLMs systematically fill ST fields the manual catalogue missed. Yet errors concentrate in coarse categorical labels (source type, 6/26) and numeric count keys (sample counts, 7/26), while modality, countries, and intended tasks had zero errors. This error map implies that free-text set fields are reliably extractable by LLMs, whereas fields requiring canonical enums or exact counts must rely on the guardrail and human review.

### Weight robustness

The RQ4 Spearman correlations (compliance 0.92, diversity 0.937) show that datasets' relative positions on the leaderboard are insensitive to weight choice, so conclusions do not hinge on subjective weight settings.

## Limitations and future work

**Single-coder gold standard (IAA PENDING).** The current M4 gold standard was built by one coder. A second independent coder and a full double-coding protocol are now defined (IAA_PROTOCOL.md), and the calculation script (`compute_iaa.py`) is in place and verified (gold-versus-gold self-test yields κ = 1.0). However, the second coder has not yet completed annotation of `coder_b/`; therefore all IAA figures (source-type Cohen's κ, the three set-field κ / mean Jaccard, and the `sample_counts` agreement rates) remain **PENDING** and are not reported here. Once Coder B finishes, the true human-human agreement is computed by a single command and will be reported as reliability evidence for the gold; no IAA value is asserted in advance.

**Convenience sample.** The 26 datasets are a flagship set covering major modalities, not a census of medical-AI datasets; generalizability is bounded accordingly. Within the modality-stratified analysis (Fig. 6), several groups are small (Genomics n=1, EHR/Tabular n=2, Physio n=3); their subgroup means are reported as exploratory and should not be over-interpreted.

**Metadata-level, not raw-data-level.** The audit uses only metadata from public abstracts or READMEs and touches no raw data, so it cannot assess true skin-tone distributions or actual subgroup performance, which require data-level measurement; datasets with empty geographic or skin-tone fields are counted as not reported rather than estimated.

**Normative absolute thresholds.** The compliance index and diversity score depend on weights and metric definitions; we provide weight-sensitivity evidence, but the thresholds themselves need community negotiation.

**Literature verification.** All five foundation-model exemplars are verified (search date August 2026): UNI, CONCH, and MONET at *Nat. Med.* 30, 850-862, 863-874, and 1154-1165 (2024), respectively; Virchow at *Nat. Med.* 30, 2924-2935 (2024); Prov-GigaPath at *Nature* 630, 181-188 (2024).

**Future work.** We will complete multi-coder IAA (the layered representation-gap figure is already generated; see Fig. 5), adopt the reproducible dataset diversity score as a foundation metric for broader fairness auditing and regulatory submission workflows, and extend the audit from metadata to licensed raw-distribution indicators.

## Conclusion

MedDataCard is the first framework to operationalize the 18 STANDING Together documentation recommendations as machine-verifiable, computable data cards, and to provide a zero-fabrication, zero-GPU dual-track extraction pipeline with an anti-fabrication guardrail. Across 26 flagship datasets, extraction accuracy reached 90.0% (kappa = 0.675), schema structural coverage was 100%, and we systematically quantified representation gaps in geographic (0.21) and skin-tone (0.12) dimensions and the zero-disclosure status of PPIE. The guardrail buys compliance trust at the cost of zero fabricated fields escaping.

## Data and code availability

Source code, the ST data-card schema, audit scripts, all 26 generated data cards, and publication figures are released in the project repository under its license. The interactive web tool and audit dashboard are deployed at https://meddatacard.streamlit.app. No raw dataset was accessed; the audit is metadata-level and requires no data-use agreement.

## References

1. Alderman, J. E. et al. Tackling algorithmic bias and promoting transparency in health datasets: the STANDING Together consensus recommendations. *Lancet Digit. Health* (2024). DOI:10.1016/S2589-7500(24)00224-3
2. Xu, A., Ding, R. & Wang, L. ChatPD: an LLM-driven paper-dataset networking system. *Proc. 31st ACM SIGKDD Conf. Knowledge Discovery and Data Mining (KDD '25)* (2025). DOI:10.1145/3711896.3737202
3. Mitchell, M. et al. Model cards for model reporting. *Proc. 2019 AAAI/ACM Conf. on AI, Ethics, and Society (FAT* '19)* (2019).
4. Gebru, T. et al. Datasheets for datasets. *Commun. ACM* 64, 86-92 (2021).
5. Lhoest, Q. et al. HuggingFace datasets: a unified interface for sharing, exploring, and processing datasets. *Proc. EMNLP 2021 (Demos)* (2021).
6. Brickley, D., Burgess, M. & Noy, N. Google dataset search: building a search engine for datasets in an open web ecosystem. *Proc. WWW 2019* (2019).
7. Ma, J. et al. Segment anything in medical images. *Nat. Commun.* 15, 654 (2024). DOI:10.1038/s41467-024-44824-z
8. Chen, R. J. et al. Towards a general-purpose foundation model for computational pathology. *Nat. Med.* 30, 850-862 (2024). DOI:10.1038/s41591-024-02857-3
9. Lu, M. Y. et al. A visual-language foundation model for computational pathology. *Nat. Med.* 30, 863-874 (2024). DOI:10.1038/s41591-024-02856-4
10. Xu, H. et al. A whole-slide foundation model for gigapixel pathology. *Nature* 630, 181-188 (2024). DOI:10.1038/s41586-024-07441-w
11. Vorontsov, E. et al. A foundation model for clinical-grade computational pathology and rare cancers detection. *Nat. Med.* 30, 2924-2935 (2024). DOI:10.1038/s41591-024-03141-0
12. MONET: a literature-based image-text foundation model for transparent medical imaging AI. *Nat. Med.* 30, 1154-1165 (2024). DOI:10.1038/s41591-024-02887-x

## Figure checklist

- **Fig. 1**: Extraction fidelity by scored field (RQ1): exact-match accuracy per modality, sample counts, countries, intended tasks, and source type across 26 datasets.
- **Fig. 2**: ST pillar completeness (per-dataset) and composite ST compliance index (RQ2).
- **Fig. 3**: Dataset diversity sub-indicators (RQ2): GEO 0.21, POP 0.49, SKIN 0.12, ANN 0.77, GEN 0.85.
- **Fig. 4**: Per-dataset ST completeness leaderboard (RQ2), range 39.1%-76.8%.
- **Fig. 5**: Representation-gap heatmap (26 datasets x 5 sub-indicators, sorted by composite diversity index; worst at top). Skin-tone nearly all red, geography broadly low, revealing the core representation gap.
- **Fig. 6**: Modality-stratified representation gaps (7 modality groups x 5 sub-indicators, plus composite diversity per group; group sizes n annotated). Skin-tone near-zero in every group (modality-agnostic gap); EHR/tabular uniquely omits annotation provenance (0.00); multi-modal highest composite diversity (0.60) yet skin-tone 0.00.
- **Fig. 7**: Modality x geographic-region representation-gap matrix (6 modality groups x 8 regions; cell = mean composite Diversity Index, n annotated; '-' = no dataset of that modality from that region). EHR/tabular confined to North America (0.31); genomics only unspecified (0.53); radiology/imaging spans all six continents (0.42-0.67).
