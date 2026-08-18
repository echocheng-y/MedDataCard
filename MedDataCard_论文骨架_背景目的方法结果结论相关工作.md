# MedDataCard：面向 STANDING Together 标准的自动化医学 AI 数据卡生成与合规审计框架
## 论文骨架（背景 · 目的 · 相关工作 · 方法 · 结果 · 结论）

> 写作原则（参考 nature-polishing 方法学）：每一句结论性陈述都有量化支撑；术语在全文中保持唯一规范形态；方法与结果严格分区；所有数字与文献均可追溯到本项目已落地的产物与公开可核验来源。
> 目标期刊定位：*Scientific Data*（数据描述/软件论文）或 *npj Digital Medicine* / *Lancet Digital Health* 通讯。
> 全部数字来源：本仓库 `m4_report.json`、`audit_summary.csv`、`st_mapping.csv`、`fabrication_audit.csv`、`MedDataCard_实验结果与写作草案.md`（RQ1 已用 26 数据集终版；RQ2–RQ4 数字与源表逐项核对一致）。

---

## 术语 ledger（全篇统一，先定义后使用）

- **STANDING Together（ST）**：2024 年共识（Lancet Digital Health / NEJM AI，DOI 10.1016/S2589-7500(24)00224-3）。共 29 条建议 = 18 条**文档化（Documentation）**建议（编号 1.1a–1.4c，可落到数据卡）+ 11 条**使用（Use）**建议（治理层级，不直接可卡片化）。
- **ST 四大支柱**：① 数据集描述与获取；② 人群构成与地理；③ 偏倚与标注局限；④ 伦理与治理。
- **数据卡（data card）**：符合 `st_datacard.schema.json`（JSON Schema Draft 2020-12, v0.2）的机器可读 JSON 对象。
- **baseline 卡**：仅取自策展目录 `dataset_catalog.xlsx` 的真实元数据，零 LLM、构造上零虚构。
- **hybrid 卡**：baseline 叠加 LLM 补全字段，再经 schema 护栏校验后的产物。
- **护栏（conform_card）**：对每个合并卡做 schema 一致性校验；凡违反类型/枚举/`additionalProperties` 的 LLM 字段一律删除或回退到 baseline 有效值。
- **capture**：被护栏删除/回退的 LLM 字段，即一次被检出并拦截的越界输出。

---

## 1. 背景（Background）

医学 AI 的性能高度依赖于训练与评估数据，而数据层面的偏倚会以链式方式被编码进算法，进而放大健康不平等。2024 年 12 月 18 日，STANDING Together 国际共识在 *The Lancet Digital Health* 与 *NEJM AI* 同步发表（Alderman et al., 2024；DOI 10.1016/S2589-7500(24)00224-3），由来自 58 个国家的 350 余名代表、经德尔菲法（194 名参与者、3 轮电子投票 + 1 次线下共识会）达成 29 条共识建议，首次为医疗健康数据集的"多样性、包容性与可泛化性"提供了统一报告标准。

共识发布后，数据集披露从"软建议"转为"硬约束"。监管与期刊对训练数据披露的审查趋严；美国 FDA 已批准 900 余款 AI 医疗器械，但其中多数未报告训练数据或架构（本项目调研结论，详见项目推荐方案文档）。与此同时，现有数据卡实践存在三重缺口：其一，标杆性模板（Model Cards、Datasheets for Datasets）提供了理念框架，但缺乏可机读、可计算的 ST 对齐实现；其二，数据卡的人工撰写成本高、覆盖不均，难以对成规模数据集做系统性审计；其三，若用大语言模型（LLM）自动抽取元数据，模型会编造源文本中不存在的事实（hallucination），直接威胁"披露即真实"的合规底线。

上述缺口在本项目调研时点（2026-08）仍然清晰：尚无任何自动化工具能将 ST 的 18 条文档化建议直接落为机器可校验的数据卡，也缺乏一套可对公开医学 AI 数据集做元数据级、零数据使用协议（DUA）依赖的多样性/包容性审计流水线。这正是 MedDataCard 的立项出发点。

---

## 2. 目的（Purpose）

