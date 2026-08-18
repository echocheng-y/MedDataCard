"""M4 — 抽样验证 + Cohen's κ。

目标：在「论文摘要级」输入下，验证 LLM 抽取管线生成的字段与人工 gold 标准的一致程度。

方法：
  - 取 12 个跨模态数据集（影像/EHR/组学/文本），源文本 = 论文摘要摘录（sources/<id>.txt）。
  - 人工 gold（gold/<id>.json）= 仅摘要中明确陈述、可由审阅者推导的事实。
  - 运行 extract_with_llm(<id>, source_text) 生成卡片（需 API key；无 key 时降级 baseline）。
  - 在可比字段上比较：modalities / sample_counts / countries / intended_tasks / source_type。
  - 计算：字段级精确匹配率 + 分类字段（source_type）的 Cohen's κ + 集合字段的 Jaccard。

诚实性说明：
  - license / commercial_use_allowed 由 catalog 基线提供，并非 LLM 从摘要抽取，故不计入 LLM 抽取准确率
    （仅作标注，展示「目录冗余」）。
  - source_type 由基线启发式(_infer_source_type) + LLM 修正共同决定。12 个数据集中有 3 个
    基线会判错（BraTS 2024→other、HAM10000→other、Tabula Sapiens→repository），正是检验
    LLM 修正能力的用例；其余 9 个基线已正确，用于衡量「基线稳健性 + LLM 不引入错误」的合干表现。
  - source_type 跨 4 个类别（repository / challenge / paper-supplement / other），边际分布更均衡，
    κ 不再像 n=4 时易退化。
"""
from __future__ import annotations

import json
import re
from pathlib import Path

from extract import extract_with_llm


def safe_name(ds_id: str) -> str:
    """把数据集 id 转成安全文件名：保留字母/数字/下划线/连字符/点/中文，
    仅把空格与路径分隔符等替换为下划线。"""
    return re.sub(r"[^A-Za-z0-9_.\-\u4e00-\u9fff]", "_", ds_id)

ROOT = Path(__file__).parent
SOURCES = ROOT / "sources"
GOLD = ROOT / "gold"
OUT = ROOT / "m4_output"
OUT.mkdir(exist_ok=True)

# 参与 LLM 抽取准确率评分的可比字段（license/commercial 由目录提供，排除）
SCORED_FIELDS = [
    "modality.modalities",
    "modality.sample_counts",
    "geography.countries",
    "tasks_and_use.intended_tasks",
    "metadata.source_type",
]
EXCLUDED_FIELDS = ["ethics.license", "ethics.commercial_use_allowed"]

CATALOG_SOURCE = {
    # —— 原有 4 个胸 X 光（放射学）——
    "NIH ChestX-ray14": "sources/NIH_ChestX-ray14.txt",
    "MIMIC-CXR": "sources/MIMIC-CXR.txt",
    "CheXpert": "sources/CheXpert.txt",
    "PadChest": "sources/PadChest.txt",
    # —— 扩样 8 个跨模态 ——
    "MIMIC-IV": "sources/MIMIC-IV.txt",
    "eICU-CRD": "sources/eICU-CRD.txt",
    "HAM10000": "sources/HAM10000.txt",
    "Tabula Sapiens": "sources/Tabula_Sapiens.txt",
    "TotalSegmentator": "sources/TotalSegmentator.txt",
    "MedQA": "sources/MedQA.txt",
    "BraTS 2024": "sources/BraTS_2024.txt",
    "ISIC 2024/历年": "sources/ISIC_2024_历年.txt",
}


def get_path(card: dict, path: str):
    cur = card
    for p in path.split("."):
        if isinstance(cur, dict) and p in cur:
            cur = cur[p]
        else:
            return None
    return cur


def _as_set(v):
    return set(v) if isinstance(v, list) else (set() if v is None else {v})


def compare_field(field: str, gold_v, llm_v) -> tuple[bool, str]:
    """返回 (是否匹配, 人类可读说明)。"""
    if field == "modality.sample_counts":
        g = gold_v or {}
        l = llm_v or {}
        ok = all((k in l and l[k] == gv) for k, gv in g.items())
        return ok, f"gold={g} llm={l}"
    if field in ("modality.modalities", "geography.countries", "tasks_and_use.intended_tasks"):
        # gold = 摘要中明确陈述的最小集；llm 若包含额外已文档化项（如文本报告）不算错：
        # 判定采用 gold ⊆ llm（子集语义）。同时报告 Jaccard。
        gs, ls = _as_set(gold_v), _as_set(llm_v)
        ok = gs <= ls
        detail = f"gold={sorted(gs)} llm={sorted(ls)}"
        if gs | ls:
            j = len(gs & ls) / len(gs | ls) if (gs | ls) else 1.0
            detail += f" jaccard={j:.2f}"
        return ok, detail
    # 单值（source_type 等）
    ok = (gold_v == llm_v)
    return ok, f"gold={gold_v!r} llm={llm_v!r}"


