"""MedDataCard Web 原型（Streamlit）。

运行：pip install -r requirements.txt && streamlit run app.py
功能：
  ① 数据卡生成：选择数据集 →（可选）粘贴论文/README → 生成 ST 数据卡 → 查看/编辑/导出。
  ② 审计总览 / 排行榜：基于 audit_summary.csv 做跨数据集系统性审计与排名。
无 LLM key 时自动用 dataset_catalog.xlsx 的真实元数据生成基线卡。
"""
from __future__ import annotations

import json
import os
import csv
import datetime as _dt
from pathlib import Path

import streamlit as st
import pandas as pd

from catalog import load_catalog
from extract import baseline_from_catalog, extract_with_llm
from schema_utils import validate_card, load_schema

DIMENSION_LABELS = {
    "metadata": "标识与来源",
    "population": "人口学",
    "geography": "地理与采集",
    "modality": "数据模态",
    "annotation": "标注",
    "data_origin": "数据起源与抽样",
    "ethics": "伦理与合规",
    "bias_and_limitations": "偏倚与局限性",
    "tasks_and_use": "任务与用途",
    "extraction": "抽取溯源",
}


def _render_value(v) -> str:
    if isinstance(v, dict):
        return "\n".join(f"- **{k}**: {_render_value(val)}" for k, val in v.items())
    if isinstance(v, list):
        return "\n".join(f"- {_render_value(x)}" for x in v) if v else "_(空)_"
    if v in (None, ""):
        return "_(未填)_"
    return str(v)


def to_markdown(card: dict) -> str:
    lines = [f"# ST 数据卡 · {card.get('dataset_name', card.get('dataset_id', ''))}",
             f"> 生成时间：{_dt.date.today().isoformat()} ｜ schema v{card.get('schema_version','?')}",
             ""]
    mf = card.get("medical_fields")
    if mf:
        lines.append(f"**医学领域**：{', '.join(mf)}")
        lines.append("")
    pending = card.get("extraction", {}).get("pending_verification", [])
    if pending:
        lines.append("**⚠️ 待核实项：**")
        for p in pending:
            lines.append(f"- {p}")
        lines.append("")
    for key in ["metadata", "population", "geography", "modality", "annotation",
                "data_origin", "ethics", "bias_and_limitations", "tasks_and_use"]:
        if key not in card:
            continue
        lines.append(f"## {DIMENSION_LABELS.get(key, key)}")
        lines.append(_render_value(card[key]))
        lines.append("")
    return "\n".join(lines)


def render_card(card: dict):
    """渲染一张数据卡：校验 / 待核实 / 维度 / 编辑 / 导出。"""
    ok, errors = validate_card(card)
    if ok:
        st.success("✅ 通过 ST 数据卡 JSON Schema 校验")
    else:
        st.error("❌ Schema 校验未通过：" + "；".join(errors[:5]))

    pending = card.get("extraction", {}).get("pending_verification", [])
    if pending:
        st.warning("⚠️ **待核实项（禁止编造，需人工确认）**：\n" + "\n".join(f"- {p}" for p in pending))

    mf = card.get("medical_fields", [])
    if mf:
        st.markdown("**医学领域**：" + "　".join(f"`{m}`" for m in mf))

    cols = st.columns(3)
    groups = ["metadata", "population", "geography", "modality", "annotation",
              "data_origin", "ethics", "bias_and_limitations"]
    for i, g in enumerate(groups):
        with cols[i % 3]:
            with st.expander(DIMENSION_LABELS.get(g, g), expanded=True):
                if g in card:
                    st.markdown(_render_value(card[g]), unsafe_allow_html=False)
                else:
                    st.markdown("_(未填)_")

    with st.expander("任务与用途 / 来源", expanded=False):
        st.markdown(_render_value({k: card[k] for k in ("tasks_and_use",) if k in card}))

    st.header("✏️ 编辑 / 校验")
    edited = st.text_area("JSON（可直接修改后点击应用）", value=st.session_state.get("json_edit", ""), height=300)
    c1, c2 = st.columns(2)
    if c1.button("应用编辑"):
        try:
            new_card = json.loads(edited)
            ok2, errs = validate_card(new_card)
            if ok2:
                st.session_state.card = new_card
                st.success("已应用并通过校验")
            else:
                st.error("校验失败：" + "；".join(errs[:5]))
        except Exception as e:
            st.error(f"JSON 解析失败：{e}")

    st.header("📤 导出")
    c1, c2, c3 = st.columns(3)
    c1.download_button("下载 JSON", json.dumps(card, ensure_ascii=False, indent=2),
                       file_name=f"{card.get('dataset_id','card')}.json", mime="application/json")
    c2.download_button("下载 Markdown", to_markdown(card),
                       file_name=f"{card.get('dataset_id','card')}.md", mime="text/markdown")
    if c3.button("💾 保存到 datacards/"):
        os.makedirs("datacards", exist_ok=True)
        p = f"datacards/{card.get('dataset_id','card')}.json"
        with open(p, "w", encoding="utf-8") as f:
            json.dump(card, f, ensure_ascii=False, indent=2)
        st.success(f"已保存：{p}")


