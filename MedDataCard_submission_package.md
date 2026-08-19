*Author note (not for submission): this package supports submission to npj Digital Medicine (primary), Lancet Digital Health, or Scientific Data. Cover Letter and Highlights target npj Digital Medicine / Lancet Digital Health; the Structured Abstract targets Scientific Data. Every number traces to m4_report.json, audit_experiments.csv, st_mapping.csv, or fabrication_audit.csv. Replace bracketed placeholders before sending.*

---

# Part A. Cover Letter (npj Digital Medicine)

**[Date]**

Editorial Office
npj Digital Medicine
Nature Portfolio

Dear Editor,

Please find enclosed our manuscript entitled "MedDataCard: an automated framework for generating STANDING Together-compliant medical-AI data cards and auditing representation gaps" for consideration as an Article (methods/resource) in npj Digital Medicine.

Algorithmic bias in medical AI propagates through training and evaluation data and amplifies health inequities. In December 2024 the STANDING Together consensus published the first unified reporting standard for dataset diversity, inclusivity, and generalizability (29 recommendations, of which 18 are documentation recommendations cardable as data cards). Three problems remain open. No machine-readable implementation of these recommendations exists. Manual data-card authoring is costly and uneven, so systematic audits of many datasets are impractical. And automated metadata extraction with large language models can fabricate facts absent from source text, threatening the truthfulness that disclosure demands.

We present MedDataCard, a framework that translates the 18 ST documentation recommendations into a constrained JSON schema (38 fields, 6 required) and generates compliant data cards through a dual-track pipeline: a zero-fabrication baseline from a curated catalogue and a hybrid track that adds LLM completion gated by an anti-fabrication schema guardrail. Across 26 flagship datasets and 130 scored cells, the hybrid pipeline reached 90.0% exact-match accuracy (117/130) against a human gold standard, with source-type Cohen's kappa of 0.675. Schema coverage of the 18 recommendations was 100%. The five-indicator diversity score (0.485) exposed a core representation gap: geographic representativeness (0.21) and skin-tone/Fitzpatrick reporting (0.12) were markedly lower than annotation provenance (0.77) and generalizability statements (0.85). Stratified by modality, the skin-tone gap was near-zero in every group, showing it is modality-agnostic. The guardrail intercepted 14 out-of-schema fields with no fabricated content escaping.

This work fits the scope of npj Digital Medicine because it delivers an open, computable method and tool that directly advance transparent, fair, and reproducible medical AI. It answers the journal's emphasis on methods, evaluation, and health-equity impact, and it releases an open-source Streamlit generator and audit dashboard with a reproducibility leaderboard.

The manuscript is original, has not been published elsewhere, and is not under consideration by another journal. All authors approve the submission. No ethical approval was required because the audit uses only public metadata and touches no human subjects' raw data. We confirm compliance with the STANDING Together disclosure principles this work implements. Suggested reviewers and any prior preprint posting are available on request.

Thank you for your consideration. We look forward to your response.

Sincerely,
[Corresponding Author Name]
[Affiliation]
[Email]

---

# Part B. Highlights (npj Digital Medicine / Lancet Digital Health, max 85 characters each incl. spaces)

1. Maps all 18 STANDING Together recommendations to machine-readable data cards.
2. Zero-fabrication pipeline reaches 90.0% accuracy (Cohen kappa 0.675) on 26 datasets.
3. Audit of 26 datasets exposes geographic (0.21) and skin-tone (0.12) gaps.
4. Guardrail intercepted 14 out-of-schema fields; no fabricated content escaped.
5. Open-source Streamlit tool and reproducibility leaderboard for fair-AI auditing.

---

# Part C. Structured Abstract (Scientific Data variant)

**Background**
In December 2024 the STANDING Together consensus set the first unified reporting standard for dataset diversity, inclusivity, and generalizability through 29 recommendations, of which 18 are documentation recommendations that can be expressed as data cards. No machine-readable implementation exists, manual authoring is costly and uneven, and automated metadata extraction with large language models can fabricate facts absent from source text.

**Objectives**
To operationalize the 18 STANDING Together documentation recommendations as computable, auditable data cards, and to provide a reproducible metric for auditing representation gaps across public medical-AI datasets under a zero-fabrication constraint.

**Methods**
We built a constrained JSON schema (38 fields, 6 required; JSON Schema Draft 2020-12) that maps the 18 documentation recommendations across the four ST pillars. A dual-track pipeline generates cards: a catalogue-only baseline with zero large-language-model use, and a hybrid track that adds LLM completion gated by a schema guardrail deleting or rolling back any out-of-schema field. We validated extraction on 26 flagship datasets (130 scored cells) against a human gold standard, and computed per-pillar completeness, a composite compliance index, and a five-indicator dataset diversity score (geographic, population-subgroup, skin-tone/Fitzpatrick, annotation provenance, generalizability). Weight sensitivity drew 200 Dirichlet weight vectors and computed Spearman rank correlations against equal-weight rankings.

