"""MedDataCard 元数据抽取管线。

两种模式：
  - baseline_from_catalog(): 仅用 dataset_catalog.xlsx 的真实元数据生成「部分数据卡」，
    所有目录未覆盖的字段留空并写入 pending_verification，绝不编造。
  - extract_with_llm(): 在 baseline 之上，用 LLM（OpenAI / Anthropic）从论文/README
    文本补充字段；无 API key 时自动降级为 baseline。

LLM 调用走 REST（requests），不强制安装官方 SDK；缺失 SDK 不影响 baseline 模式。
"""
from __future__ import annotations

import datetime as _dt
import json
import os
import re
from pathlib import Path

from catalog import load_catalog
from schema_utils import load_schema

_SCHEMA = load_schema()


# ---------- API key 读取（安全：优先环境变量，回退本地 .env，绝不打印） ----------

def _load_api_key(provider: str, explicit: str | None = None) -> str | None:
    """读取 LLM API key。顺序：显式参数 → 环境变量 → 本地 .env 文件。

    不写入日志、不在任何输出中回显 key 内容。
    """
    if explicit:
        return explicit
    env_name = {
        "openai": "OPENAI_API_KEY",
        "anthropic": "ANTHROPIC_API_KEY",
        "dashscope": "DASHSCOPE_API_KEY",
    }.get(provider)
    if env_name and os.environ.get(env_name):
        return os.environ[env_name]
    env_path = Path(__file__).with_name(".env")
    if env_path.exists() and env_name:
        for line in env_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, _, v = line.partition("=")
            if k.strip() == env_name:
                return v.strip().strip('"').strip("'")
    return None


# ---------- baseline（仅目录真实元数据） ----------

def _infer_source_type(rec: dict) -> str:
    s = (rec["platform"] + " " + rec["link"]).lower()
    if "challenge" in s or "竞赛" in rec["platform"]:
        return "challenge"
    if "registry" in s or rec["id"] in ("UK Biobank", "TCGA", "ADNI"):
        return "registry"
    if any(k in s for k in ("github", "huggingface", "zenodo", "physionet")):
        return "repository"
    return "other"


def _infer_commercial(license_: str) -> bool | None:
    l = license_.lower()
    if "nc" in l or "non-commercial" in l or "研究许可" in license_ or "DUA" in license_:
        return False
    if l.startswith("cc0") or l.startswith("cc by") or "mit" in l or "odc-by" in l:
        return True
    return None


def _parse_sample_counts(scale: str) -> dict:
    out: dict = {}
    m = re.search(r"([\d,]+)\s*患者", scale)
    if m:
        out["patients"] = int(m.group(1).replace(",", ""))
    m = re.search(r"([\d,]+)\s*(?:图|images|图 ?\(?)", scale)
    if m:
        out["images"] = int(m.group(1).replace(",", ""))
    return out


def _map_tasks(task_text: str) -> list[str]:
    t = task_text
    out = []
    pairs = [
        ("分类", "classification"), ("检测", "detection"), ("分割", "segmentation"),
        ("报告生成", "report-generation"), ("问答", "qa"), ("检索", "retrieval"),
        ("预后", "classification"), ("预测", "classification"), ("因果", "causal"),
    ]
    for kw, enum in pairs:
        if kw in t and enum not in out:
            out.append(enum)
    return out


def baseline_from_catalog(dataset_id: str) -> dict:
    recs = {r["id"]: r for r in load_catalog()}
    rec = recs.get(dataset_id)
    if not rec:
        raise KeyError(f"目录中未找到数据集：{dataset_id}")

    pending = []
    geo = rec["geo_hints"]
    if geo:
        pending.append("geography.countries is heuristically inferred from limitation text; requires manual verification")

    # modality：仅在有值时写入可选字段（避免 None 违反类型约束）
    modality = {"modalities": rec["modalities"]}
    sample_counts = _parse_sample_counts(rec["scale"])
    if sample_counts:
        modality["sample_counts"] = sample_counts

    # ethics
    ethics = {"license": rec["license"]}
    commercial = _infer_commercial(rec["license"])
    if commercial is not None:
        ethics["commercial_use_allowed"] = commercial

    # bias
    limitations = [x for x in re.split(r"[；;]", rec["limitation"]) if x.strip()]

    # tasks
    tasks = _map_tasks(rec["task"])

    # metadata 组（ST 支柱①：身份/访问/目的）
    metadata = {"source_type": _infer_source_type(rec)}
    if rec["link"]:
        metadata["homepage"] = rec["link"]
        metadata["repositories"] = [{"platform": _host_of(rec["link"]), "url": rec["link"]}]

    card = {
        "schema_version": "0.2",
        "dataset_id": rec["id"],
        "dataset_name": rec["name"],
        "metadata": metadata,
        "medical_fields": rec["medical_fields"],
        "modality": modality,
        "ethics": ethics,
        "extraction": {
            "method": "manual",
            "human_reviewed": False,
            "last_updated": _dt.date.today().isoformat(),
            "notes": "Baseline card derived solely from dataset_catalog.xlsx real metadata; remaining fields require paper/README or manual completion.",
            "pending_verification": pending,
        },
    }
    if geo:
        card["geography"] = {"countries": geo}
    if limitations:
        card["bias_and_limitations"] = {"known_limitations": limitations}
    if tasks:
        card["tasks_and_use"] = {"intended_tasks": tasks}
    return card


