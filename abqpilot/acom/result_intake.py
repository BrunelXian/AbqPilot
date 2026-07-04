from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from abqpilot.acom.handoff_builder import validate_codex_handoff
from abqpilot.acom.result_pipeline_intake import intake_pipeline_acom_result
from abqpilot.acom.result_schema import unsafe_safety_flags, validate_structured_result


def intake_codex_result(handoff_dir: str | Path, result_json: str | Path) -> dict[str, Any]:
    handoff_root = Path(handoff_dir)
    manifest_path = handoff_root / "handoff_manifest.json"
    if _looks_like_pipeline_handoff(handoff_root, manifest_path):
        return intake_pipeline_acom_result(handoff_root, result_json)

    handoff = validate_codex_handoff(handoff_dir)
    result_path = Path(result_json)
    errors: list[str] = []
    if not handoff["success"]:
        errors.extend(handoff["errors"])
    if not result_path.exists():
        return {
            "command": "intake-codex-result",
            "verdict": "ACOM_RESULT_BLOCKED_MISSING_RESULT",
            "success": False,
            "errors": [f"missing structured result JSON: {result_path}"],
            "warnings": [],
            "handoff_dir": str(handoff_dir),
            "result_json": str(result_path),
            "details": {},
        }
    result = json.loads(result_path.read_text(encoding="utf-8"))
    valid, schema_errors = validate_structured_result(result)
    errors.extend(schema_errors)
    manifest = handoff.get("details") or {}
    if manifest:
        if result.get("task_id") != manifest.get("task_id"):
            return {
                "command": "intake-codex-result",
                "verdict": "ACOM_RESULT_REJECTED_TASK_MISMATCH",
                "success": False,
                "errors": ["result task_id does not match handoff manifest"],
                "warnings": [],
                "handoff_dir": str(handoff_dir),
                "result_json": str(result_path),
                "details": {"abqpilot_revalidation_required": True},
            }
        if result.get("handoff_id") != manifest.get("handoff_id"):
            return {
                "command": "intake-codex-result",
                "verdict": "ACOM_RESULT_REJECTED_HANDOFF_MISMATCH",
                "success": False,
                "errors": ["result handoff_id does not match handoff manifest"],
                "warnings": [],
                "handoff_dir": str(handoff_dir),
                "result_json": str(result_path),
                "details": {"abqpilot_revalidation_required": True},
            }
    unsafe = unsafe_safety_flags(result)
    if unsafe:
        return {
            "command": "intake-codex-result",
            "verdict": "ACOM_RESULT_REJECTED_SAFETY_FLAGS",
            "success": False,
            "errors": errors,
            "warnings": [f"unsafe safety flags: {', '.join(unsafe)}"],
            "handoff_dir": str(handoff_dir),
            "result_json": str(result_path),
            "details": {
                "unsafe_safety_flags": unsafe,
                "abqpilot_revalidation_required": True,
            },
        }
    if errors or not valid:
        return {
            "command": "intake-codex-result",
            "verdict": "ACOM_RESULT_REJECTED_SCHEMA_INVALID",
            "success": False,
            "errors": errors,
            "warnings": [],
            "handoff_dir": str(handoff_dir),
            "result_json": str(result_path),
            "details": {"abqpilot_revalidation_required": True},
        }
    return {
        "command": "intake-codex-result",
        "verdict": "ACOM_RESULT_ACCEPTED_PENDING_REVALIDATION",
        "success": True,
        "errors": [],
        "warnings": ["AbqPilot deterministic revalidation is still required."],
        "handoff_dir": str(handoff_dir),
        "result_json": str(result_path),
        "details": {
            "task_id": result.get("task_id"),
            "handoff_id": result.get("handoff_id"),
            "abqpilot_revalidation_required": True,
            "codex_summary_is_final_evidence": False,
            "accepted_as_evidence": False,
        },
    }


def _looks_like_pipeline_handoff(handoff_root: Path, manifest_path: Path) -> bool:
    if handoff_root.name == "codex_handoff" and (handoff_root.parent / "TRACE_INDEX.md").exists():
        return True
    if not manifest_path.exists():
        return False
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return False
    return bool(manifest.get("pipeline_task_dir") or manifest.get("requires_pipeline_protocol"))
