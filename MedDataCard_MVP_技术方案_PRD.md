# MedDataCard MVP 技术方案 / PRD

> 版本：v0.1（规划草案，待评审）　日期：2026-08-18　状态：Draft
> 关联文件：`st_datacard.schema.json`（数据卡 schema）、`dataset_catalog.xlsx`（26 数据集目录）

---

## 1. 背景与问题

**标准空白。** STANDING Together 共识（The Lancet Digital Health + NEJM AI，2024-12-18，DOI: `10.1016/S2589-7500(24)00224-3`）为医学 AI 数据集的报告与评估提供了统一标准本体，但截至目前**没有任何自动化工具**能生成符合该标准的数据卡，也没有对现有数据集做系统性合规审计（已核实）。

**监管与期刊压力。** FDA 已批准 900+ AI 医疗设备，多数未报告训练数据 / 架构；监管与顶刊对「训练数据披露」要求趋严，工程与合规缺口明确。

**参考范式（ChatPD）。** ChatPD（arXiv:2505.22349，KDD 2025，[code](https://github.com/ChatPD-web/ChatPD) / [web](https://chatpd-web.github.io/chatpd-web/)）的核心是「论文–数据集」知识网络。MedDataCard **借鉴其方法**——如何把非结构化论文 / 仓库元数据抽取为结构化字段的管线与 schema 表达——但**目标不同**：ChatPD 建网络，MedDataCard 做 ST 合规数据卡生成与审计。

**算力现实。** 本地机器 RTX 4080S ×2（32GB，无 NVLink）+ 50GB 可扩存储。本项目**零 GPU 依赖**：元数据级审计仅用 CPU + LLM API；若本地部署抽取模型，单卡 4080S(16GB) 经 4-bit QLoRA 可跑 7B。存储预算 < 20GB。

---

## 2. 目标

### 2.1 产品目标
构建一个 Web 工具 **MedDataCard**，自动生成符合 STANDING Together 标准的数据卡，并对医学 AI 数据集做元数据级合规审计。

### 2.2 MVP 范围（本次必须做）
- **ST 数据卡 JSON Schema**：机器可读，约 30–40 字段，分必填 / 可选，覆盖 ST 六大维度。
- **LLM 元数据抽取管线**：论文 PDF / 仓库 README → LLM → 填充数据卡 → 结构化 JSON。
- **Web 呈现**：可运行 Web 应用，查看 / 编辑 / 导出（JSON / Markdown）数据卡。
- **抽样验证**：3–5 个数据集跑通端到端流程 + 人工复核（κ）。

### 2.3 不在本次范围（后续迭代）
审计仪表盘（偏倚可视化）、公开排行榜、全 26 数据集自动化审计、模型侧公平性审计（对应 P3 FairMed-Audit）。

### 2.4 成功指标（MVP）
- 数据卡 Schema 通过 JSON Schema 校验，覆盖 ST 六大维度。
- 端到端管线对抽样数据集的字段抽取准确率 ≥ 80%，人工复核 κ ≥ 0.6。
- Web 应用本地可启（一条命令），可完成「载入数据集 → 生成 → 编辑 → 导出」闭环。

---

## 3. 用户与用户故事

**研究者 / 数据集发布者**：作为论文或数据集发布前的合规自查工具，快速生成 ST 合规数据卡。
> 作为医学 AI 研究者，我希望输入数据集论文 / 仓库链接就能自动生成 ST 数据卡，以便投稿前满足期刊的数据披露要求。

**审稿人 / 监管评估者**：快速比对多个数据集的多样性与偏倚情况。
> 作为审稿人，我希望浏览某数据集的数据卡，以便判断其人群 / 地理代表性是否充分。

**Meta 研究者（本项目自身）**：用工具对 26+ 数据集做系统性审计，识别系统性偏倚（如 90%+ 美欧单中心）。
> 作为审计者，我希望批量生成数据卡并导出，以便汇总成审计排行榜与方法稿。

---

## 4. 功能清单（MVP）

| 编号 | 功能 | 优先级 | 说明 |
|---|---|---|---|
| F1 | ST 数据卡 Schema 定义与校验 | P0 | `st_datacard.schema.json`，支持 JSON Schema 校验 |
| F2 | 论文 / README 采集 | P0 | 按 `dataset_catalog.xlsx` 链接抓取 PDF / README 文本 |
| F3 | LLM 元数据抽取 | P0 | 调用 LLM API 抽取字段 → 填充 JSON；预留本地 7B 接口 |
| F4 | 人工复核与 κ 统计 | P1 | 标注抽样字段人工判定，计算一致性 κ |
| F5 | 数据卡查看 | P0 | Web 卡片 / 列表展示（参考 ChatPD Web） |
| F6 | 数据卡编辑 | P1 | 网页内修正抽取错误字段 |
| F7 | 导出 | P0 | 导出 JSON / Markdown |
| F8 | 待核实标记 | P0 | 无法确认字段标记为 `pending_verification`，禁止编造 |

---

## 5. 流程说明（端到端）

```
dataset_catalog.xlsx (26 数据集)
        │  按链接采集
        ▼
论文 PDF / 仓库 README 文本语料
        │  F3: LLM 抽取（GPT/Claude API，预留本地 7B）
        ▼
ST 数据卡 JSON  ──校验──▶ st_datacard.schema.json
        │  F5/F6: Web 查看 / 编辑
        ▼
导出 JSON / Markdown  +  F4 人工复核（κ）
```

**异常流（If）：**
- If 论文链接失效或需凭证（如 MIMIC DUA），then 系统跳过原文抓取，仅用目录元数据 + README，并在 `pending_verification` 标记缺失项。
- If LLM 对某校验字段无证据，then 该字段留空并写入 `pending_verification`，不得编造。
- If 抽取结果未通过 JSON Schema 校验，then 系统拒绝入库并提示具体失败字段。

---

## 6. 交互说明（Web）

- **首页 / 列表**：展示已生成数据卡的数据集清单（卡片式，含名称、模态、国家、许可证徽章），参考 ChatPD Web 的卡片网格。
- **数据卡详情**：分区展示六大维度（人口 / 地理 / 模态 / 标注 / 伦理 / 偏倚），`pending_verification` 字段以警示色标注。
- **生成入口**：粘贴论文 / README 链接或文本 → 触发抽取 → 进度提示 → 跳转详情。
- **导出**：详情页提供 JSON / Markdown 下载。

---

## 7. 数据模型

核心实体为 ST 数据卡，结构见 [`st_datacard.schema.json`](./st_datacard.schema.json)，顶层分组：

- `metadata`：标识、来源类型、论文 / 仓库链接、目录溯源
- `population`：年龄 / 性别 / 种族 / 纳入排除 / 共病 / 脆弱人群
- `geography`：国家 / 大区 / 单多中心 / 采集时段 / 机构数
- `modality`：模态 / 范围 / 设备 / 格式 / 样本量
- `annotation`：标注方式 / 方法 / 标注者 / 标签噪声 / 指南
- `ethics`：知情同意 / IRB / 许可证 / DUA / 隐私 / 商用
- `bias_and_limitations`：已知局限 / 代表性 / 长尾 / 泛化性 / 亚组 / 缺失
- `tasks_and_use`：适用任务 / Benchmark / 禁用任务
- `medical_fields`：医学研究领域划分（基础医学 / 临床医学 / 中医学 / 中药学 / 妇产科学 / 影像学 / 内科学 / 外科学 / 其他），用于跨数据集按学科横向归类与审计（独立于 ST 六大报告维度）
- `extraction`：抽取方式 / 置信度 / 人工复核 / κ / 待核实（审计溯源）

**字段规模**：约 38 个叶子字段，必填项 6 个（schema_version / dataset_id / dataset_name / modalities / license / extraction）。

---

## 8. 非功能需求

- **零 GPU 依赖**：抽取以 LLM API 为主；本地 7B 为可选。
- **存储 < 20GB**：论文 PDF + 元数据 + 代码 + 静态站点。
- **开源**：优先开源技术栈，最终开源到 GitHub。
- **可扩展**：新增数据集仅需提供链接 / 文本，无需改代码。

---

## 9. 验收标准（EARS）

- **Ubiquitous**：系统应始终对输出的每一条数据卡执行 JSON Schema 校验，未通过不得入库。
- **Event-driven**：当用户提交论文 / README 链接时，系统应在 60 秒内返回结构化数据卡草稿（API 可用前提下）。
- **Unwanted**：若 LLM 对某字段无证据或来源链接失效，则系统应将该字段留空并写入 `pending_verification`，而非编造。
- **State-driven**：当数据集处于「需凭证（DUA）」状态时，系统应仅基于目录元数据 + 公开 README 生成数据卡并标记缺失项。
- **Optional**：若用户配置本地 7B 抽取模型，则系统应在无外部 API 时仍可离线抽取。

---

## 10. 里程碑（建议）

| 阶段 | 内容 | 产出 |
|---|---|---|
| M1 | Schema 定稿 + 校验脚本 | `st_datacard.schema.json` |
| M2 | 采集 + LLM 抽取管线 | 抽取 CLI / 服务 |
| M3 | Web 应用（查看 / 编辑 / 导出） | 可运行站点 |
| M4 | 抽样验证 + κ 报告 | 验证报告 |
| M5 | README + 开源 | GitHub 仓库 |

---

## 11. 风险与依赖

- **ST 标准对齐（已缓解 ✅）**：Schema 已升级至 v0.2，逐条对齐 STANDING Together 『健康数据集文档记录推荐』（18 条，1.1a–1.4c），四大支柱映射如下；剩余风险为「ST 强制要求显式报告未知项」需在抽取/人工复核环节落实。

  | ST 支柱 | ST 条目 | Schema 分组 |
  |---|---|---|
  | ① 数据集描述与访问 | 1.1a–1.1c（摘要/身份访问/目的） | `metadata` |
  | ① 数据起源与抽样 | 1.1d–1.1f（起源/抽样/时间偏移） | `data_origin` |
  | ② 群体构成与属性 | 1.2a–1.2c（构成/属性记录/风险群体） | `population` |
  | ② 地理与采集 | （采集设置/时段） | `geography` |
  | ③ 偏倚/误差/局限 | 1.3a–1.3f（局限/修改/偏倚源） | `bias_and_limitations` |
  | ④ 伦理治理与参与 | 1.4a–1.4c（治理/PPIE/影响评估） | `ethics` |
  | （分类标签，非 ST） | — | `medical_fields` |

- **抽取准确率风险**：自动化标签噪声数据集（如 ChestX-ray14 NLP 标签）可能干扰抽取，需人工复核兜底。
- **DUA 限制**：MIMIC / eICU 等需凭证，MVP 仅元数据级处理，不触碰原始数据。
- **依赖**：LLM API（GPT / Claude）、PDF 解析库、前端框架（Streamlit）。

---

## 12. 参考与引用

- STANDING Together 共识（Lancet Digital Health + NEJM AI, 2024-12-18）— https://doi.org/10.1016/S2589-7500(24)00224-3
- ChatPD（KDD 2025, arXiv:2505.22349）— https://arxiv.org/abs/2505.22349 ｜ [code](https://github.com/ChatPD-web/ChatPD) ｜ [web](https://chatpd-web.github.io/chatpd-web/)
- 审计对象：`dataset_catalog.xlsx`（26 数据集，事实基准）
- 上游方案：`项目推荐_完整方案.docx`（P1 MedDataCard 章节）