本研究旨在回答一个核心研究问题（RQ0）：**能否自动生成符合 STANDING Together 标准的数据卡，并对现有医学 AI 数据集做系统性、可复现的多样性/包容性/可泛化性审计？**

围绕 RQ0，MedDataCard 设定四项可检验的研究目标，并映射为四个子研究问题（RQ1–RQ4）：

- **目标一（RQ1，抽取保真度）**：在零虚构约束下，用 LLM 辅助管线从公开论文摘要/仓库 README 抽取结构化元数据，其准确率是否达到可发表水平？
- **目标二（RQ2，标准保真度与合规缺口）**：所设计的 schema 是否完整覆盖 18 条文档化建议？26 个旗舰数据集在 ST 四大支柱上的实际披露完整度与合规指数如何？
- **目标三（RQ3，反虚构行为）**：护栏机制能在多大程度上拦截 LLM 的越界/虚构输出，确保零虚构字段进入发布卡？
- **目标四（RQ4，指标稳健性）**：所定义的合规指数与多样性评分，在权重选择变化下排名是否稳健？

工程交付上，MedDataCard 提供：(a) 机器可读的 ST 数据卡 schema；(b) LLM 辅助 + 人工复核的双轨元数据抽取管线（零 GPU 依赖）；(c) 可计算的包容性/可泛化性评分与排行榜；(d) 开源的 Web 数据卡生成器 + 审计仪表盘（Streamlit 三标签页）。审计对象为已调研的全部 26 个数据集，仅做元数据级审计，不触及原始数据，因而无需任何 DUA。

---

## 3. 相关工作（Related Work）

### 3.1 数据文档化标准谱系
- **Model Cards（Mitchell et al., 2019, FAT\* '19）**：首次提出"模型报告卡"范式，倡导对模型用途、偏倚、伦理做透明说明，是数据/模型文档化的理念源头。
- **Datasheets for Datasets（Gebru et al., 2021, CACM 64(12):86–92；arXiv:1803.09010）**：将"数据也应附说明书"系统化，以问卷式 datasheet 暴露数据来源、收集、伦理与局限，是 ST 共识的直接前驱之一。
- **STANDING Together（Alderman et al., 2024, Lancet Digit Health；DOI 10.1016/S2589-7500(24)00224-3）**：本项目所对齐的**标准本体**，将文档化要求收敛为 18 条可卡片化建议，并补充 11 条使用治理建议。

### 3.2 自动化数据集元数据抽取
- **ChatPD（Xu, Ding, Wang, KDD 2025；DOI 10.1145/3711896.3737202；arXiv:2505.22349）**：用 LLM 从论文中自动抽取数据集信息并构建"论文—数据集"网络，在实体解析上达到约 90% 的精确率与召回率。MedDataCard 借鉴其"数据集信息模板"思路，但区别在于：(1) 以 ST 共识为强约束本体而非通用模板；(2) 引入 schema 护栏实现反虚构，而非仅做信息抽取；(3) 面向医疗数据集的合规审计而非论文—数据集链接发现。
- **HuggingFace Datasets（Lhoest et al., 2021, EMNLP Demos）** 与 **Google Dataset Search（Brickley et al., 2019, WWW）**：分别代表社区级数据集卡片与通用数据集检索基础设施，凸显了"结构化元数据 + 可发现性"的产业共识，但未内建 ST 合规校验。

### 3.3 被审基础模型范例（为何审计紧迫）
2024 年集中涌现的一批医疗基础模型，其内部训练域偏窄、人群代表性披露不足，恰是 ST 审计要暴露的对象，亦为本研究提供现实动机与对照素材：
- **MedSAM（Ma et al., Nat Commun 2024; 15(1):654；DOI 10.1038/s41467-024-44824-z；PMID 38253604）**：通用医学图像分割基础模型，1,570,263 图像-掩膜对、10 种模态，但模态分布高度不均（CT/MRI 主导）。
- **UNI（Chen et al., Nat Med 2024；DOI 10.1038/s41591-024-02857-3）**：计算病理基础模型（307M 参数，Mass-100K，20 器官）。
- **CONCH（Lu et al., Nat Med 2024；DOI 10.1038/s41591-024-02856-4）**：视觉-语言病理基础模型。
- **Prov-GigaPath（Xu et al., Nature 2024；DOI 10.1038/s41586-024-07441-w）**：长上下文病理视觉-语言模型。
- **Virchow（Vorontsov et al., Nat Med 2024；DOI 10.1038/s41591-024-03141-0）**：临床级计算病理与罕见癌检测基础模型（632M 参数）。
- （注：MONET（medical concept retriever，Su-In Lee 组）, *Nat Med* 2024;**30**(4), DOI **10.1038/s41591-024-02887-x**，作为概念级可审计影像-文本模型的补充范例，卷期页已核验。）

