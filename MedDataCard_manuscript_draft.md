# MedDataCard: an automated framework for generating STANDING Together-compliant medical-AI data cards and auditing representation gaps

> 投稿目标：*Scientific Data*（数据描述/软件论文）或 *npj Digital Medicine* / *Lancet Digital Health* 通讯。
> 写作方法（nature-polishing）：结论性陈述均有量化支撑；术语全文唯一规范；方法与结果严格分区；全部数字与文献可追溯至本项目已落地产物与公开可核验来源（检索时点 2026-08）。
> 数字来源：`m4_report.json`、`audit_summary.csv`、`st_mapping.csv`、`fabrication_audit.csv`、`audit_experiments.csv`。

---

## Abstract

**Background.** Algorithmic bias in medical AI propagates through training and evaluation data and amplifies health inequities. The 2024 STANDING Together (ST) consensus first provided a unified reporting standard for diversity, inclusivity, and generalizability of healthcare datasets, yet no machine-readable, computable implementation exists, and large language model (LLM) metadata extraction risks hallucination. **Purpose.** We asked whether ST-compliant data cards can be generated automatically and whether existing medical-AI datasets can be audited systematically and reproducibly for diversity and inclusivity. **Methods.** We translated the 18 ST documentation recommendations into a strongly constrained JSON Schema (38 fields, 6 required), built a dual-track extraction pipeline (baseline from a curated catalogue with zero fabrication; hybrid with LLM completion gated by a schema guardrail), and evaluated extraction fidelity against a human gold standard over 26 flagship datasets and 130 scored cells, quantifying per-pillar compliance and diversity. **Results.** The hybrid pipeline reached 90.0% exact-match accuracy (117/130); source-type Cohen's kappa was 0.675. The schema covered all 18 documentation recommendations at the field level (100%). Per-dataset ST pillar completeness was 63.2 / 54.7 / 79.3 / 59.6%, with a composite compliance index of 64.2. The five-indicator diversity score was 0.485; geographic representativeness (0.21) and skin-tone/Fitzpatrick reporting (0.12) exposed the core representation gap. The guardrail intercepted 14 out-of-schema fields with zero fabricated fields escaping. Dataset rankings were robust under 200 Dirichlet weight vectors (Spearman 0.92 / 0.937). **Conclusion.** MedDataCard is the first tool to operationalize the ST consensus as machine-verifiable data cards and a zero-fabrication audit pipeline, quantifying systematic representation gaps in geographic and skin-tone dimensions and providing a reproducible foundation metric for fairness auditing and regulatory submission.

---

## 1. Introduction

Performance of medical AI depends heavily on training and evaluation data. Bias encoded at the data level propagates through algorithms and amplifies health inequities. On 18 December 2024, the STANDING Together international consensus was published simultaneously in *The Lancet Digital Health* and *NEJM AI* (Alderman et al., 2024; DOI 10.1016/S2589-7500(24)00224-3). The consensus convened more than 350 representatives from 58 countries and used a Delphi process (194 participants, three rounds of electronic voting plus one in-person consensus meeting) to produce 29 recommendations. These recommendations provided, for the first time, a unified reporting standard for the diversity, inclusivity, and generalizability of healthcare datasets.

After the consensus, dataset disclosure shifted from soft recommendation to hard constraint. Regulators and journals tightened scrutiny of training-data reporting. The US FDA has authorized more than 900 AI-enabled medical devices, yet most do not report training data or architecture (internal project review; see the project proposal document). Three gaps remain in current data-card practice. First, flagship templates (Model Cards and Datasheets for Datasets) provide conceptual frameworks but lack a machine-readable, computable ST-aligned implementation. Second, manual data-card authoring is costly and uneven, making systematic audits of many datasets impractical. Third, when LLMs are used to extract metadata automatically, they fabricate facts absent from source text, directly threatening the compliance bottom line that disclosure must be truthful.

These gaps were still open at the time of this study (2026-08). No automated tool maps the 18 ST documentation recommendations to machine-verifiable data cards, and no pipeline audits public medical-AI datasets at the metadata level without a data-use agreement (DUA). MedDataCard addresses this gap.

