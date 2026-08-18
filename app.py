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
    "metadata": "Identity & Source",
    "population": "Population",
    "geography": "Geography & Collection",
    "modality": "Modality",
    "annotation": "Annotation",
    "data_origin": "Data Origin & Sampling",
    "ethics": "Ethics & Compliance",
    "bias_and_limitations": "Bias & Limitations",
    "tasks_and_use": "Tasks & Use",
    "extraction": "Extraction Provenance",
}


def _render_value(v) -> str:
    if isinstance(v, dict):
        return "\n".join(f"- **{k}**: {_render_value(val)}" for k, val in v.items())
    if isinstance(v, list):
        return "\n".join(f"- {_render_value(x)}" for x in v) if v else "_(empty)_"
    if v in (None, ""):
        return "_(not filled)_"
    return str(v)


def to_markdown(card: dict) -> str:
    lines = [f"# ST Data Card · {card.get('dataset_name', card.get('dataset_id', ''))}",
             f"> Generated: {_dt.date.today().isoformat()} ｜ schema v{card.get('schema_version','?')}",
             ""]
    mf = card.get("medical_fields")
    if mf:
        lines.append(f"**Medical Fields**: {', '.join(mf)}")
        lines.append("")
    pending = card.get("extraction", {}).get("pending_verification", [])
    if pending:
        lines.append("**⚠️ Pending Verification:**")
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
    """Render a data card: validation / pending / dimensions / edit / export."""
    ok, errors = validate_card(card)
    if ok:
        st.success("✅ Passed ST Data Card JSON Schema validation")
    else:
        st.error("❌ Schema validation failed: " + "; ".join(errors[:5]))

    pending = card.get("extraction", {}).get("pending_verification", [])
    if pending:
        st.warning("⚠️ **Pending items (no fabrication; require manual confirmation):**\n" + "\n".join(f"- {p}" for p in pending))

    mf = card.get("medical_fields", [])
    if mf:
        st.markdown("**Medical Fields:** " + "　".join(f"`{m}`" for m in mf))

    cols = st.columns(3)
    groups = ["metadata", "population", "geography", "modality", "annotation",
              "data_origin", "ethics", "bias_and_limitations"]
    for i, g in enumerate(groups):
        with cols[i % 3]:
            with st.expander(DIMENSION_LABELS.get(g, g), expanded=True):
                if g in card:
                    st.markdown(_render_value(card[g]), unsafe_allow_html=False)
                else:
                    st.markdown("_(not filled)_")

    with st.expander("Tasks & Use / Source", expanded=False):
        st.markdown(_render_value({k: card[k] for k in ("tasks_and_use",) if k in card}))

    st.header("✏️ Edit / Validate")
    edited = st.text_area("JSON (edit then click Apply)", value=st.session_state.get("json_edit", ""), height=300)
    c1, c2 = st.columns(2)
    if c1.button("Apply Edit"):
        try:
            new_card = json.loads(edited)
            ok2, errs = validate_card(new_card)
            if ok2:
                st.session_state.card = new_card
                st.success("Applied and validated")
            else:
                st.error("Validation failed: " + "; ".join(errs[:5]))
        except Exception as e:
            st.error(f"JSON parse failed: {e}")

    st.header("📤 Export")
    c1, c2, c3 = st.columns(3)
    c1.download_button("Download JSON", json.dumps(card, ensure_ascii=False, indent=2),
                       file_name=f"{card.get('dataset_id','card')}.json", mime="application/json")
    c2.download_button("Download Markdown", to_markdown(card),
                       file_name=f"{card.get('dataset_id','card')}.md", mime="text/markdown")
    if c3.button("💾 Save to datacards/"):
        os.makedirs("datacards", exist_ok=True)
        p = f"datacards/{card.get('dataset_id','card')}.json"
        with open(p, "w", encoding="utf-8") as f:
            json.dump(card, f, ensure_ascii=False, indent=2)
        st.success(f"Saved: {p}")