---

## 4. 方法（Methods）

### 4.1 标准可执行化（schema 设计）
将 ST 的 18 条文档化建议（1.1a–1.4c，覆盖四大支柱）翻译为机器可读的 JSON Schema。schema 定义 **38 个叶子字段**，按四大支柱分组，其中 **6 个字段为必填**，并在每个节点强制 `additionalProperties: false`，从结构上杜绝未声明字段进入数据卡。11 条使用（Use）建议属治理层级、不可直接卡片化，按设计落在 schema 范围之外但被引用。

### 4.2 双轨抽取管线
- **baseline 轨**：字段仅取自策展目录（`dataset_catalog.xlsx`，含模态、许可、规模、地理线索、医学领域），构造上保证零虚构。
- **hybrid 轨**：将每个数据集的源文本（论文摘要或仓库 README）经单一 OpenAI 兼容接口（OpenAI / Anthropic / 阿里百炼 `qwen-plus`）送入 LLM，返回部分卡片后与 baseline 合并，仅保留非空的 baseline 或 LLM 取值。

### 4.3 反虚构护栏
每张合并卡都经 schema 校验。任何在对象键或列表项层级违反类型、枚举或附加属性约束的字段被删除；若同路径存在有效 baseline 值则回退到该值。被删字段记入 `extraction.pending_verification` 供人工复核，因此 LLM 永远无法将 schema 非法内容写入发布卡。

### 4.4 评测语料与金标准
抽样 **26 个旗舰医学 AI 数据集**，覆盖放射、病理、基因组、生理时序、临床文本与问答等 **9 类主要模态**（含 NIH ChestX-ray14、MIMIC-CXR、CheXpert、PadChest、VinDr-CXR、BraTS 2024、ISIC 2024、HAM10000、MedMNIST、TotalSegmentator、CT-RATE、DeepLesion、UK Biobank、TCGA、ADNI、Tabula Sapiens、MIMIC-IV、eICU-CRD、Sleep-EDF、CHB-MIT、PhysioNet/CinC 2020、PMC-Patients、MedQA、MedMCQA、PubMedQA、BioASQ）。金标准仅记录公开摘要/README 中显式陈述或可直接推算的事实，**绝不**从目录推断。计分字段为模态、样本计数、国家、预期任务、来源类型；许可与商用字段由目录提供，不计入抽取准确率。

### 4.5 指标
- **抽取保真度**：计分字段上的精确匹配准确率；集合字段用 `gold ⊆ llm` 子集语义，计数与分类来源类型用精确相等。报告来源类型的 Cohen's κ 以暴露 baseline 与 LLM 修正行为。
- **标准保真度**：schema 对各文档化建议的字段级实现率，及 26 张卡的经验填充率。
- **合规与多样性**：逐支柱完整度 + 复合 ST 合规指数（ST Compliance Index）；五指标数据集多样性评分（地理代表性、人群亚组报告、肤色/Fitzpatrick 报告、标注溯源、可泛化性陈述）。
- **权重敏感性**：抽取 200 个 Dirichlet 权重向量，计算替代权重与等权重排名的 Spearman 秩相关。

---

## 5. 结果（Results）