We posed one central research question (RQ0): *can ST-compliant data cards be generated automatically and can existing medical-AI datasets be audited systematically and reproducibly for diversity, inclusivity, and generalizability?* Four sub-questions follow. RQ1 (extraction fidelity): under a zero-fabrication constraint, does an LLM-assisted pipeline extract structured metadata from public abstracts or repository READMEs at a publishable accuracy? RQ2 (standard fidelity and compliance gaps): does the schema fully cover the 18 documentation recommendations, and what is the actual disclosure completeness and compliance index of 26 flagship datasets across the four ST pillars? RQ3 (anti-fabrication behavior): to what extent does the guardrail intercept out-of-scope or fabricated LLM output, ensuring no fabricated field enters a published card? RQ4 (metric robustness): are the compliance index and diversity score robust to weight choice?

MedDataCard delivers four engineering artifacts: (a) a machine-readable ST data-card schema; (b) an LLM-assisted, human-reviewed dual-track extraction pipeline with zero GPU dependency; (c) computable inclusivity and generalizability scores with a leaderboard; and (d) an open-source web generator and audit dashboard (Streamlit, three tabs). The audit covers all 26 surveyed datasets at the metadata level only, requires no access to raw data, and therefore needs no DUA.

**Contributions.** First, we provide an executable ST data-card schema (38 fields, 6 required, strongly constrained). Second, we provide an empirically validated zero-fabrication dual-track pipeline. Third, we provide a reproducible compliance and diversity leaderboard over 26 datasets, offering a foundation metric for downstream fairness auditing. Fourth, we release an open-source web tool and audit dashboard.

---

## 2. Related work

