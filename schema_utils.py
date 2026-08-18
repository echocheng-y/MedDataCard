"""ST 数据卡 schema 加载与校验。"""
from __future__ import annotations

import json
from pathlib import Path

import jsonschema

SCHEMA_PATH = Path(__file__).parent / "st_datacard.schema.json"


def load_schema(path: Path | None = None) -> dict:
    path = Path(path) if path else SCHEMA_PATH
    return json.loads(Path(path).read_text(encoding="utf-8"))


def validate_card(card: dict, schema: dict | None = None) -> tuple[bool, list[str]]:
    """返回 (是否通过, 错误信息列表)。"""
    schema = schema or load_schema()
    validator = jsonschema.Draft202012Validator(schema)
    errors = [f"{'/'.join(str(e.path) or '<root>')}: {e.message}" for e in validator.iter_errors(card)]
    return (len(errors) == 0, errors)