def render_card_tab():
    catalog = load_catalog()
    names = [r["id"] for r in catalog]

    with st.sidebar:
        st.header("① Select Dataset")
        sel = st.selectbox("Dataset (from dataset_catalog.xlsx)", names)
        rec = next(r for r in catalog if r["id"] == sel)
        st.write(f"**Platform:** {rec['platform']}")
        st.write(f"**Modality:** {rec['modality_text']}")
        st.write(f"**License:** {rec['license']}")

        st.header("② LLM Extraction (optional)")
        provider = st.selectbox("Provider", ["openai", "anthropic", "dashscope"])
        api_key = st.text_input("API Key (leave empty to use catalog baseline only)", type="password")
        source_text = st.text_area("Paste paper abstract / README text (for LLM field completion)", height=160)

        if st.button("🚀 Generate Data Card", type="primary"):
            with st.spinner("Generating…"):
                if api_key and source_text.strip():
                    card = extract_with_llm(sel, source_text, provider=provider, api_key=api_key)
                else:
                    card = baseline_from_catalog(sel)
            st.session_state.card = card
            st.session_state.json_edit = json.dumps(card, ensure_ascii=False, indent=2)

    if "card" not in st.session_state:
        st.info("Select a dataset from the left and click 'Generate Data Card' to start. With no API key, a catalog baseline card is generated automatically.")
        return
    render_card(st.session_state.card)


def _safe_name(name: str) -> str:
    import re
    return re.sub(r"[^\w一-鿿-]", "_", name)


def render_audit_tab():
    st.subheader("📊 Cross-dataset Systematic Audit (based on audit_summary.csv)")
    csv_path = Path("audit_summary.csv")
    if not csv_path.exists():
        st.warning("Audit summary not yet generated; run `python generate_all.py` first.")
        return

    rows = list(csv.DictReader(open(csv_path, encoding="utf-8")))
    df = pd.DataFrame(rows)
    for c in ("st_completeness_pct", "pending_count"):
        df[c] = pd.to_numeric(df[c], errors="coerce")

    # Metrics
    n = len(df)
    avg_comp = round(df["st_completeness_pct"].mean(), 1)
    single = int((df["geography_single_center"] == "Y").sum())
    recs = {r["id"]: r for r in load_catalog()}
    us_eu = sum(1 for r in recs.values() if any(k in r["limitation"] for k in ("美国", "美欧", "欧洲")))
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Datasets", n)
    c2.metric("Avg ST Completeness", f"{avg_comp}%")
    c3.metric("Single-center Datasets", f"{single}/{n}")
    c4.metric("US/EU-source Datasets", f"{us_eu}/{n}")

    # Leaderboard (sortable by ST completeness)
    st.subheader("🏆 Data Card Completeness Leaderboard")
    st.caption("Current baseline completeness reflects catalog metadata only; it rises after paper/README or manual completion.")
    show = df[["dataset", "medical_fields", "modalities", "license",
               "countries", "geography_single_center", "st_completeness_pct", "pending_count"]]
    st.dataframe(show.sort_values("st_completeness_pct", ascending=False),
                 use_container_width=True, hide_index=True)

    # Charts
    st.subheader("📈 Visualization")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**ST Completeness per Dataset**")
        st.bar_chart(df.set_index("dataset")["st_completeness_pct"])
    with col2:
        st.markdown("**Medical Field Distribution**")
        mf_counter: dict[str, int] = {}
        for v in df["medical_fields"]:
            for m in str(v).split("/"):
                m = m.strip()
                if m:
                    mf_counter[m] = mf_counter.get(m, 0) + 1
        st.bar_chart(pd.Series(mf_counter, name="Dataset count").sort_values(ascending=False))

    # Systematic bias
    st.subheader("🚨 Systematic Bias Overview")
    single_list = df[df["geography_single_center"] == "Y"]["dataset"].tolist()
    st.markdown(f"- **Single-center datasets ({len(single_list)}):** {', '.join(single_list)}")
    st.markdown(f"- **US/EU-source datasets ({us_eu}):** "
                + ", ".join(r["id"] for r in recs.values()
                            if any(k in r["limitation"] for k in ("美国", "美欧", "欧洲"))))

    # View a single data card
    st.subheader("🔍 View a Single Data Card")
    pick = st.selectbox("Select Dataset", df["dataset"].tolist())
    jp = Path("datacards") / f"{_safe_name(pick)}.json"
    if jp.exists():
        card = json.loads(jp.read_text(encoding="utf-8"))
        render_card(card)
    else:
        st.info("This data card is not generated yet; generate it on the 'Data Card Generation' page or run generate_all.py.")


def main():
    st.set_page_config(page_title="MedDataCard", layout="wide")
    st.title("🩺 MedDataCard")
    st.caption("STANDING Together compliance data cards · auto-generation & audit (MVP prototype)")

    tab1, tab2 = st.tabs(["🩺 Data Card Generation", "📊 Audit Overview / Leaderboard"])
    with tab1:
        render_card_tab()
    with tab2:
        render_audit_tab()


if __name__ == "__main__":
    main()
