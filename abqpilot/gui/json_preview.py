from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from abqpilot.gui.artifact_type_classifier import classify_artifact
from abqpilot.gui.preview_safety import collect_safety_fields, find_unsafe_claims


STATUS_FIELD_NAMES = (
    "status",
    "verdict",
    "final_status",
    "diagnosis_status",
    "revalidation_status",
    "supervisor_review_status",
    "summary_status",
    "acknowledgement_status",
)

DECISION_FIELD_NAMES = ("decision", "gate_decision", "ledger_decision")


def build_json_preview(path: str | Path) -> dict[str, Any]:
    target = Path(path)
    if not target.exists() or not target.is_file():
        return _missing(target)
    try:
        text = target.read_text(encoding="utf-8", errors="replace")
        payload = json.loads(text)
    except json.JSONDecodeError as exc:
        return {
            "path": str(target),
            "filename": target.name,
            "file_type": "json",
            "exists": True,
            "parse_status": "ARTIFACT_PREVIEW_PARSE_ERROR",
            "parse_error": str(exc),
            "json_data": None,
            "pretty_json": "",
            "top_level_keys": [],
            "safety_fields": {},
            "status_fields": {},
            "decision_fields": {},
            "warning_items": [],
            "blocked_items": [str(exc)],
            "unsafe_claims": [],
            "read_only": True,
            "editable": False,
        }
    except OSError as exc:
        result = _missing(target)
        result["parse_status"] = "ARTIFACT_PREVIEW_PARSE_ERROR"
        result["blocked_items"] = [str(exc)]
        return result

    unsafe_claims = find_unsafe_claims(payload, path=str(target))
    parse_status = "ARTIFACT_PREVIEW_BLOCKED_UNSAFE_FINAL_APPROVAL_CLAIM" if unsafe_claims else "ARTIFACT_PREVIEW_READY"
    top_level_keys = list(payload.keys()) if isinstance(payload, dict) else []
    return {
        "path": str(target),
        "filename": target.name,
        "file_type": "json",
        "artifact_type": classify_artifact(target, json_data=payload),
        "exists": True,
        "parse_status": parse_status,
        "json_data": payload,
        "pretty_json": json.dumps(payload, indent=2, ensure_ascii=False),
        "top_level_keys": top_level_keys,
        "safety_fields": collect_safety_fields(payload),
        "status_fields": _selected_fields(payload, STATUS_FIELD_NAMES),
        "decision_fields": _selected_fields(payload, DECISION_FIELD_NAMES),
        "warning_items": _collect_messages(payload, "warning"),
        "blocked_items": _collect_messages(payload, "block"),
        "unsafe_claims": unsafe_claims,
        "read_only": True,
        "editable": False,
        "preview_notice": "Read-only preview. JSON contents are displayed, not executed.",
    }


def _missing(target: Path) -> dict[str, Any]:
    return {
        "path": str(target),
        "filename": target.name,
        "file_type": "json",
        "exists": False,
        "parse_status": "ARTIFACT_PREVIEW_MISSING_FILE",
        "json_data": None,
        "pretty_json": "",
        "top_level_keys": [],
        "safety_fields": {},
        "status_fields": {},
        "decision_fields": {},
        "warning_items": [],
        "blocked_items": [],
        "unsafe_claims": [],
        "read_only": True,
        "editable": False,
    }


def _selected_fields(payload: Any, names: tuple[str, ...]) -> dict[str, Any]:
    if not isinstance(payload, dict):
        return {}
    return {name: payload[name] for name in names if name in payload}


def _collect_messages(payload: Any, term: str) -> list[str]:
    messages: list[str] = []
    _walk_messages(payload, term.lower(), messages)
    return messages[:20]


def _walk_messages(payload: Any, term: str, messages: list[str]) -> None:
    if isinstance(payload, dict):
        for key, value in payload.items():
            if term in str(key).lower() and isinstance(value, (str, int, float, bool)):
                messages.append(f"{key}: {value}")
            elif isinstance(value, (dict, list)):
                _walk_messages(value, term, messages)
    elif isinstance(payload, list):
        for item in payload:
            _walk_messages(item, term, messages)