**Results**
Hybrid extraction reached 90.0% exact-match accuracy (117/130; source-type Cohen's kappa 0.675). Schema coverage was 100% of the 18 documentation recommendations. Per-dataset pillar completeness was 63.2%, 54.7%, 79.3%, and 59.6%; the composite compliance index mean was 64.2. The diversity score (0.485) exposed geographic (0.21) and skin-tone/Fitzpatrick (0.12) gaps, while annotation provenance (0.77) and generalizability statements (0.85) were better covered. Stratified by modality, skin-tone reporting stayed near zero in all groups, indicating a modality-agnostic gap. The guardrail intercepted 14 out-of-schema fields with zero fabricated content escaping. Rankings were robust to weight choice (Spearman 0.92 for compliance, 0.937 for diversity).

**Conclusions**
MedDataCard turns the STANDING Together consensus into executable, auditable data cards and supplies a foundation metric for fair-AI auditing. The modality-agnostic skin-tone gap shows representation disclosure must improve regardless of data type, and the anti-fabrication guardrail makes automated extraction acceptable in regulatory and journal-review settings.

**Data availability**
Source code, the ST data-card schema, audit scripts, all 26 generated data cards, and publication figures are released in the project repository at https://github.com/echocheng-y/MedDataCard. The interactive web tool and audit dashboard are deployed at https://meddatacard.streamlit.app. No raw dataset was accessed; the audit is metadata-level and requires no data-use agreement.

---

# Part D. Cover Letter (Lancet Digital Health variant)

**[Date]**

Editorial Office
The Lancet Digital Health

Dear Editor,

Please consider our manuscript "MedDataCard: an automated framework for generating STANDING Together-compliant medical-AI data cards and auditing representation gaps" for publication in The Lancet Digital Health.

The Lancet Digital Health seeks work that advances equitable, trustworthy, and clinically actionable digital health. MedDataCard responds directly. Algorithmic bias in medical AI is a health-equity problem: we show that 26 flagship datasets concentrate representation in source geography (geographic sub-indicator 0.21) and nearly omit skin-tone documentation (0.12), and that this gap is modality-agnostic and compounds geographically (EHR/tabular only from North America; genomics only from an unspecified region). By turning the 2024 STANDING Together consensus into machine-readable, auditable data cards with a zero-fabrication guardrail, MedDataCard gives regulators, journal reviewers, and clinical deployment teams a computable tool to demand and verify representation disclosure before models reach patients.

Across 26 datasets the hybrid pipeline reached 90.0% extraction accuracy (Cohen kappa 0.675) under a zero-fabrication constraint, with 100% schema coverage of the 18 ST documentation recommendations and a reproducible compliance and diversity leaderboard. The work is translational: it converts a qualitative equity concern into a rankable metric and an open-source Streamlit tool already deployed at https://meddatacard.streamlit.app.

The manuscript is original, unpublished, and not under consideration elsewhere; all authors approve submission. No ethical approval was required (metadata-only audit, no human-subjects raw data). We confirm alignment with the STANDING Together disclosure principles this journal advocates.

Thank you for your consideration.

Sincerely,
[Corresponding Author Name]
[Affiliation]
[Email]

---

# Part E. Cover Letter (Scientific Data variant)

**[Date]**

Editorial Office
Scientific Data (Nature Portfolio)

Dear Editor,

We submit our manuscript "MedDataCard: an automated framework for generating STANDING Together-compliant medical-AI data cards and auditing representation gaps" as a Data Descriptor to Scientific Data.

Scientific Data publishes descriptions of scientifically valuable datasets and the tools that make them reusable. MedDataCard delivers a reusable, open resource: 26 ST-compliant medical-AI data cards generated from public abstracts or repository READMEs, a constrained JSON schema operationalizing the 18 STANDING Together documentation recommendations, and a metadata-level audit of representation gaps across those datasets, all released with code, schemas, and figures. The resource is immediately reusable: other teams can regenerate cards for new datasets, reproduce the compliance and diversity leaderboard, and adopt the five-indicator diversity score as a foundation metric for fairness auditing.

The accompanying data are fully available: source code, schema, audit scripts, all 26 generated data cards, and publication figures are in the project repository (https://github.com/echocheng-y/MedDataCard); the interactive generator and audit dashboard are deployed at https://meddatacard.streamlit.app. No raw dataset was accessed; the audit is metadata-level and requires no data-use agreement, so the descriptor is reproducible without restricted data.

We confirm the manuscript describes a publicly available, citable resource with clear reuse value, and that all authors approve submission. No ethical approval was required.

Thank you for your consideration.

Sincerely,
[Corresponding Author Name]
[Affiliation]
[Email]
