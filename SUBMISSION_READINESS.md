# MedDataCard 投稿就绪清单（Submission Readiness Checklist）

> 生成日期：2026-08-20｜目标期刊：npj Digital Medicine（可平移 Lancet Digital Health / Scientific Data）
> 本清单由自动化审计 + 人工核验生成。所有研究数字均来自已验证口径，无编造。

## 一、交付文件清单（均已推送 GitHub `main`）

| 文件 | 类型 | 状态 |
|---|---|---|
| `MedDataCard_manuscript_submission.md` | 英文投稿稿（主投件） | ✅ em-dash 已清零 |
| `MedDataCard_manuscript_draft.md` | 中文完整草稿（内部） | ✅ 图1–7 齐备 |
| `MedDataCard_submission_package.md` | 投稿包（Cover Letter / Highlights / Scientific Data 摘要 / Lancet / Scientific Data 专属投稿信） | ✅ |
| `figures/fig_*.png`（7 张） | 图1–7 | ✅ 全部生成 |
| `app.py` | Streamlit demo（Tab3 嵌入图1–7） | ✅ 已部署 |
| `IAA_PROTOCOL.md` + `compute_iaa.py` + `generate_coder_b_template.py` + `coder_b_template/` | 第二位编码者 IAA 协议 | ✅ 协议就绪，数字 PENDING |

## 二、自动化审计结果（英文投稿稿）

| 检查项 | 结果 | 说明 |
|---|---|---|
| em-dash（—, U+2014） | ✅ 0 处 | 上一轮被频率限制阻断的修正已于本轮回补 |
| en-dash（–, U+2013） | ✅ 0 处 | — |
| 图引用闭合 | ✅ 图1–7 | 每图 ≥2 处引用，无悬空引用 |
| 引文闭合 | ✅ [1]–[12] | 编号引文全部闭合，无悬空 |
| 关键数字一致性 | ✅ 13 项 | 见第三节 |
| PENDING 标记 | ⚠️ 3 处（合法） | 均为 IAA 待补，未断言任何值 |

### 关键数字一致性（英文稿已核验）
M4 抽取准确率 90.0% / Cohen's κ 0.675；四支柱 63.2 / 54.7 / 79.3 / 59.6；文档合规率 64.2；
多样性复合 0.485（GEO 0.21 / POP 0.49 / SKIN 0.12 / ANN 0.77 / GEN 0.85）；守护拦截 14 个越界字段。
> 注：90.0%/κ0.675 为 **LLM-vs-gold（M4）** 数字；IAA（人类—人类）为另一维度，当前 PENDING。

## 三、文献卷期页终校（已实查，非编造）

| 编号 | 文献 | 卷期页 |
|---|---|---|
| [8] | UNI | *Nat. Med.* **30**, 850–862 (2024) |
| [9] | CONCH | *Nat. Med.* **30**, 863–874 (2024) |
| [10] | Prov-GigaPath | *Nature* **630**, 181–188 (2024) |
| [11] | Virchow | *Nat. Med.* **30**, 2924–2935 (2024)（期 30(10)） |
| [12] | MONET | *Nat. Med.* **30**, 1154–1165 (2024)（期 30(4)） |

## 四、待人工完成项（投稿前必办）

1. **第二位独立编码者 IAA（硬缺口）**
   - 协议/模板/脚本已就绪（`IAA_PROTOCOL.md`、`coder_b_template/coder_b_blank.csv`、26 个空白 JSON）。
   - 行动：请一位独立编码者依据 `sources/<id>.txt` 填写 `coder_b/` 后运行 `python compute_iaa.py`，真实 κ/Jaccard/一致率即自动生成并回填论文（当前标记 PENDING）。
2. **投稿信占位符**（4 个，位于 `MedDataCard_submission_package.md`）
   - `[Corresponding Author Name]`、`[Affiliation]`、`[Email]`、`[Date]` —— 填后可直接用。
3. **审稿人建议**：Cover Letter 中 `Suggested reviewers` 为占位，按实际填写（或删去请编辑安排）。

## 五、投稿前最终确认（checklist）

- [x] 图1–7 全部生成且嵌入 demo 与论文
- [x] 引文 [1]–[12] 闭合，文献卷期页已核验
- [x] 英文稿无 em-dash / en-dash
- [x] 关键数字与图注、补充材料一致
- [x] IAA 协议就位，数字明确标记 PENDING（未编造）
- [x] 投稿包含主投 + 两期刊变体
- [ ] 第二位编码者完成 `coder_b/` 标注并回填 IAA（**需人工**）
- [ ] 填写作者/单位/邮箱/日期占位符（**需人工**）
- [ ] 选定期刊后对应微调 Cover Letter（npj DM / Lancet DH / Scientific Data 三版已备）

---
*诚信声明：本清单所有"已通过"项均经脚本实跑或文献实查，未断言任何未经计算的 IAA 数值。*
