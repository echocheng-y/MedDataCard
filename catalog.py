"""读取 dataset_catalog.xlsx，输出 26 个数据集的元数据列表。

这是 MedDataCard 的「事实基准」：所有数据集事实以该目录为准，
任何未在目录中确认的信息都应标记 pending_verification，禁止编造。
"""
from __future__ import annotations

import openpyxl
from pathlib import Path

CATALOG_PATH = Path(__file__).parent / "dataset_catalog.xlsx"

# 中文模态关键词 → ST schema 模态枚举
_MODALITY_MAP = [
    ("X线", "X-ray"),
    ("CT", "CT"),
    ("MRI", "MRI"),
    ("磁共振", "MRI"),
    ("病理", "pathology-WSI"),
    ("皮肤镜", "dermoscopy"),
    ("超声", "ultrasound"),
    ("眼底", "fundus"),
    ("EEG", "EEG"),
    ("脑电", "EEG"),
    ("ECG", "ECG"),
    ("心电", "ECG"),
    ("EHR", "EHR"),
    ("电子健康", "EHR"),
    ("组学", "genomic"),
    ("基因", "genomic"),
    ("单细胞", "single-cell"),
    ("转录", "single-cell"),
    ("文本", "text"),
    ("报告", "text"),
    ("QA", "text"),
    ("问答", "text"),
]

# 局限文本中的国家/地区关键词 → 推断国家（仅作提示，需人工核实）
_GEO_HINTS = {
    "美国": "United States",
    "美欧": ["United States", "Europe"],
    "欧洲": "Europe",
    "西班牙": "Spain",
    "越南": "Vietnam",
    "英国": "United Kingdom",
    "伊斯坦布尔": "Turkey",
    "土耳其": "Turkey",
    "巴西": "Brazil",
    "中国": "China",
    "印度": "India",
    "日本": "Japan",
}

# 医学研究领域划分（与 schema 的 medical_fields enum 对齐）。
# 当前 26 数据集暂无明确归属中医学/中药学/妇产科学/外科学的样本，维度保留以待扩展。
MEDICAL_FIELD_MAP = {
    "NIH ChestX-ray14": ["影像学"],
    "CheXpert": ["影像学"],
    "MIMIC-CXR": ["影像学", "临床医学"],
    "PadChest": ["影像学"],
    "VinDr-CXR": ["影像学"],
    "BraTS 2024": ["影像学"],
    "ISIC 2024/历年": ["影像学", "临床医学"],
    "HAM10000": ["影像学"],
    "MedMNIST": ["影像学"],
    "TotalSegmentator": ["影像学"],
    "CT-RATE": ["影像学", "临床医学"],
    "NIH DeepLesion": ["影像学"],
    "UK Biobank": ["临床医学"],
    "TCGA": ["基础医学", "临床医学"],
    "ADNI": ["临床医学", "影像学"],
    "Tabula Sapiens": ["基础医学"],
    "MIMIC-IV": ["临床医学"],
    "eICU-CRD": ["临床医学"],
    "Sleep-EDF Expanded": ["临床医学"],
    "CHB-MIT": ["临床医学"],
    "PhysioNet/CinC 2020": ["临床医学"],
    "PMC-Patients": ["临床医学"],
    "MedQA": ["临床医学"],
    "MedMCQA": ["临床医学"],
    "PubMedQA": ["基础医学"],
    "BioASQ": ["基础医学"],
}


def load_catalog(path: Path | None = None) -> list[dict]:
    """返回数据集字典列表，key 与 schema 尽量对齐。"""
    path = Path(path) if path else CATALOG_PATH
    wb = openpyxl.load_workbook(path, data_only=True)
    ws = wb.active
    rows = list(ws.iter_rows(values_only=True))
    header = [str(h).strip() if h else "" for h in rows[0]]
    records = []
    for r in rows[1:]:
        if r is None or all(c is None for c in r):
            continue
        rec = {header[i]: (r[i] if i < len(r) else None) for i in range(len(header))}
        records.append(_normalize(rec))
    return records


def _normalize(rec: dict) -> dict:
    name = str(rec.get("数据集", "") or "").strip()
    modality_text = str(rec.get("模态", "") or "")
    limitation = str(rec.get("主要局限", "") or "")
    link = str(rec.get("链接", "") or "").strip()
    license_ = str(rec.get("许可证", "") or "").strip()
    return {
        "id": name,
        "name": name,
        "platform": str(rec.get("平台", "") or "").strip(),
        "modality_text": modality_text,
        "modalities": map_modalities(modality_text),
        "scale": str(rec.get("规模", "") or "").strip(),
        "task": str(rec.get("任务", "") or "").strip(),
        "license": license_,
        "link": link,
        "limitation": limitation,
        # 从局限文本启发式推断地理（标记待核实）
        "geo_hints": infer_geo(limitation),
        # 医学研究领域划分（分类标签，非推断）
        "medical_fields": MEDICAL_FIELD_MAP.get(name, ["其他"]),
    }


def map_modalities(text: str) -> list[str]:
    found = []
    for kw, enum in _MODALITY_MAP:
        if kw in text and enum not in found:
            found.append(enum)
    # 多模态 / 通用描述兜底
    if not found:
        found = ["other"]
    return found


def infer_geo(text: str) -> list[str]:
    out = []
    for kw, val in _GEO_HINTS.items():
        if kw in text:
            out.extend(val if isinstance(val, list) else [val])
    # 去重保序
    seen, uniq = set(), []
    for c in out:
        if c not in seen:
            seen.add(c)
            uniq.append(c)
    return uniq


if __name__ == "__main__":
    for d in load_catalog():
        print(f"{d['id']:20s} | {','.join(d['modalities']):30s} | {d['license']}")
