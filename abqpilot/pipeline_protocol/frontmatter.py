from __future__ import annotations

from pathlib import Path
from typing import Any


REQUIRED_FRONTMATTER_KEYS: dict[str, tuple[str, ...]] = {
    "run_report": (
        "doc_type",
        "task_id",
        "run_id",
        "run_name",
        "agent",
        "status",
        "risk_level",
        "forbidden_actions",
    ),
    "handoff": (
        "doc_type",
        "task_id",
        "handoff_id",
        "from_agent",
        "to_agent",
        "from_run",
        "target_run",
        "risk_level",
        "expected_output",
    ),
    "gate_decision": (
        "doc_type",
        "task_id",
        "gate_id",
        "transition",
        "risk_level",
        "decision",
        "approver_type",
        "human_approval_required",
        "required_conditions_met",
    ),
    "task_plan": ("doc_type", "task_id", "status", "risk_level"),
    "trace_index": ("doc_type", "task_id", "status"),
    "final_evidence_ledger": ("doc_type", "task_id", "status", "final_verdict"),
}


def parse_frontmatter_text(text: str) -> tuple[dict[str, Any], str]:
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}, text
    end_index = None
    for idx in range(1, len(lines)):
        if lines[idx].strip() == "---":
            end_index = idx
            break
    if end_index is None:
        return {}, text
    return _parse_minimal_yaml(lines[1:end_index]), "\n".join(lines[end_index + 1 :])


def load_frontmatter(path: str | Path) -> dict[str, Any]:
    frontmatter, _ = parse_frontmatter_text(Path(path).read_text(encoding="utf-8"))
    return frontmatter


def validate_frontmatter(path: str | Path, required_keys: tuple[str, ...] | None = None) -> dict[str, Any]:
    target = Path(path)
    if not target.exists():
        return {"valid": False, "path": str(target), "errors": [f"missing file: {target}"], "frontmatter": {}}
    frontmatter = load_frontmatter(target)
    if not frontmatter:
        return {"valid": False, "path": str(target), "errors": ["missing YAML frontmatter"], "frontmatter": {}}
    doc_type = str(frontmatter.get("doc_type", ""))
    keys = required_keys if required_keys is not None else REQUIRED_FRONTMATTER_KEYS.get(doc_type, ("doc_type",))
    missing = [key for key in keys if key not in frontmatter]
    return {
        "valid": not missing,
        "path": str(target),
        "doc_type": doc_type,
        "errors": [f"missing frontmatter key: {key}" for key in missing],
        "frontmatter": frontmatter,
    }


def _parse_minimal_yaml(lines: list[str]) -> dict[str, Any]:
    data: dict[str, Any] = {}
    current_key: str | None = None
    for raw in lines:
        if not raw.strip() or raw.strip().startswith("#"):
            continue
        if raw.startswith("  - ") and current_key:
            data.setdefault(current_key, []).append(_coerce_scalar(raw[4:].strip()))
            continue
        if raw.startswith("  ") and ":" in raw and current_key:
            nested_key, nested_value = raw.strip().split(":", 1)
            nested = data.setdefault(current_key, {})
            if isinstance(nested, dict):
                nested[nested_key.strip()] = _coerce_scalar(nested_value.strip())
            continue
        if ":" in raw:
            key, value = raw.split(":", 1)
            current_key = key.strip()
            stripped = value.strip()
            data[current_key] = {} if stripped == "" else _coerce_scalar(stripped)
    return data


def _coerce_scalar(value: str) -> Any:
    if value == "":
        return ""
    if (value.startswith('"') and value.endswith('"')) or (value.startswith("'") and value.endswith("'")):
        return value[1:-1]
    lower = value.lower()
    if lower == "true":
        return True
    if lower == "false":
        return False
    if lower in {"null", "none"}:
        return None
    try:
        return int(value)
    except ValueError:
        return value
