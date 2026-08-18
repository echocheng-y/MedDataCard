"""批量生成 26 个数据集的 ST 数据卡 + 审计摘要。

默认（无 --llm）：仅用 dataset_catalog.xlsx 真实元数据生成基线卡（无 key 也能跑）。
加 --llm：对有 curated 摘要（sources/<id>.txt）的数据集走 extract_with_llm 生成 hybrid 卡，
其余回退基线卡。需要 LLM API key（默认 dashscope，见 .env）。
输出：
  datacards/<dataset>.json   每张数据卡
  audit_summary.csv         跨数据集审计摘要（维度完整度 / 待核实 / 地理集中 / 生成方式）
"""
from __future__ import annotations

import csv
import json
import re
import sys
from pathlib import Path

from catalog import load_catalog
from extract import baseline_from_catalog, extract_with_llm
from schema_utils import load_schema, validate_card

HERE = Path(__file__).parent
OUT_DIR = HERE / "datacards"
SOURCES = HERE / "sources"
SCHEMA = load_schema()

# ST 四大支柱对应的顶层分组（用于计算维度完整度）
ST_GROUPS = ["metadata", "data_origin", "population", "geography",
             "modality", "annotation", "ethics", "bias_and_limitations"]


def _safe_name(name: str) -> str:
    return re.sub(r"[^\w一-鿿-]", "_", name)


def _group_completeness(card: dict, group: str) -> float:
    """该 ST 分组中『已填字段数 / 定义字段数』百分比（仅统计定义过的属性）。"""
    props = SCHEMA["properties"].get(group, {}).get("properties")
    if not props:
        return 100.0
    filled = 0
    for k in props:
        v = card.get(group, {}).get(k) if isinstance(card.get(group), dict) else None
        if v not in (None, "", [], {}):
            filled += 1
    return round(100.0 * filled / len(props), 1)


def _overall_completeness(card: dict) -> float:
    total = 0
    filled = 0
    for g in ST_GROUPS:
        props = SCHEMA["properties"].get(g, {}).get("properties")
        if not props:
            continue
        total += len(props)
        for k in props:
            v = card.get(g, {}).get(k) if isinstance(card.get(g), dict) else None
            if v not in (None, "", [], {}):
                filled += 1
    return round(100.0 * filled / total, 1) if total else 0.0


def main(use_llm: bool = False, provider: str = "dashscope", model: str | None = None):
    OUT_DIR.mkdir(exist_ok=True)
    recs = load_catalog()
    rows = []
    n_hybrid = 0
    for r in recs:
        src_file = SOURCES / f"{_safe_name(r['id'])}.txt"
        if use_llm and src_file.exists():
            card = extract_with_llm(
                r["id"], src_file.read_text(encoding="utf-8"),
                provider=provider, model=model,
            )
            n_hybrid += 1
        else:
            card = baseline_from_catalog(r["id"])
        ok, errs = validate_card(card, SCHEMA)
        fname = OUT_DIR / f"{_safe_name(r['id'])}.json"
        fname.write_text(json.dumps(card, ensure_ascii=False, indent=2), encoding="utf-8")

        geo = card.get("geography", {}).get("countries", [])
        single_center = "单中心" in r["limitation"]
        rows.append({
            "dataset": r["id"],
            "medical_fields": "/".join(card.get("medical_fields", [])),
            "modalities": "/".join(card.get("modality", {}).get("modalities", [])),
            "license": card.get("ethics", {}).get("license", ""),
            "countries": "/".join(geo),
            "geography_single_center": "Y" if single_center else "N",
            "st_completeness_pct": _overall_completeness(card),
            "pending_count": len(card.get("extraction", {}).get("pending_verification", [])),
            "schema_valid": "Y" if ok else "N",
            "method": card.get("extraction", {}).get("method", "manual"),
        })

    # 写审计摘要
    csv_path = HERE / "audit_summary.csv"
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)

    # 控制台汇总（系统性偏倚洞察）
    n = len(rows)
    us_eu = sum(1 for x in recs if ("美国" in x["limitation"] or "美欧" in x["limitation"] or "欧洲" in x["limitation"]))
    single = sum(1 for r in rows if r["geography_single_center"] == "Y")
    mode = f"LLM hybrid（{n_hybrid} 张 hybrid + {n - n_hybrid} 张 baseline）" if use_llm else "基线（仅目录元数据）"
    print(f"已生成 {n} 张数据卡 → {OUT_DIR}/  [{mode}]")
    print(f"审计摘要 → {csv_path}")
    print(f"\n系统性偏倚速览：")
    print(f"  局限文本提及『单中心』的数据集：{single}/{n}")
    print(f"  局限文本提及美/欧的数据集：{us_eu}/{n}")
    avg = round(sum(r["st_completeness_pct"] for r in rows) / n, 1)
    print(f"  平均 ST 维度完整度（{('hybrid' if use_llm else '基线')}）：{avg}%")
    print(f"  全部 schema 校验：{'通过' if all(r['schema_valid']=='Y' for r in rows) else '有失败'}")


if __name__ == "__main__":
    use_llm = "--llm" in sys.argv
    provider = "dashscope"
    model = None
    if use_llm:
        # 可选：--provider openai|dashscope|anthropic  /  --model <name>
        if "--provider" in sys.argv:
            provider = sys.argv[sys.argv.index("--provider") + 1]
        if "--model" in sys.argv:
            model = sys.argv[sys.argv.index("--model") + 1]
    main(use_llm=use_llm, provider=provider, model=model)