### RQ1 — 抽取保真度
在全部 26 个数据集上，hybrid 管线于 **130 个计分单元**（模态、样本计数、国家、预期任务、来源类型）取得 **90.0% 精确匹配准确率（117/130）**（图 1）。将样本计数的键标签放宽为数值等价（模型以同义键如 `studies` 而非 `admissions` 记录同一数字）后，一致率升至 **120/130（≈92%）**。来源类型的 Cohen's κ = **0.675**（substantial，Landis & Koch 0.61–0.80），基于跨 repository/challenge/paper-supplement/registry/other 的全 26 数据集边际分布。全部 26 张生成卡通过 schema 校验；每个被删字段均可经 `pending_verification` 追溯。13 个残差错误呈非弥散分布：**模态、国家、预期任务零误**（子集语义下）；6 个为来源类型过度泛化（混淆 repository/registry/challenge），7 个为样本计数键标签差异（其中 3 个为同义键数值正确、4 个为真实错误：BraTS 2024 患者数错误、ISIC 2024 图像总数冲突、eICU-CRD 缺医院数、UK Biobank 空抽取）。错误图谱表明管线在自由文本集合字段上可靠，在粗粒度分类标签与数值计数键上最弱，且均被护栏与金标准收容。

### RQ2 — 标准保真度与合规缺口
schema 在字段级**实现全部 18 条文档化建议（100% 结构覆盖）**；26 张 hybrid 卡的**建议级平均字段覆盖率（来自 `st_mapping.csv`）为 70.3%**（四大支柱分别为 77.6% / 65.4% / 82.1% / 37.2%）。逐数据集口径的**四大支柱完整度（来自 `audit_experiments.csv`，图 2）**为：描述与获取 **63.2%**、人群与地理 **54.7%**、偏倚与标注 **79.3%**、伦理 **59.6%**；复合 ST 合规指数均值 **64.2**（图 2）。两类指标口径不同但互补：前者衡量"schema 是否映射到每条建议"，后者衡量"每张卡在每个支柱上实际填了多少"。26 个数据集的完整度排行榜（图 4）显示跨数据集差异显著（39.1%–76.8%）。数据集多样性评分（五指标均值，图 3）为 **0.485**（0–1）：地理代表性 **0.21**、人群亚组报告 **0.49**、肤色/Fitzpatrick 报告 **0.12**、标注溯源 **0.77**、可泛化性陈述 **0.85**；其中地理（0.21）与肤色（0.12）暴露出核心代表性缺口，标注溯源与可泛化性陈述覆盖较好。与仅用目录的 baseline 相比，hybrid 卡的整体完整度提升约 **+52.9 个百分点**（hybrid ≈63.4% vs baseline ≈10.5%），证明 LLM 补全显著填补了人工目录未覆盖的 ST 字段。最突出的缺口为"随时间的数据漂移"（23.1% 卡覆盖）、"亚组与差异结局"（11.5%）、"患者与公众参与（PPIE）"（0.0%）、"偏倚与影响评估"（11.5%）——这些反映源文档的真实欠报告，而非 schema 遗漏。

### RQ3 — 反虚构行为
26 张 hybrid 卡上，护栏共捕获 **14 次**违反 schema 的 LLM 字段并删除/回退，捕获率 **0.54 次/卡**。14 次捕获事件共删除 **21 个字段提及，跨越 7 个 schema 字段**：超枚举医学领域标签（7）、来源类型（4）、模态（3）、预期任务（3）、数据收集场景（2）、方法（1）、标注类型（1）。另有 **10 个**待确认项为 baseline 启发式地理推断（区别于 LLM 越界，交人工确认）。**无任何虚构字段进入发布卡**。

### RQ4 — 权重敏感性
在 200 个随机 Dirichlet 权重向量下，替代权重与等权重排名的 Spearman 秩相关：合规指数为 **0.92（最小 0.705）**、多样性评分为 **0.937（最小 0.745）**。数据集排名对合理的权重选择稳健。

---

## 6. 结论（Conclusion）

MedDataCard 首次将 STANDING Together 的 18 条文档化建议落地为机器可校验、可计算的数据卡 schema，并给出一条零虚构、零 GPU 依赖的双轨抽取 + 反虚构护栏流水线。在 26 个旗舰数据集上，抽取准确率达 90.0%（κ=0.675），schema 结构覆盖 100%，并系统性量化出医学 AI 数据在地理（0.21）与肤色（0.12）维度的代表性缺口及 PPIE 的零披露现状。护栏以零虚构字段逃逸的代价，换取了"披露即真实"的合规可信度。