def render_card_tab():
    catalog = load_catalog()
    names = [r["id"] for r in catalog]

    with st.sidebar:
        st.header("① 选择数据集")
        sel = st.selectbox("数据集（来自 dataset_catalog.xlsx）", names)
        rec = next(r for r in catalog if r["id"] == sel)
        st.write(f"**平台**：{rec['platform']}")
        st.write(f"**模态**：{rec['modality_text']}")
        st.write(f"**许可证**：{rec['license']}")

        st.header("② LLM 抽取（可选）")
        provider = st.selectbox("Provider", ["openai", "anthropic", "dashscope"])
        api_key = st.text_input("API Key（留空则仅用目录基线卡）", type="password")
        source_text = st.text_area("粘贴论文摘要 / README 文本（用于 LLM 补充字段）", height=160)

        if st.button("🚀 生成数据卡", type="primary"):
            with st.spinner("生成中…"):
                if api_key and source_text.strip():
                    card = extract_with_llm(sel, source_text, provider=provider, api_key=api_key)
                else:
                    card = baseline_from_catalog(sel)
            st.session_state.card = card
            st.session_state.json_edit = json.dumps(card, ensure_ascii=False, indent=2)

    if "card" not in st.session_state:
        st.info("从左侧选择数据集并点击「生成数据卡」开始。无 API key 时自动生成目录基线卡。")
        return
    render_card(st.session_state.card)


def _safe_name(name: str) -> str:
    import re
    return re.sub(r"[^\w一-鿿-]", "_", name)


def render_audit_tab():
    st.subheader("📊 跨数据集系统性审计（基于 audit_summary.csv）")
    csv_path = Path("audit_summary.csv")
    if not csv_path.exists():
        st.warning("尚未生成审计摘要，请先运行 `python generate_all.py`。")
        return

    rows = list(csv.DictReader(open(csv_path, encoding="utf-8")))
    df = pd.DataFrame(rows)
    for c in ("st_completeness_pct", "pending_count"):
        df[c] = pd.to_numeric(df[c], errors="coerce")

    # 指标
    n = len(df)
    avg_comp = round(df["st_completeness_pct"].mean(), 1)
    single = int((df["geography_single_center"] == "Y").sum())
    recs = {r["id"]: r for r in load_catalog()}
    us_eu = sum(1 for r in recs.values() if any(k in r["limitation"] for k in ("美国", "美欧", "欧洲")))
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("数据集总数", n)
    c2.metric("平均 ST 维度完整度", f"{avg_comp}%")
    c3.metric("单中心数据集", f"{single}/{n}")
    c4.metric("美/欧来源数据集", f"{us_eu}/{n}")

    # 排行榜（按 ST 维度完整度排序，可点击表头重排）
    st.subheader("🏆 数据卡完整度排行榜")
    st.caption("当前为「仅目录元数据」基线完整度；接入论文/README 或人工补充后会提升。")
    show = df[["dataset", "medical_fields", "modalities", "license",
               "countries", "geography_single_center", "st_completeness_pct", "pending_count"]]
    st.dataframe(show.sort_values("st_completeness_pct", ascending=False),
                 use_container_width=True, hide_index=True)

    # 图表
    st.subheader("📈 可视化")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**各数据集 ST 维度完整度**")
        st.bar_chart(df.set_index("dataset")["st_completeness_pct"])
    with col2:
        st.markdown("**医学领域分布**")
        mf_counter: dict[str, int] = {}
        for v in df["medical_fields"]:
            for m in str(v).split("/"):
                m = m.strip()
                if m:
                    mf_counter[m] = mf_counter.get(m, 0) + 1
        st.bar_chart(pd.Series(mf_counter, name="数据集数").sort_values(ascending=False))

    # 系统性偏倚
    st.subheader("🚨 系统性偏倚速览")
    single_list = df[df["geography_single_center"] == "Y"]["dataset"].tolist()
    st.markdown(f"- **单中心数据集（{len(single_list)}）**：{', '.join(single_list)}")
    st.markdown(f"- **美/欧来源数据集（{us_eu}）**："
                + ", ".join(r["id"] for r in recs.values()
                            if any(k in r["limitation"] for k in ("美国", "美欧", "欧洲"))))

    # 查看某数据集数据卡
    st.subheader("🔍 查看单张数据卡")
    pick = st.selectbox("选择数据集", df["dataset"].tolist())
    jp = Path("datacards") / f"{_safe_name(pick)}.json"
    if jp.exists():
        card = json.loads(jp.read_text(encoding="utf-8"))
        render_card(card)
    else:
        st.info("该数据卡尚未生成，请先在『数据卡生成』页生成，或运行 generate_all.py。")


def main():
    st.set_page_config(page_title="MedDataCard", layout="wide")
    st.title("🩺 MedDataCard")
    st.caption("STANDING Together 合规数据卡 · 自动生成与审计（MVP 原型）")

    tab1, tab2 = st.tabs(["🩺 数据卡生成", "📊 审计总览 / 排行榜"])
    with tab1:
        render_card_tab()
    with tab2:
        render_audit_tab()


if __name__ == "__main__":
    main()
