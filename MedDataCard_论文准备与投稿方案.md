# MedDataCard 论文准备方案（优化指令 + 投稿 Venue）

> 综合自：项目推荐完整方案.docx、dataset_catalog.xlsx（26 数据集）、ChatPD（arXiv:2505.22349, KDD'25 ADS）、STANDING Together（Lancet Digital Health + NEJM AI, 2024-12-18）、本地 MedDataCard MVP 现状。
> 由实证研究团「选题锐」完成新颖性审计与期刊路由，主理人汇编。

---

## 一、优化后的研究指令 / Statement of Work（SOW）

### 1. 一句话定位
MedDataCard **不是**「论文—数据集」发现网络（那是 ChatPD 的目标），而是把刚发布的权威治理标准 STANDING Together（ST）「可执行化」为机器可读 schema、并据此对真实医学 AI 训练数据集做**元数据级合规差距审计**的开源工具与测量研究。

### 2. 研究问题与贡献点声明
- **RQ1（保真/有效性）**：在「零编造」约束下，schema 驱动的 LLM 增强抽取管线能否高保真地从论文摘要/README 生成符合 ST 建议的数据卡？与纯元数据基线相比，字段级准确率、schema 合法性、反编造率如何？
- **RQ2（合规差距/测量）**：当前被广泛使用的旗舰医学 AI 数据集在多大程度上满足 ST 的文档与包容性建议？系统性短板集中在哪些维度（地理、人口、肤色/Fitzpatrick、标注来源、泛化性声明）？
- **RQ3（增量消融）**：LLM 增强相比纯元数据基线，能在不引入编造的前提下把 ST 维度完整度提升多少？（把现有 10.5%→62.6% 实证扩展为可泛化结论）

- **C1（本体/标准可执行化）**：首次将 ST 共识转化为机器可读、可校验的 JSON Schema（st_datacard.schema.json, Draft 2020-12），含 4 大支柱 + medical_fields 学科分类、~38 叶子字段、6 必填，使「软标准」变成「可计算、可校验、可批量审计」的执行件。
- **C2（方法/反编造管线）**：双轨抽取（零 LLM 基线 + LLM 增强 hybrid）+ 反编造护栏（schema 校验失败即丢弃/回退基线、写入 pending_verification、全程可追溯），在合规场景把「可信自动化」作为 load-bearing 设计原则，并量化护栏捕获的编造尝试。
- **C3（测量/领域状态）**：首个对 26 个跨模态旗舰医学 AI 数据集的元数据级系统性合规审计，量化 representation gaps，作为「领域现状」经验证据（也是后续公平性审计 P3 / RO6 的「数据集多样性评分」基础）。
- **C4（工具/可复现）**：开源、零 GPU、已部署的 Web 工具 + 可复现包，任何数据发布者都能一键生成 ST 合规卡并自评。

### 3. 与 ChatPD 的差异定位（核心防线）