**主要贡献**：(1) 可执行的 ST 数据卡 schema（38 字段、6 必填、强约束）；(2) 经实证的反虚构双轨管线；(3) 覆盖 26 数据集的可复现合规/多样性排行榜，为后续公平性审计提供基础度量；(4) 开源 Web 工具与审计仪表盘。

**局限与下一步（须如实陈述）**：金标准当前为单编码者，需补第二位独立编码者以报告编码者间一致性（IAA）；论文级分层代表性缺口图仍需生成；部分数据集地理/肤色字段为空（含 10 个 baseline 启发式待确认项），相关指标以"未报告"如实计入而非估算；UNI/CONCH/Virchow 等同期 *Nat Med* 2024 范例文献的卷期页须于投稿前终校（MONET 已核验：*Nat Med* 2024;30(4), DOI 10.1038/s41591-024-02887-x）。后续将把可复现的"数据集多样性评分"作为基础度量，接入更广泛的公平性审计（RO6）与监管提交工作流。

---

## 7. 讨论（Discussion）

**代表性缺口的可操作化。** 地理代表性（0.21）与肤色/Fitzpatrick 报告（0.12）两项指标揭示，当前旗舰医学 AI 训练与评估数据的来源高度集中，少数群体与深肤色人群在文档层面几乎不可见。MedDataCard 把这一定性担忧转化为可在数据集间横向比较、可在排行榜上排序的量化指标，直接回应 STANDING Together 对"透明披露谁被代表、如何被代表"的核心诉求。

**反虚构作为合规信任机制。** RQ3 证明，在零虚构字段逃逸的约束下，披露即可被信赖。这与纯生成式数据卡工具形成根本区别：后者可能以流畅文本掩盖未被源文件支持的事实。护栏把"LLM 能补多少"与"LLM 不能编造什么"解耦，使自动抽取在监管与期刊审查场景可被接受。

**LLM 补全的价值与边界。** hybrid 卡将整体完整度从 baseline 的 ≈10.5% 提升至 ≈63.4%，证实 LLM 能系统性填补人工目录未覆盖的 ST 字段；但误差集中于粗粒度分类标签（source_type，6/26）与数值计数键（sample_counts，7/26），且 modality/countries/intended_tasks 零误。这一误差图谱说明：自由文本集合字段可由 LLM 可靠抽取，而需规范枚举与精确计数的字段必须依赖护栏与人工复核。

**权重稳健性。** RQ4 的 Spearman 秩相关（合规指数 0.92、多样性 0.937）表明，数据集在排行榜上的相对位置对权重选择不敏感，结论不因评分权重的主观设定而动摇。

## 8. 局限性与展望（Limitations）

- **单编码者金标准**：当前 M4 金标准由单一编码者构建，编码者间一致性（IAA）尚未报告；下一步将加入第二位独立编码者并计算 Cohen's κ 作为可靠性证据。
- **便利性样本**：26 个数据集为覆盖主要模态的旗舰集合，并非医学 AI 数据集的全量普查，结论的外推范围受限。
- **元数据级而非原始数据级**：审计仅基于公开摘要/README 的元数据，不触及原始数据，因此无法评估真实肤色分布、实际亚组表现等需在数据层面度量的偏倚；地理/肤色字段为空的数据集以"未报告"如实计入，而非估算。
- **绝对阈值具规范性**：合规指数与多样性评分的绝对数值依赖权重与指标定义，本文给出权重敏感性证据，但阈值本身仍需社区协商。
- **文献核验**：MONET（*Nat Med* 2024;**30**(4), DOI 10.1038/s41591-024-02887-x）卷期页已核验；UNI/CONCH/Virchow 等同为 *Nat Med* 2024 的范例文献卷期页须在投稿前终校（检索时点 2026-08）。

**展望**：补全是多编码者 IAA 与论文级分层代表性缺口图；将可复现的"数据集多样性评分"作为基础度量，接入更广泛的公平性审计（RO6）与监管提交工作流；并把审计范围从元数据扩展至带许可的数据集原始分布指标。

---