def _host_of(url: str) -> str:
    if "github" in url:
        return "GitHub"
    if "huggingface" in url:
        return "HuggingFace"
    if "zenodo" in url:
        return "Zenodo"
    if "physionet" in url:
        return "PhysioNet"
    if "arxiv" in url:
        return "arXiv"
    if "isic" in url:
        return "ISIC"
    if "dataverse" in url:
        return "Harvard Dataverse"
    if "synapse" in url:
        return "Synapse"
    return "other"


# ---------- LLM 抽取（可选） ----------

def _build_prompt(dataset_id: str, source_text: str) -> list[dict]:
    system = (
        "你是医学 AI 数据集合规审计助手。请根据「源文本」（数据集论文/仓库 README 摘录），"
        "补全一份 STANDING Together 合规数据卡的结构化 JSON。\n"
        "严格遵守：\n"
        "1) 只填写源文本中有证据支持的字段；无证据的字段设为 null 或省略。\n"
        "2) 绝对禁止编造数据、卷期、页码、指标或来源。\n"
        "3) 任何不确定或需人工核实的内容，写入 extraction.pending_verification 列表。\n"
        "4) 输出严格为单个 JSON 对象，不要包含解释文字或 markdown 代码块。\n"
        "下面是数据卡 schema（仅填充其中已有的字段）：\n"
        + json.dumps(_SCHEMA, ensure_ascii=False)
    )
    user = f"数据集名称：{dataset_id}\n\n源文本：\n{source_text[:12000]}\n\n请输出补全后的数据卡 JSON。"
    return [
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ]


def _call_openai(messages, api_key, model="gpt-4o-mini",
                 base_url="https://api.openai.com/v1"):
    import requests
    r = requests.post(
        f"{base_url.rstrip('/')}/chat/completions",
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        json={"model": model, "messages": messages, "temperature": 0,
              "response_format": {"type": "json_object"}},
        timeout=120,
    )
    r.raise_for_status()
    return r.json()["choices"][0]["message"]["content"]


def _call_anthropic(messages, api_key, model="claude-3-5-haiku-20241022"):
    import requests
    # Anthropic 不支持 system 作为 messages；单独传
    sys = next((m["content"] for m in messages if m["role"] == "system"), "")
    conv = [m for m in messages if m["role"] != "system"]
    r = requests.post(
        "https://api.anthropic.com/v1/messages",
        headers={"x-api-key": api_key, "anthropic-version": "2023-06-01",
                 "Content-Type": "application/json"},
        json={"model": model, "max_tokens": 4000, "system": sys, "messages": conv},
        timeout=120,
    )
    r.raise_for_status()
    return r.json()["content"][0]["text"]


def _strip_json(text: str) -> str:
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    return text.strip()


def extract_with_llm(dataset_id: str, source_text: str,
                     provider: str = "openai", api_key: str | None = None,
                     model: str | None = None) -> dict:
    """在 baseline 之上用 LLM 补充字段；失败或无 key 时降级 baseline。

    api_key 可显式传入，也可省略（自动从环境变量 / 本地 .env 读取）。
    """
    baseline = baseline_from_catalog(dataset_id)
    api_key = _load_api_key(provider, api_key)
    if not api_key:
        baseline["extraction"]["notes"] = "未提供 LLM API key，已降级为目录基线卡。"
        return baseline
    messages = _build_prompt(dataset_id, source_text)
    try:
        if provider == "openai":
            raw = _call_openai(messages, api_key, model or "gpt-4o-mini")
        elif provider == "dashscope":
            # 阿里云百炼 DashScope：OpenAI 兼容接口
            raw = _call_openai(
                messages, api_key,
                model or "qwen-plus",
                base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
            )
        elif provider == "anthropic":
            raw = _call_anthropic(messages, api_key, model or "claude-3-5-haiku-20241022")
        else:
            raise ValueError(f"未知 provider：{provider}")
        llm_card = json.loads(_strip_json(raw))
        merged = _merge(baseline, llm_card)
        merged, dropped = conform_card(merged, _SCHEMA, baseline)
        merged["extraction"]["method"] = "hybrid"
        if dropped:
            merged["extraction"]["pending_verification"].append(
                "The following LLM fields were auto-dropped for violating schema constraints and reverted to baseline; pending manual review: "
                + ", ".join(sorted(set(dropped)))
            )
        return merged
    except Exception as e:  # 网络/解析失败 → 降级
        baseline["extraction"]["notes"] = f"LLM 抽取失败（{e}），已降级为目录基线卡。"
        return baseline


