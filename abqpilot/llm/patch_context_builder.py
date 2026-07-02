from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from abqpilot.llm.patch_proposal_schema import ALLOWED_PATCH_TYPES, FORBIDDEN_PATCH_TYPES


def build_patch_context(task_dir: str | Path, max_chars: int = 12000) -> dict[str, Any]:
    task = Path(task_dir)
    state = _read_json(task / "task_state.json")
    artifacts = _read_json(task / "artifacts.json").get("artifacts", [])
    evaluation = _find_json(task, artifacts, "evaluation_json", ["analysis/evaluation.json"])
    repair_plan = _find_json(task, artifacts, "repair_plan_json", ["analysis/repair_plan.json"])
    reasoning = _read_json(task / "llm_reasoning" / "llm_reasoning_result.json")
    context = {
        "schema_version": "0.1",
        "task_id": state.get("task_id") or task.name,
        "current_status": state.get("status"),
        "evaluation": _evaluation_summary(evaluation),
        "deterministic_repair_plan": _repair_plan_summary(repair_plan),
        "current_llm_reasoning": {
            "verdict": reasoning.get("verdict"),
            "recommended_next_action": reasoning.get("recommended_next_action"),
            "risk_flags": reasoning.get("risk_flags", []),
        },
        "pipeline": {
            "current_step": state.get("current_step"),
            "stop_reason": state.get("stop_reason"),
            "failed_steps": state.get("failed_steps", []),
        },
        "artifact_refs": [
            {"name": item.get("name"), "kind": item.get("kind"), "file": Path(str(item.get("path", ""))).name}
            for item in artifacts[:40]
        ],
        "safety_boundaries": {
            "llm_can_mutate_inp": False,
            "llm_can_submit_solver": False,
            "llm_can_enqueue": False,
            "patch_application_requires_static_validator": True,
            "patch_application_requires_diff_guard": True,
            "patch_application_requires_physics_guard": True,
            "includes_full_inp": False,
            "includes_odb_content": False,
            "includes_cae_content": False,
            "includes_secret": False,
            "includes_full_logs": False,
        },
        "allowed_patch_types": sorted(ALLOWED_PATCH_TYPES),
        "forbidden_patch_types": sorted(FORBIDDEN_PATCH_TYPES),
    }
    return _enforce_limit(context, max_chars)


def _evaluation_summary(evaluation: dict[str, Any]) -> dict[str, Any]:
    return {
        "verdict": evaluation.get("evaluation_verdict") or evaluation.get("verdict"),
        "observations": evaluation.get("observations", [])[:10] if isinstance(evaluation.get("observations", []), list) else [],
        "metrics_summary": _compact_dict(evaluation.get("metrics_summary", {})),
        "errors": evaluation.get("errors", [])[:5] if isinstance(evaluation.get("errors", []), list) else [],
    }


def _repair_plan_summary(repair_plan: dict[str, Any]) -> dict[str, Any]:
    return {
        "evaluation_verdict": repair_plan.get("evaluation_verdict"),
        "repair_required": repair_plan.get("repair_required"),
        "recommended_next_action": repair_plan.get("recommended_next_action"),
        "allowed_patch_types": repair_plan.get("allowed_patch_types", []),
        "forbidden_patch_types": repair_plan.get("forbidden_patch_types", []),
    }


def _find_json(task: Path, artifacts: list[dict[str, Any]], artifact_name: str, fallbacks: list[str]) -> dict[str, Any]:
    for item in artifacts:
        if item.get("name") == artifact_name:
            path = Path(str(item.get("path", "")))
            if path.exists() and path.is_file():
                return _read_json(path)
    for fallback in fallbacks:
        path = task / fallback
        if path.exists():
            return _read_json(path)
    return {}


def _compact_dict(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        return {}
    compact: dict[str, Any] = {}
    for key, item in list(value.items())[:20]:
        if isinstance(item, (str, int, float, bool)) or item is None:
            compact[str(key)] = item
        elif isinstance(item, dict):
            compact[str(key)] = {str(k): v for k, v in list(item.items())[:5] if isinstance(v, (str, int, float, bool)) or v is None}
    return compact


def _read_json(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return {}


def _enforce_limit(context: dict[str, Any], max_chars: int) -> dict[str, Any]:
    context["input_truncated"] = False
    if len(json.dumps(context, ensure_ascii=False, sort_keys=True)) <= max_chars:
        return context
    context["input_truncated"] = True
    context["artifact_refs"] = context.get("artifact_refs", [])[:12]
    if len(json.dumps(context, ensure_ascii=False, sort_keys=True)) <= max_chars:
        return context
    context["evaluation"]["observations"] = context["evaluation"].get("observations", [])[:3]
    context["evaluation"]["metrics_summary"] = {}
    return context