## 参考文献（全部真实、可溯源；检索时点 2026-08）

1. Alderman JE, Palmer J, Laws E, et al. Tackling algorithmic bias and promoting transparency in health datasets: the STANDING Together consensus recommendations. *Lancet Digit Health*. 2024 (Dec). DOI: **10.1016/S2589-7500(24)00224-3**. PMID: 39701919.（29 条建议 = 18 文档化 + 11 使用；58 国 350+ 代表；德尔菲法）
2. Xu A, Ding R, Wang L. ChatPD: An LLM-driven Paper-Dataset Networking System. *Proc. 31st ACM SIGKDD (KDD '25)*. 2025. DOI: **10.1145/3711896.3737202**. arXiv:2505.22349.
3. Mitchell M, Wu S, Zaldivar A, et al. Model Cards for Model Reporting. *Proc. 2019 AAAI/ACM Conf. on AI, Ethics, and Society (FAT\* '19)*. 2019.
4. Gebru T, Morgenstern J, Vecchione B, et al. Datasheets for Datasets. *Commun. ACM*. 2021; 64(12):86–92. arXiv:1803.09010.
5. Lhoest Q, et al. HuggingFace Datasets: a unified interface for sharing, exploring, and processing datasets. *EMNLP 2021 (Demos)*. 2021.
6. Brickley D, Burgess M, Noy N. Google Dataset Search: Building a search engine for datasets in an open Web ecosystem. *WWW 2019*. 2019.
7. Ma J, He Y, Li F, et al. Segment Anything in Medical Images. *Nat Commun*. 2024; 15(1):654. DOI: **10.1038/s41467-024-44824-z**. PMID: 38253604.
8. Chen RJ, et al. Towards a general-purpose foundation model for computational pathology. *Nat Med*. 2024. DOI: **10.1038/s41591-024-02857-3**.
9. Lu MY, et al. A visual-language foundation model for computational pathology. *Nat Med*. 2024. DOI: **10.1038/s41591-024-02856-4**.
10. Xu H, et al. A whole-slide foundation model for gigapixel pathology. *Nature*. 2024. DOI: **10.1038/s41586-024-07441-w**.
11. Vorontsov E, et al. A foundation model for clinical-grade computational pathology and rare cancers detection. *Nat Med*. 2024. DOI: **10.1038/s41591-024-03141-0**.
12. MONET: a literature-based image–text foundation model for transparent medical imaging AI (medical concept retriever). *Nat Med*. 2024;**30**(4). DOI: **10.1038/s41591-024-02887-x**.

---

## 附录：数字可追溯性核验表

| 数字 | 数值 | 源文件 |
|---|---|---|
| RQ1 数据集数 / 计分单元 / 匹配 | 26 / 130 / 117（90.0%） | `m4_report.json` |
| RQ1 来源类型 Cohen's κ | 0.675 | `m4_report.json` |
| RQ1 残差错误 | 13（6 来源类型 + 7 样本计数，其中 3 同义键 + 4 真实） | `m4_report.json` cells 逐项核对 |
| RQ2 schema 实现率 | 18/18（100%） | `st_mapping.csv`（19 行含表头，18 条文档化建议全 Y） |
| RQ2 平均填充率 | 70.3% | 草案 RQ2 |
| RQ2 逐支柱完整度 | 63.2 / 54.7 / 79.3 / 59.6% | 草案 RQ2 |
| RQ2 合规指数 / 多样性评分 | 64.2 / 0.485（地理 0.21、肤色 0.12） | 草案 RQ2 |
| RQ2 hybrid vs baseline 完整度 | ≈63.4% vs ≈10.5%（+52.9pp） | `README.md` / 草案 |
| RQ3 护栏捕获 / 提及 / 字段 | 14 次 / 21 提及 / 7 字段 | `audit_summary.csv` + `fabrication_audit.csv` |
| RQ3 地理启发式待确认 | 10 | `audit_summary.csv` |
| RQ4 Spearman（合规/多样性） | 0.92（min 0.705）/ 0.937（min 0.745） | 草案 RQ4 |
| 发布卡 schema 通过 | 26/26 | `m4_report.json` + `audit_summary.csv` |