def _merge(baseline: dict, llm: dict) -> dict:
    """以 baseline 为骨架，用 llm 的非空值覆盖；保留 baseline 的 extraction 溯源。"""
    out = dict(baseline)
    for k, v in llm.items():
        if k == "extraction":
            continue
        if isinstance(v, dict):
            out[k] = {**(out.get(k) or {}), **{kk: vv for kk, vv in v.items() if vv not in (None, "", [])}}
        elif v not in (None, "", []):
            out[k] = v
    return out


# ---------- 合并后 schema 一致性清洗（M4 暴露的防编造护栏） ----------

def _clean_none(obj):
    if isinstance(obj, dict):
        return {k: _clean_none(v) for k, v in obj.items() if v is not None}
    if isinstance(obj, list):
        return [_clean_none(x) for x in obj if x is not None]
    return obj


def conform_card(card: dict, schema: dict, baseline: dict | None = None):
    """保证最终卡片符合 schema：递归删 None，并中和任何违反类型/枚举/额外属性的 LLM 字段。

    返回 (清洗后卡片, 被丢弃字段名列表)。处理两类违规：
      - 字典键违规（LLM 注入 schema 不存在的字段，或写错枚举/类型）：回退到 baseline 同路径
        合法值；baseline 无该字段则删除。
      - 列表项违规（如 intended_tasks / medical_fields 中出现非法枚举值）：以 baseline 列表为
        基底，仅保留 LLM 中明确「单项 schema 合法」且不重复的项，丢弃其余——既防编造，又保留
        LLM 的有效补充。
    回退/丢弃动作应在 extraction.pending_verification 中记录，保持可追溯。
    """
    import copy
    from jsonschema import Draft202012Validator

    card = _clean_none(copy.deepcopy(card))
    dropped: list[str] = []
    validator = Draft202012Validator(schema)

    def nav(node, path):
        for p in path:
            if isinstance(p, int):
                if isinstance(node, list) and 0 <= p < len(node):
                    node = node[p]
                else:
                    return None
            elif isinstance(node, dict) and p in node:
                node = node[p]
            else:
                return None
        return node

    def set_path(node, path, value):
        for p in path[:-1]:
            node = node[p]
        node[path[-1]] = value

    def del_path(node, path):
        for p in path[:-1]:
            node = node[p]
        last = path[-1]
        if isinstance(last, int):
            if isinstance(node, list) and 0 <= last < len(node):
                del node[last]
        else:
            if isinstance(node, dict) and last in node:
                del node[last]

    def list_valid(field_path, items):
        trial = copy.deepcopy(card)
        set_path(trial, field_path, items)
        for err in validator.iter_errors(trial):
            ep = list(err.path)
            if len(ep) >= len(field_path) and ep[: len(field_path)] == list(field_path):
                return False
        return True

    for _ in range(50):
        errs = list(validator.iter_errors(card))
        if not errs:
            break
        errs.sort(key=lambda e: len(list(e.path)), reverse=True)
        fixed = False
        for e in errs:
            path = list(e.path)
            if not path:
                break  # 根级错误（如缺必填）无法通过删除修复
            last = path[-1]
            if isinstance(last, int):
                # 列表项违规 → 重建：baseline 项 + LLM 中单项合法且不重复的项
                field_path = path[:-1]
                base_list = nav(baseline, field_path) if baseline is not None else None
                if not isinstance(base_list, list):
                    base_list = []
                cur_list = nav(card, field_path) or []
                existing = list(base_list)
                for item in cur_list:
                    if item in existing:
                        continue
                    cand = existing + [item]
                    if list_valid(field_path, cand):
                        existing = cand
                if existing:
                    set_path(card, field_path, existing)
                else:
                    del_path(card, field_path)
                dropped.append("/".join(map(str, field_path)) + "[list-items]")
                fixed = True
                break
            # 字典键违规 → 回退 baseline 或删除
            field_path = path
            restored = False
            if baseline is not None:
                bval = nav(baseline, field_path)
                if bval is not None:
                    set_path(card, field_path, copy.deepcopy(bval))
                    restored = True
            if not restored:
                del_path(card, field_path)
            dropped.append(last)
            fixed = True
            break
        if not fixed:
            break
    return card, dropped


if __name__ == "__main__":
    import sys
    did = sys.argv[1] if len(sys.argv) > 1 else "NIH ChestX-ray14"
    print(json.dumps(baseline_from_catalog(did), ensure_ascii=False, indent=2))