| 维度 | ChatPD (KDD'25 ADS) | MedDataCard |
|---|---|---|
| 目标构造 | 论文↔数据集的关系网络（发现/推荐） | 数据集对治理标准的合规程度（审计/测量） |
| 核心产出 | 实体解析后的 paper-dataset graph | 符合 ST 的 data card + 合规差距指标 |
| 评估基准 | 内部 precision/recall（实体链接） | 外部金标准本体（ST 建议逐条映射） |
| 设计约束 | 抽取准确性为主 | 反编造是 load-bearing（合规工具不可虚构） |
| 影响主张 | 提升数据集可发现性 | 暴露偏倚、提升报告透明度与可复现 |
| 方法亮点 | Graph Completion & Inference | Schema-driven 校验 + 反编造护栏 + 合规差距量化 |

一句话差异化：**ChatPD 回答「这篇论文用了哪些数据集」，MedDataCard 回答「这些数据集到底代表/不代表谁、是否经得起治理标准检验」。** 两者仅共享「非结构化文本→结构化字段」的抽取方法论起点，终点与目标构造根本不同。Related Work 需显式给出此对照表，并在引言用「我们不是又一个数据集发现系统」preempt reviewer 的「ChatPD 换皮」质疑。

### 4. 范围边界（In / Out）
- **In scope（P1 本篇）**：26 个数据集（dataset_catalog.xlsx 为事实基准）生成 ST 卡 + 合规审计；元数据级抽取（不触发 DUA）；反编造护栏的方法论贡献与量化；「数据集多样性评分/ST 合规指数」指标定义与首版计算；工具本身（schema + 管线 + Web）作为可复现交付物。
- **Out of scope（留 P2/P3/P4）**：因果推断、ICU 干预（P2）；基于模型输出的公平性审计（P3/FairMed-Audit，基于本篇多样性评分）；跨模态统一检索（P4/UniRetrieval）；进入 DUA 受保护数据做像素/记录级审计（未来工作）。

### 5. 需补充的实验/分析（MVP → 可投稿）
1. **ST 官方建议逐条映射表**：把 ST 文档类建议（注意已发表版 29 条，分 Documentation/Use；内部「18 条记录建议」需核对口径）逐条映射到 schema 字段，标注 coverage（已实现/部分/未覆盖），证明工具「标准保真度」。
2. **扩大 M4 抽样验证**：当前 12/26 → 跨模态分层抽样（目标 ≥20，理想覆盖 26），补第二人类编码员做 inter-annotator agreement，分 4 支柱报告完整度而非仅总体。
3. **反编造量化实验**：统计 pending_verification 触发量（按字段）、护栏 precision/recall（人工抽检被丢弃字段是否确属虚构/超纲）、false-negative（漏网编造）。
4. **合规差距审计主结果**：26 数据集 ST 维度完整度分布、按模态/地区/标注来源分层的 representation gap 图；与已审计基础模型（MedSAM/UNI/CONCH 等）所用训练集衔接，说明「数据偏倚如何向上游传播」。
5. **多样性评分定义与稳健性**：明确地理覆盖 / 人口报告（年龄·性别·种族）/ 肤色(Fitzpatrick)覆盖 / 标注来源(专家 vs NLP) / 泛化性声明 各子指标操作化与加权，给 composite ST Compliance Index，做敏感性分析（权重变动下排名稳定性）。
6. **可复现包**：Docker、一键运行、样例输入、26 张生成卡为补充材料、schema、验证脚本（MIT 许可已有）。

### 6. 目标产出（Deliverables）
- 一篇投稿级论文（首选 Scientific Data；备选 npj Digital Medicine / Lancet Digital Health / KDD ADS）
- 26 张 ST 合规数据卡（机器可读 JSON + 人类可读视图）
- st_datacard.schema.json v0.3（含 ST 映射文档）
- 审计仪表盘 / 排行榜（每数据集合规完整度、可排序、差距高亮）
- 可复现包（GitHub 已开源，补 Docker + 验证脚本）
- 「数据集多样性评分」 v1 规范文档（供 P3 复用）

### 7. 成功标准
- 论文被目标期刊/会议送审且获「可修回」级评审（非 desk reject）
- schema 通过 ST 官方建议逐条映射审查
- M4 扩到 ≥20 数据集且字段精确匹配 ≥85%、schema 合法性 100%
- 反编造护栏有量化证据（pending_verification 统计 + 抽检）
- 工具可被第三方一键复现

---

## 二、新颖性审计与投稿 Venue 推荐

### B.1 新颖性审计（真实增量）
- **相对 ChatPD**：见 §3 对照表。增量 = 把「抽取」升级为「对权威治理标准的合规测量」，并引入 ChatPD 不需要的反编造设计约束（合规卡不可虚构）。这是方法 + 测量 + 治理三重增量，而非领域迁移。
- **相对 ST 标准生态**：ST 于 2024-12-18 发布，目前没有任何自动化工具把它变成机器可读 schema 或做批量审计。ST 自身是「建议/清单」，不是可执行件。MedDataCard 填补「标准 → 可执行 → 可审计」缺口，是 ST 生态第一个 tooling。
- **相对通用 data card 工作**（Model Cards / Datasheets for Datasets / HuggingFace）：那些是通用模板 + 人工填写；MedDataCard 是医学 AI 专用 + 自动化 + 对齐具体共识标准 + 自带反编造与审计。差异明确。
- **避免「ChatPD 换皮」叙事**：(1) 引言 preempt 式对比 ChatPD；(2) 贡献重心放 C1/C2/C3（标准可执行化 + 反编造 + 合规差距测量），而非「我们也能从论文抽字段」；(3) 用 ST 外部金标准作评估基准，而非内部 precision/recall——从方法论上区别于 ChatPD。

### B.2 候选 Venue 对比（跨谱系）

| 候选 | 类型 | 声誉/IF | 为什么 fit | 最看重 | 需补强 | 难度 |
|---|---|---|---|---|---|---|
| **Scientific Data** ★首选 | Nature Portfolio 期刊（OA） | IF~6.9，中科院2区 | ST 本质是「数据集报告标准」，本刊正是发表「标准/数据集可执行化 + 描述数据集」的首选；26 卡+schema+工具=典型 Data Descriptor/扩展 Article | 可复现性、工具真能用、schema 经校验、FAIR 合规 | ST 逐条映射表；M4≥20；Docker+脚本；how-to-use/cite；伦理声明（仅元数据级，不触 DUA） | 中 |
| **npj Digital Medicine** ▲冲高 | Nature Portfolio 期刊 | IF~15 | 爱发 state-of-the-field 实证；26 数据集 representation gap 正合其口味 | 发现的临床/方法学显著性、改变实践、不夸大 | 审计作主叙事+强故事线；衔接基础模型审计；更强统计；可能需行动呼吁框架 | 高 |
| **KDD ADS** ▲CS 能见度 | CS 顶会（ChatPD 同轨） | 顶会 | 定位为已部署治理/测量系统+真实影响；schema 作为知识工件、live 服务、领域级审计 | 真实部署系统、可扩展管线、实证评估、applied 影响 | 部署指标（卡数/用户/API）；反编造作 CS 贡献；可扩展证据；差异化必须过硬 | 高 |
| **JAMIA** △稳妥备选 | 医学信息学旗舰期刊 | IF~7–8 | ST 是健康信息学报告标准；其 Data&Resource/Methods 接收「标准实现+工具+资源」 | 信息学严谨、标准对齐、社区可用、对照标准评估 | 标准机构引用/认可；清晰信息学框架；可选小型可用性研究 | 中 |

备选提及：Lancet Digital Health（通讯/简报，与 ST 同源期刊，审计故事极强可投 correspondence）；AMIA Annual Symposium（dataset/resource + methods track）；CHI/CSCW（若走 HCI 角度——人在环标准化、可信自动化合规，优先级低）。

### B.3 明确首选推荐与理由
**首选：Scientific Data。**
1. 选题与期刊范围几乎完美对齐（标准可执行化 + 数据集描述 + 工具）；
2. Nature 品牌 + 合理 IF，作为博士首篇「快赢」风险收益比最优；
3. 已具备较强 MVP，所需补强可控（映射表 + 扩样 + 可复现包）；
4. 在此建立「数据集多样性评分」为可复用指标，为 P3 公平性审计铺路，战略协同最强。

**升级路径**：若审计主结果故事线足够强（representation gap 触目且衔接基础模型），改投/加投 npj Digital Medicine（full article）或 Lancet Digital Health（correspondence）。
**CS 能见度路径**：若重视 CS 社区且能坐实部署指标与差异化，投 KDD ADS（叙事从「抽取」翻转为「治理/测量系统」）。
**稳妥备选**：JAMIA（若 Scientific Data 被拒且想保信息学主场）。

### B.4 论文准备清单 + 时间线
关键工作（MVP → 可投稿）：
1. ST 官方建议逐条映射表（核对 18 vs 29 口径，标注 coverage）——工具「标准保真度」证据。
2. 扩大 M4 至 ≥20（理想 26）跨模态分层抽样；补第二人类编码员 IAA；分 4 支柱报告。
3. 反编造量化：pending_verification 统计（按字段）+ 抽检护栏 precision/recall + false-negative。
4. 合规差距审计主结果：26 数据集 ST 完整度分布 + 分层 representation gap 图 + 与 MedSAM/UNI/CONCH 训练集衔接。
5. 多样性评分 v1：地理/人口/肤色/标注来源/泛化性 子指标操作化 + composite ST Compliance Index + 权重敏感性。
6. 审计仪表盘/排行榜（每数据集合规完整度、可排序、差距高亮）——既供论文图，也促采用。
7. 可复现包：Docker + 一键运行 + 样例 + 26 卡补充材料 + schema + 验证脚本（MIT 已有）。
8. 局限与威胁诚实讨论：仅元数据级（不触 DUA）、LLM 抽取受限于摘要/README、NLP 标签噪声未独立验证、schema v0.2→v0.3 演进、26 数据集为便利样本等。
9. Related Work 精确对照表（ChatPD / Model Cards / Datasheets / HuggingFace / ST 生态无工具）——即 B.1。
10. 写作叙事：Scientific Data 主线「工具+标准」；npj/Lancet 主线「审计发现」。

**建议节奏（快赢导向，MVP 已存在）**：
- **M1–M2**：ST 映射表 + 扩 M4 至 ≥20 + 反编造量化 + 多样性评分定义。
- **M2–M3**：审计主结果 + 仪表盘 + 基础模型衔接 + 可复现包 + 局限讨论。
- **M3–M4**：写稿，首选投 Scientific Data（Data Descriptor/Article）；同步挂 arXiv 预印本。
- **M4+**：若投 npj/Lancet，补强审计故事线 + 基础模型衔接，晚 1–2 月加投；若走 CS，对齐 KDD ADS 截稿（通常前一年 9–10 月），准备部署指标。
- **并行**：保持工具迭代与采用（用户/星标/集成）作为 KDD 与 npj 的「影响」证据。

---

## 三、必须核实的关键口径（重要）
- **ST 建议条数口径**：项目 README/PRD 写「18 条记录建议、4 大支柱」，但 STANDING Together 已发表版为 **29 条共识建议**（分 Documentation / Use 两部分）。「18 条」可能是文档子集或早期草稿口径——**在动笔 C1 贡献与 schema 映射前必须先核对**，否则审稿人会直接质疑标准保真度。
- 其他「【待核实】」标注（如部分文献卷期页、TITAN 卷期）也建议在写稿前一并核对。