def cohen_kappa(labels_a: list, labels_b: list) -> float:
    n = len(labels_a)
    cats = sorted(set(labels_a) | set(labels_b))
    cm = {(a, b): 0 for a in cats for b in cats}
    for a, b in zip(labels_a, labels_b):
        cm[(a, b)] += 1
    po = sum(cm[(c, c)] for c in cats) / n if n else 1.0
    row = {c: sum(cm[(c, x)] for x in cats) for c in cats}
    col = {c: sum(cm[(x, c)] for x in cats) for c in cats}
    pe = sum(row[c] * col[c] for c in cats) / (n * n) if n else 1.0
    if pe >= 1.0:
        return 1.0
    return (po - pe) / (1 - pe)


def main(provider: str = "openai", model: str | None = None):
    cells = []          # (dataset, field, gold, llm, match)
    source_type_pairs = []  # (gold, llm)
    degraded = False

    for ds_id, src_rel in CATALOG_SOURCE.items():
        src = (SOURCES / src_rel.split("/")[-1]).read_text(encoding="utf-8")
        gold = json.loads((GOLD / f"{safe_name(ds_id)}.json").read_text(encoding="utf-8"))["comparable"]
        card = extract_with_llm(ds_id, src, provider=provider, model=model)
        if card["extraction"].get("method") != "hybrid":
            degraded = True
        (OUT / f"{safe_name(ds_id)}.json").write_text(
            json.dumps(card, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        for field in SCORED_FIELDS:
            gv = gold.get(field)
            lv = get_path(card, field)
            ok, detail = compare_field(field, gv, lv)
            cells.append((ds_id, field, gv, lv, ok))
            if field == "metadata.source_type":
                source_type_pairs.append((str(gv), str(lv)))

    total = len(cells)
    matches = sum(1 for *_, ok in cells if ok)
    acc = matches / total if total else 0.0
    kappa = cohen_kappa([a for a, _ in source_type_pairs], [b for _, b in source_type_pairs])

    report = {
        "provider": provider,
        "model": model or "(default)",
        "degraded_to_baseline": degraded,
        "n_datasets": len(CATALOG_SOURCE),
        "n_cells": total,
        "matched_cells": matches,
        "exact_match_accuracy": round(acc, 4),
        "cohen_kappa_source_type": round(kappa, 4),
        "cells": [
            {"dataset": d, "field": f, "gold": gv, "llm": lv, "match": ok}
            for (d, f, gv, lv, ok) in cells
        ],
        "note": ("license/commercial_use_allowed 由 catalog 基线提供，未计入 LLM 抽取准确率；"
                 "source_type 的 κ 基于 12 个跨模态数据集，跨越 repository/challenge/paper-supplement/other "
                 "4 个类别，边际分布较均衡。其中基线(_infer_source_type)会判错的 3 个（BraTS 2024、HAM10000、"
                 "Tabula Sapiens）是检验 LLM 修正能力的关键样例。集合字段用 gold⊆llm 子集语义判定；"
                 "sample_counts 用 gold 各键精确匹配（键缺失或值不符即判错）。"),
    }
    (ROOT / "m4_report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    # 控制台摘要
    print(f"Provider={provider} model={model or '(default)'} degraded={degraded}")
    print(f"Exact-match accuracy: {matches}/{total} = {acc:.1%}")
    print(f"Cohen's κ (source_type): {kappa:.3f}")
    print("\nPer-cell:")
    for d, f, gv, lv, ok in cells:
        print(f"  [{'OK ' if ok else 'XX '}] {d:18s} {f:32s} {lv!r}")
    print(f"\nReport -> m4_report.json ; generated cards -> m4_output/")
    return report


if __name__ == "__main__":
    import sys
    prov = sys.argv[1] if len(sys.argv) > 1 else "openai"
    mdl = sys.argv[2] if len(sys.argv) > 2 else None
    main(provider=prov, model=mdl)
