# MedDataCard

> 自动生成符合 **STANDING Together** 标准的医学 AI 数据集数据卡（Data Card），并对数据集做元数据级合规审计。
> MVP 聚焦：**ST 数据卡 Schema + 自动生成器（Web）**。审计仪表盘 / 公开排行榜为后续迭代。

[English](#english) | 中文

## 🚀 在线 Demo

已部署到 Streamlit Community Cloud：

[![Open in Streamlit](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://meddatacard.streamlit.app)

无需 API key 即可查看基线数据卡；填写 key 后可用 LLM 从论文摘要补充字段。

## 背景

- **标准**：[STANDING Together](https://www.standingtogether.ai/) 共识（*The Lancet Digital Health* + *NEJM AI*，2024-12-18，DOI `10.1016/S2589-7500(24)00224-3`）——医学 AI 数据集报告与评估的统一标准本体（18 条记录建议，4 大支柱）。
- **问题**：截至目前没有任何自动化工具能生成符合该标准的数据卡，也缺少对现有数据集的系统性合规审计。
- **参考范式**：ChatPD（arXiv:2505.22349，KDD 2025）的「论文–数据集」元数据抽取方法论（仅借鉴方法，目标不同）。
- **审计对象**：`dataset_catalog.xlsx`（26 个医学 AI 数据集，事实基准）。

## 特性

- **机器可读 Schema**：`st_datacard.schema.json`（JSON Schema Draft 2020-12，v0.2），对齐 ST 四大支柱 + `medical_fields` 学科分类。
- **双轨抽取管线**：
  - **基线卡**：仅用 `dataset_catalog.xlsx` 的真实元数据，零 LLM 依赖、零编造。
  - **Hybrid 卡**：基线 + LLM（OpenAI / Anthropic / **阿里云 DashScope**）从论文摘要 / 仓库 README 补充人口、地理、标注、伦理等字段。
- **防编造护栏**：LLM 输出任何不符合 schema 的字段（类型 / 枚举 / 列表项违规）会被自动丢弃或回退基线值，并写入 `extraction.pending_verification`，全程可追溯、不静默造假。
- **抽样验证（M4）**：内置 `evaluate_m4.py`，用人工 gold 标准评估 LLM 抽取准确率与 Cohen's κ。当前在 12 个跨模态数据集上：**字段精确匹配 86.7%，source_type 的 κ = 0.617（substantial）**。
- **批量生成**：`generate_all.py --llm` 一次生成全部 26 张卡（有摘要处 hybrid，无摘要处诚实回退 baseline）。

## 目录结构

```
MedDataCard/
├─ st_datacard.schema.json   # ST 数据卡 JSON Schema v0.2
├─ dataset_catalog.xlsx      # 26 数据集目录（事实基准）
├─ catalog.py                # 读取目录 → 元数据列表 + 模态/地理映射
├─ schema_utils.py           # schema 加载与 JSON Schema 校验
├─ extract.py                # 抽取管线：目录基线卡 + LLM 补充（OpenAI/Anthropic/DashScope，无 key 自动降级）
├─ app.py                    # Streamlit Web 原型（查看/编辑/导出）
├─ generate_all.py           # 批量生成 26 张卡（--llm 开启 hybrid）
├─ evaluate_m4.py            # M4 抽样验证：gold 比对 + Cohen's κ
├─ sources/                  # 12 个数据集的论文摘要/源文本（M4 输入）
├─ gold/                     # 12 个人工 gold 标准（M4 比对基准）
├─ datacards/                # 生成的数据卡示例输出（26 张）
├─ audit_summary.csv         # 跨数据集审计摘要（维度完整度/待核实/地理集中）
├─ requirements.txt
├─ .env.example              # API key 模板（DASHSCOPE / OPENAI / ANTHROPIC）
├─ LICENSE                   # MIT
└─ MedDataCard_MVP_技术方案_PRD.md  # 技术方案 / PRD
```

## 运行

```bash
pip install -r requirements.txt
streamlit run app.py
# 浏览器打开 http://localhost:8501
```

- 选择左侧数据集 → 点击「生成数据卡」。
- **无 LLM API key** 时，自动用 `dataset_catalog.xlsx` 的真实元数据生成**基线卡**（不编造任何字段）。
- 填入 API key + 论文/README 文本后，调用 LLM 补充人口/地理/标注/伦理等字段（hybrid）。

### 配置 API key

复制 `.env.example` 为 `.env` 并填入其一（绝不提交 `.env`）：

```bash
cp .env.example .env
# 编辑 .env：DASHSCOPE_API_KEY=xxx  或  OPENAI_API_KEY=xxx  或  ANTHROPIC_API_KEY=xxx
```

| Provider | 环境变量 | 默认模型 | 端点 |
|---|---|---|---|
| 阿里云 DashScope（百炼） | `DASHSCOPE_API_KEY` | `qwen-plus` | OpenAI 兼容 `https://dashscope.aliyuncs.com/compatible-mode/v1` |
| OpenAI | `OPENAI_API_KEY` | `gpt-4o-mini` | `https://api.openai.com/v1` |
| Anthropic | `ANTHROPIC_API_KEY` | `claude-3-5-sonnet` | 经 OpenAI 兼容层 |

### 批量生成全部 26 张卡

```bash
python generate_all.py            # 仅基线卡
python generate_all.py --llm       # 有摘要处 hybrid，无摘要处基线（需 API key）
```

### 跑 M4 抽样验证

```bash
python evaluate_m4.py dashscope   # 或 openai / anthropic
# 输出：m4_report.json + m4_output/*.json
```

## 设计原则（硬性）

- **不编造**：目录 / LLM 未覆盖的字段留空并写入 `extraction.pending_verification`；凡【待核实】项一律标注。
- **零 GPU 依赖**：元数据级审计仅用 CPU + LLM API。
- **可扩展**：新增数据集只需在 `dataset_catalog.xlsx` 加一行（及可选 `sources/<id>.txt` 摘要），无需改代码。
- **可复现**：所有 LLM 抽取均带 schema 护栏与可追溯的待核实清单。

## 验证结果（M4）

| 指标 | 数值 |
|---|---|
| 精确匹配准确率（60 个可比字段） | 52/60 = 86.7% |
| Cohen's κ（source_type，12 数据集） | 0.617（substantial） |
| 卡片 schema 合法性 | 12/12 通过 |
| ST 维度完整度（hybrid 均值 vs 基线均值） | 62.6% vs 10.5% |

诚实说明：LLM 在事实 / 计数抽取上明显强于基线；`source_type` 等粗粒度枚举是弱项（会过修正），故 κ 未达完美——M4 已量化该偏倚，详见 `m4_report.json`。

## 待办

- [x] ST 数据卡 Schema（v0.2，JSON Schema 校验通过）
- [x] 双轨抽取管线（基线 + LLM hybrid）+ 防编造护栏
- [x] Web 原型（查看/编辑/导出）
- [x] 抽样验证 + Cohen's κ（M4，κ=0.617）
- [x] 批量生成 26 张卡
- [x] 开源到 GitHub
- [ ] 与 ST 官方 checklist 逐条对齐校正 schema
- [ ] 审计仪表盘（偏倚可视化）、公开排行榜

## 部署（Streamlit Community Cloud）

无需本地环境，一键把公开仓库部署成在线 Web 应用：

[![Deploy to Streamlit](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://share.streamlit.io/deploy?repository=github.com/echocheng-y/MedDataCard)

已部署实例：**https://meddatacard.streamlit.app**

步骤：
1. 打开 [Streamlit Cloud](https://streamlit.io/cloud)，用 GitHub 登录并授权。
2. 新建 App，选择仓库 `echocheng-y/MedDataCard`、分支 `main`、主文件 `app.py`，点 **Deploy**。
3. 完成后获得一个公开 URL，任何人可直接打开使用（已通过本地冒烟测试，无 key 时自动降级 baseline 模式）。

本次部署踩坑记录：首次部署时 Streamlit Cloud 需安装 GitHub App 并授权 `MedDataCard` 仓库，否则表单会报 `branch/file does not exist`。

> 如需启用 LLM 抽取：在 App 的 **Settings → Secrets** 中加入
> `DASHSCOPE_API_KEY = "你的key"`（或 `OPENAI_API_KEY` / `ANTHROPIC_API_KEY`）；不配置则自动使用目录基线元数据生成。

## 许可证

[MIT](LICENSE)。

---

## English

**MedDataCard** automatically generates [STANDING Together](https://www.standingtogether.ai/)-compliant data cards for medical-AI datasets and runs metadata-level compliance audits.

[![Open in Streamlit](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://meddatacard.streamlit.app)

- **Schema**: `st_datacard.schema.json` (JSON Schema Draft 2020-12, v0.2) aligned with ST's four pillars + `medical_fields` taxonomy.
- **Pipeline**: a catalog-only **baseline** card (zero fabrication) plus an LLM **hybrid** card (OpenAI / Anthropic / Alibaba **DashScope**) that fills demographics / geography / annotation / ethics fields from paper abstracts or repo READMEs.
- **Anti-fabrication guardrail**: any LLM field violating the schema (type / enum / list items) is dropped or reverted to the baseline and logged in `extraction.pending_verification`.
- **Validation (M4)**: `evaluate_m4.py` compares LLM output against a human gold standard. On 12 cross-modality datasets: **86.7% exact-match accuracy, Cohen's κ = 0.617 (substantial)** on `source_type`.

```bash
pip install -r requirements.txt
streamlit run app.py
cp .env.example .env   # add DASHSCOPE_API_KEY / OPENAI_API_KEY / ANTHROPIC_API_KEY
python generate_all.py --llm     # generate all 26 cards (hybrid where abstracts exist)
python evaluate_m4.py dashscope  # run the M4 validation harness
```

Licensed under [MIT](LICENSE).