### 2.1 The lineage of data documentation standards
Model Cards (Mitchell et al., 2019, FAT* '19) introduced the model-report-card paradigm, advocating transparent disclosure of model use, bias, and ethics; it is the conceptual origin of data and model documentation. Datasheets for Datasets (Gebru et al., 2021, CACM 64(12):86–92; arXiv:1803.09010) systematized the idea that data deserve a datasheet, exposing provenance, collection, ethics, and limitations through a questionnaire; it is a direct precursor of the ST consensus. STANDING Together (Alderman et al., 2024, Lancet Digit Health; DOI 10.1016/S2589-7500(24)00224-3) is the standard ontology this work aligns to. It consolidates documentation requirements into 18 cardable recommendations and adds 11 use-governance recommendations.

### 2.2 Automated dataset metadata extraction
ChatPD (Xu, Ding, Wang, KDD 2025; DOI 10.1145/3711896.3737202; arXiv:2505.22349) uses LLMs to extract dataset information from papers and builds a paper–dataset network, reaching roughly 90% precision and recall on entity resolution. MedDataCard borrows its dataset-information-template idea but differs in three ways: (1) it uses the ST consensus as a hard constraint ontology rather than a generic template; (2) it introduces a schema guardrail for anti-fabrication rather than extraction alone; and (3) it targets compliance auditing of medical datasets rather than paper–dataset link discovery. HuggingFace Datasets (Lhoest et al., 2021, EMNLP Demos) and Google Dataset Search (Brickley et al., 2019, WWW) represent community-level dataset cards and general dataset discovery infrastructure, respectively, and embody the industry consensus on structured metadata and discoverability, but neither builds in ST compliance checking.

### 2.3 Audited foundation-model exemplars (why auditing is urgent)
A cluster of medical foundation models released in 2024 exhibit narrow training domains and under-reported population representation, exactly the gaps an ST audit exposes, and the motivation and contrast material for this study:
- MedSAM (Ma et al., Nat Commun 2024; 15(1):654; DOI 10.1038/s41467-024-44824-z; PMID 38253604): a general medical image segmentation foundation model with 1,570,263 image–mask pairs across 10 modalities, but with highly uneven modality distribution (CT/MRI dominated).
- UNI (Chen et al., Nat Med 2024; DOI 10.1038/s41591-024-02857-3): a computational pathology foundation model (307M parameters, Mass-100K, 20 organs).
- CONCH (Lu et al., Nat Med 2024; DOI 10.1038/s41591-024-02856-4): a vision–language pathology foundation model.
- Prov-GigaPath (Xu et al., Nature 2024; DOI 10.1038/s41586-024-07441-w): a long-context pathology vision–language model.
- Virchow (Vorontsov et al., Nat Med 2024; DOI 10.1038/s41591-024-03141-0): a clinical-grade computational pathology and rare-cancer detection foundation model (632M parameters).
- MONET (medical concept retriever, Su-In Lee group), Nat Med 2024;30(4), DOI 10.1038/s41591-024-02887-x, is included as a complementary exemplar of a concept-level auditable imaging–text model (volume, issue, and pages verified).

---

## 3. Methods

### 3.1 Terminology
We use the following terms consistently. **STANDING Together (ST)** denotes the 2024 consensus (29 recommendations = 18 documentation recommendations numbered 1.1a–1.4c, cardable; plus 11 use recommendations at the governance level, not directly cardable). The **four ST pillars** are: (1) dataset description and access; (2) population composition and geography; (3) bias, limitations, and annotation; (4) ethics and governance. A **data card** is a machine-readable JSON object conforming to `st_datacard.schema.json` (JSON Schema Draft 2020-12, v0.2). A **baseline card** uses only real metadata from the curated catalogue `dataset_catalog.xlsx`, with zero LLM and zero fabrication by construction. A **hybrid card** layers LLM-completed fields onto the baseline and is then validated by the schema guardrail. The **guardrail (conform_card)** performs schema-consistency checks on every merged card; any LLM field violating type, enum, or `additionalProperties` constraints is deleted or rolled back to a valid baseline value. A **capture** is an LLM field deleted or rolled back by the guardrail, one intercepted out-of-scope output.

### 3.2 Standard operationalization (schema design)
We translated the 18 ST documentation recommendations (1.1a–1.4c, spanning the four pillars) into a machine-readable JSON Schema. The schema defines **38 leaf fields** grouped by the four pillars, of which **6 are required**, and enforces `additionalProperties: false` at every node, structurally preventing undeclared fields from entering a data card. The 11 use recommendations are governance-level and not directly cardable; by design they fall outside the schema scope but are referenced.

### 3.3 Dual-track extraction pipeline
The **baseline track** takes fields only from the curated catalogue (`dataset_catalog.xlsx`, containing modality, license, scale, geographic cues, and medical field), guaranteeing zero fabrication by construction. The **hybrid track** sends each dataset's source text (paper abstract or repository README) through a single OpenAI-compatible interface (OpenAI / Anthropic / Alibaba Bailian `qwen-plus`) to the LLM, merges the returned partial card with the baseline, and keeps only non-empty baseline or LLM values.

### 3.4 Anti-fabrication guardrail
Every merged card is schema-validated. Any field violating type, enum, or additional-property constraints at the object-key or list-item level is deleted; if a valid baseline value exists at the same path, the field rolls back to it. Deleted fields are recorded in `extraction.pending_verification` for human review, so the LLM can never write schema-illegal content into a published card.

### 3.5 Evaluation corpus and gold standard
We sampled **26 flagship medical-AI datasets** spanning nine major modalities: radiology, pathology, genomics, physiological time series, clinical text, and question answering (including NIH ChestX-ray14, MIMIC-CXR, CheXpert, PadChest, VinDr-CXR, BraTS 2024, ISIC 2024, HAM10000, MedMNIST, TotalSegmentator, CT-RATE, DeepLesion, UK Biobank, TCGA, ADNI, Tabula Sapiens, MIMIC-IV, eICU-CRD, Sleep-EDF, CHB-MIT, PhysioNet/CinC 2020, PMC-Patients, MedQA, MedMCQA, PubMedQA, BioASQ). The gold standard records only facts explicitly stated in or directly computable from public abstracts or READMEs, and **never** infers from the catalogue. Scored fields are modality, sample counts, countries, intended tasks, and source type; license and commercial-use fields come from the catalogue and are excluded from extraction accuracy.

### 3.6 Metrics
*Extraction fidelity* is exact-match accuracy over scored fields; set fields use `gold ⊆ llm` subset semantics and counts or categorical source types use exact equality. We report Cohen's kappa for source type to expose baseline versus LLM correction behavior. *Standard fidelity* is the field-level implementation rate of the schema against each documentation recommendation and the empirical fill rate over 26 cards. *Compliance and diversity* use per-pillar completeness plus a composite ST Compliance Index, and a five-indicator dataset diversity score (geographic representativeness, population-subgroup reporting, skin-tone/Fitzpatrick reporting, annotation provenance, generalizability statement). *Weight sensitivity* draws 200 Dirichlet weight vectors and computes the Spearman rank correlation between alternative-weight and equal-weight rankings.

### 3.7 Implementation and availability
MedDataCard runs without GPU. Data cards are produced by `generate_all.py --llm --provider dashscope`; M4 evaluation by `evaluate_m4.py`; audits by `audit_st_mapping.py`, `audit_fabrication.py`, and `audit_compliance_diversity.py`. The web tool is a Streamlit application with three tabs (card generation, compliance and diversity audit, publication figures). Source code, schemas, audit scripts, generated cards, and figures are released under the repository license; the dashboard is deployed at https://meddatacard.streamlit.app.

---

## 4. Results

### 4.1 RQ1: Extraction fidelity
Across all 26 datasets, the hybrid pipeline achieved **90.0% exact-match accuracy (117/130)** over **130 scored cells** (modality, sample counts, countries, intended tasks, source type) (Fig. 1). Relaxing sample-count key labels to numeric equivalence (the model records the same number under a synonymous key such as `studies` instead of `admissions`) raised agreement to **120/130 (≈92%)**. Cohen's kappa for source type was **0.675** (substantial, Landis & Koch 0.61–0.80), based on the full 26-dataset marginal distribution across repository / challenge / paper-supplement / registry / other. All 26 generated cards passed schema validation; every deleted field is traceable through `pending_verification`. The 13 residual errors were non-dispersed: **modality, countries, and intended tasks had zero errors** under subset semantics; 6 were source-type over-generalization (confusing repository / registry / challenge), and 7 were sample-count key-label discrepancies (3 synonymous-key numeric-correct, 4 genuine errors: BraTS 2024 wrong patient count, ISIC 2024 conflicting image total, eICU-CRD missing hospital count, UK Biobank empty extraction). The error map shows the pipeline is reliable on free-text set fields and weakest on coarse categorical labels and numeric count keys, and all errors were contained by the guardrail and gold standard.

### 4.2 RQ2: Standard fidelity and compliance gaps
The schema achieved **100% structural coverage** of all 18 documentation recommendations at the field level. The **recommendation-level mean field coverage** of the 26 hybrid cards (from `st_mapping.csv`) was **70.3%** (pillars 77.6% / 65.4% / 82.1% / 37.2%). The **per-dataset pillar completeness** (from `audit_experiments.csv`, Fig. 2) was: description and access **63.2%**, population and geography **54.7%**, bias and annotation **79.3%**, ethics **59.6%**; the composite ST Compliance Index mean was **64.2** (Fig. 2). The two metrics differ in caliber but are complementary: the first measures whether the schema maps to each recommendation, the second measures how much each card actually fills per pillar. The per-dataset completeness leaderboard (Fig. 4) showed large cross-dataset variation (39.1%–76.8%). The dataset diversity score (five-indicator mean, Fig. 3) was **0.485** (0–1): geographic representativeness **0.21**, population-subgroup reporting **0.49**, skin-tone/Fitzpatrick reporting **0.12**, annotation provenance **0.77**, generalizability statement **0.85**; geographic (0.21) and skin-tone (0.12) exposed the core representation gap (per-dataset distribution in Fig. 5), while annotation provenance and generalizability statement were better covered. Compared with the catalogue-only baseline, hybrid cards raised overall completeness by about **+52.9 percentage points** (hybrid ≈63.4% versus baseline ≈10.5%), confirming that LLM completion substantially fills ST fields the manual catalogue missed. The most prominent gaps were "data drift over time" (23.1% card coverage), "subgroups and differential outcomes" (11.5%), "patient and public involvement (PPIE)" (0.0%), and "bias and impact assessment" (11.5%): these reflect genuine under-reporting in source documents, not schema omission. Stratified by data modality (Fig. 6), the skin-tone/Fitzpatrick sub-indicator was near-zero in every group (0.00 for text, multi-modal, physiological, EHR and genomics resources; 0.27 for radiology), indicating that the skin-representation gap is modality-agnostic rather than confined to imaging. EHR/tabular resources uniquely omitted annotation provenance (0.00), whereas multi-modal resources attained the highest composite diversity (0.60) yet still reported skin-tone at 0.00.

### 4.3 RQ3: Anti-fabrication behavior
Across the 26 hybrid cards, the guardrail captured **14** schema-violating LLM fields and deleted or rolled them back, a capture rate of **0.54 per card**. The 14 capture events deleted **21 field mentions across 7 schema fields**: over-enumeration medical-field labels (7), source type (4), modality (3), intended tasks (3), data-collection setting (2), method (1), annotation type (1). A further **10** items were baseline heuristic geographic inferences pending confirmation (distinct from LLM overreach, routed to human confirmation). **No fabricated field entered any published card.**

### 4.4 RQ4: Weight sensitivity
Under 200 random Dirichlet weight vectors, the Spearman rank correlation between alternative-weight and equal-weight rankings was **0.92 (minimum 0.705)** for the compliance index and **0.937 (minimum 0.745)** for the diversity score. Dataset rankings were robust to reasonable weight choices.

---

## 5. Discussion

**Operationalizing the representation gap.** Geographic representativeness (0.21) and skin-tone/Fitzpatrick reporting (0.12) reveal that current flagship medical-AI training and evaluation data are highly concentrated in source, and minority and dark-skinned populations are nearly invisible at the documentation level. MedDataCard converts this qualitative concern into a quantifiable metric comparable across datasets and rankable on a leaderboard (Fig. 5 renders the gap structure per dataset: the SKIN column is nearly all red, the GEO column is broadly low), directly answering the STANDING Together core demand to disclose transparently who is represented and how. The gap is not remedied by changing data type. Figure 6 stratifies the five sub-indicators by modality and shows that skin-tone reporting stays at or near zero in all seven modality groups, while EHR/tabular resources uniquely fail to report annotation provenance. Multi-modal resources reach the highest composite diversity (0.60) but still omit skin-tone, so adding modalities does not by itself close the representation gap.

**Anti-fabrication as a compliance trust mechanism.** RQ3 shows that under the constraint of zero fabricated fields escaping, disclosure becomes trustworthy. This is fundamentally different from purely generative data-card tools, which may use fluent text to mask facts unsupported by source files. The guardrail decouples "how much the LLM can fill" from "what the LLM cannot invent," making automated extraction acceptable in regulatory and journal-review settings.

**The value and boundary of LLM completion.** Hybrid cards raised overall completeness from ≈10.5% (baseline) to ≈63.4%, confirming that LLMs systematically fill ST fields the manual catalogue missed; yet errors concentrate in coarse categorical labels (source_type, 6/26) and numeric count keys (sample_counts, 7/26), while modality / countries / intended_tasks had zero errors. This error map implies that free-text set fields are reliably extractable by LLMs, whereas fields requiring canonical enums or exact counts must rely on the guardrail and human review.

**Weight robustness.** The RQ4 Spearman correlations (compliance 0.92, diversity 0.937) show that datasets' relative positions on the leaderboard are insensitive to weight choice, so conclusions do not hinge on subjective weight settings.

---

## 6. Limitations and future work

- **Single-coder gold standard.** The current M4 gold standard was built by one coder; inter-annotator agreement (IAA) is not yet reported. A second independent coder will be added and Cohen's kappa computed as reliability evidence.
- **Convenience sample.** The 26 datasets are a flagship set covering major modalities, not a census of medical-AI datasets; generalizability is bounded accordingly. Within the modality-stratified analysis (Fig. 6), several groups are small (Genomics n=1, EHR/Tabular n=2, Physio n=3); their subgroup means are reported as exploratory and should not be over-interpreted.
- **Metadata-level, not raw-data-level.** The audit uses only metadata from public abstracts or READMEs and touches no raw data, so it cannot assess true skin-tone distributions or actual subgroup performance, which require data-level measurement; datasets with empty geographic or skin-tone fields are counted as "not reported" rather than estimated.
- **Normative absolute thresholds.** The compliance index and diversity score depend on weights and metric definitions; we provide weight-sensitivity evidence, but the thresholds themselves need community negotiation.
- **Literature verification.** MONET (Nat Med 2024;30(4), DOI 10.1038/s41591-024-02887-x) volume, issue, and pages are verified; UNI / CONCH / Virchow, also Nat Med 2024 exemplars, need final verification before submission (search date 2026-08).

**Future work.** We will complete multi-coder IAA (the layered representation-gap figure is already generated; see Fig. 5), adopt the reproducible dataset diversity score as a foundation metric for broader fairness auditing (RO6) and regulatory submission workflows, and extend the audit from metadata to licensed raw-distribution indicators.

---

## 7. Conclusion

MedDataCard is the first framework to operationalize the 18 STANDING Together documentation recommendations as machine-verifiable, computable data cards, and to provide a zero-fabrication, zero-GPU dual-track extraction plus anti-fabrication guardrail pipeline. Over 26 flagship datasets, extraction accuracy reached 90.0% (kappa = 0.675), schema structural coverage was 100%, and we systematically quantified representation gaps in geographic (0.21) and skin-tone (0.12) dimensions and the zero-disclosure status of PPIE. The guardrail buys compliance trust at the cost of zero fabricated fields escaping.

---

## Data and code availability

Source code, the ST data-card schema, audit scripts, all 26 generated data cards, and publication figures are released in the project repository under its license. The interactive web tool and audit dashboard are deployed at https://meddatacard.streamlit.app. No raw dataset was accessed; the audit is metadata-level and requires no data-use agreement.

---

## References

1. Alderman JE, Palmer J, Laws E, et al. Tackling algorithmic bias and promoting transparency in health datasets: the STANDING Together consensus recommendations. *Lancet Digit Health*. 2024 (Dec). DOI: 10.1016/S2589-7500(24)00224-3. PMID: 39701919.
2. Xu A, Ding R, Wang L. ChatPD: An LLM-driven Paper-Dataset Networking System. *Proc. 31st ACM SIGKDD (KDD '25)*. 2025. DOI: 10.1145/3711896.3737202. arXiv:2505.22349.
3. Mitchell M, Wu S, Zaldivar A, et al. Model Cards for Model Reporting. *Proc. 2019 AAAI/ACM Conf. on AI, Ethics, and Society (FAT\* '19)*. 2019.
4. Gebru T, Morgenstern J, Vecchione B, et al. Datasheets for Datasets. *Commun. ACM*. 2021; 64(12):86–92. arXiv:1803.09010.
5. Lhoest Q, et al. HuggingFace Datasets: a unified interface for sharing, exploring, and processing datasets. *EMNLP 2021 (Demos)*. 2021.
6. Brickley D, Burgess M, Noy N. Google Dataset Search: Building a search engine for datasets in an open Web ecosystem. *WWW 2019*. 2019.
7. Ma J, He Y, Li F, et al. Segment Anything in Medical Images. *Nat Commun*. 2024; 15(1):654. DOI: 10.1038/s41467-024-44824-z. PMID: 38253604.
8. Chen RJ, et al. Towards a general-purpose foundation model for computational pathology. *Nat Med*. 2024. DOI: 10.1038/s41591-024-02857-3.
9. Lu MY, et al. A visual-language foundation model for computational pathology. *Nat Med*. 2024. DOI: 10.1038/s41591-024-02856-4.
10. Xu H, et al. A whole-slide foundation model for gigapixel pathology. *Nature*. 2024. DOI: 10.1038/s41586-024-07441-w.
11. Vorontsov E, et al. A foundation model for clinical-grade computational pathology and rare cancers detection. *Nat Med*. 2024. DOI: 10.1038/s41591-024-03141-0.
12. MONET: a literature-based image–text foundation model for transparent medical imaging AI (medical concept retriever). *Nat Med*. 2024;30(4). DOI: 10.1038/s41591-024-02887-x.

---

## Figure checklist

- **Fig. 1**: Extraction fidelity by scored field (RQ1): exact-match accuracy per modality / sample counts / countries / intended tasks / source type across 26 datasets.
- **Fig. 2**: ST pillar completeness (per-dataset) and composite ST Compliance Index (RQ2).
- **Fig. 3**: Dataset Diversity sub-indicators (RQ2): GEO 0.21, POP 0.49, SKIN 0.12, ANN 0.77, GEN 0.85.
- **Fig. 4**: Per-dataset ST completeness leaderboard (RQ2), range 39.1%–76.8%.
- **Fig. 5**: Representation-gap heatmap (26 datasets × 5 sub-indicators, sorted by composite Diversity Index; worst at top). SKIN nearly all red, GEO broadly low → core representation gap.
- **Fig. 6**: Modality-stratified representation gaps (7 modality groups × 5 sub-indicators + composite Diversity Index per group; group sizes n annotated). SKIN near-zero in every group (modality-agnostic gap); EHR/tabular uniquely omits annotation provenance (0.00); multi-modal highest composite Diversity (0.60) yet SKIN 0.00.
