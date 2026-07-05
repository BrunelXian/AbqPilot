from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from abqpilot.gui.recommendation_copy import FORBIDDEN_ACTION_GUIDANCE, recommendation_safety_notes
from abqpilot.gui.recommendation_rules import recommendation_for_workflow_state
from abqpilot.gui.safe_action_catalog import get_disabled_high_risk_actions, get_safe_action_catalog
from abqpilot.gui.trace_viewer import build_trace_viewer
from abqpilot.gui.workflow_state import inspect_gui_workflow_state


def build_next_step_recommendation(task_dir: str | Path | None) -> dict[str, Any]:
    workflow_state = inspect_gui_workflow_state(task_dir)
    trace_viewer = build_trace_viewer(task_dir)
    downstream_agent = _read_downstream_agent(workflow_state)
    rule = recommendation_for_workflow_state(workflow_state, downstream_agent=downstream_agent)
    action = _catalog_action(str(rule.get("recommended_action_id")))
    disabled_actions = get_disabled_high_risk_actions()
    missing_prerequisites = _missing_prerequisites(rule, workflow_state)
    recommendation = {
        "schema_version": "0.1",
        "stage": "Stage 5.1E",
        "task_dir": workflow_state.get("task_dir"),
        "task_id": workflow_state.get("task_id"),
        "current_state": rule["current_state"],
        "current_stage_label": workflow_state.get("current_stage_label"),
        "latest_status": workflow_state.get("latest_status"),
        "latest_gate_decision": workflow_state.get("gate_records", {}).get("latest_decision"),
        "recommended_action_id": rule.get("recommended_action_id"),
        "recommended_action_label": rule.get("recommended_action_label"),
        "recommended_panel": action.get("panel") if action else rule.get("recommended_panel"),
        "recommendation_status": rule.get("recommendation_status"),
        "recommendation_rationale": rule.get("recommendation_rationale"),
        "prerequisites": rule.get("prerequisites", []),
        "missing_prerequisites": missing_prerequisites,
        "expected_outputs": rule.get("expected_outputs", []),
        "final_evidence_effect": _safe_final_effect(str((action or {}).get("final_evidence_effect") or rule.get("final_evidence_effect") or "NONE")),
        "risk_level": str((action or {}).get("risk_level") or rule.get("risk_level") or "LOW"),
        "disabled_actions_summary": [
            {
                "display_name": item.get("display_name"),
                "disabled_reason": item.get("disabled_reason"),
                "backend_method": item.get("backend_method"),
            }
            for item in disabled_actions
        ],
        "warnings": _combine_unique(rule.get("warnings", []), trace_viewer.get("unsafe_claims", [])),
        "blocked_reasons": rule.get("blocked_reasons", []),
        "non_final_boundary": workflow_state.get("non_final_boundary"),
        "safety_boundary": "Recommendation only; no automatic execution. Final evidence remains locked. Solver / ODB / metrics remain disabled. GUI does not call Codex CLI.",
        "user_instruction": rule.get("user_instruction"),
        "read_only_guidance": "The recommendation card reads workflow records and safe-action metadata only.",
        "forbidden_action_guidance": list(FORBIDDEN_ACTION_GUIDANCE),
        "safety_notes": recommendation_safety_notes(),
        "trace_viewer_state": trace_viewer.get("viewer_state"),
        "downstream_agent": downstream_agent,
        "action_allowed": False,
        "auto_execute_allowed": False,
        "codex_execution_allowed": False,
        "solver_approved": False,
        "odb_approved": False,
        "metrics_approved": False,
        "final_evidence_approved": False,
        "final_verdict_frozen": False,
    }
    _assert_recommendation_safe(recommendation)
    return recommendation


def _catalog_action(action_id: str) -> dict[str, Any] | None:
    for action in get_safe_action_catalog():
        if action.get("action_id") == action_id:
            return action
    return None


def _missing_prerequisites(rule: dict[str, Any], workflow_state: dict[str, Any]) -> list[str]:
    missing = list(rule.get("missing_prerequisites", []))
    artifacts = workflow_state.get("artifact_paths", {})
    for prerequisite in rule.get("prerequisites", []):
        text = str(prerequisite)
        if text.endswith(".json") or text.endswith(".md") or text.endswith("/"):
            if text not in json.dumps(artifacts):
                continue
    return missing


def _read_downstream_agent(workflow_state: dict[str, Any]) -> str | None:
    artifacts = workflow_state.get("artifact_paths", {})
    candidates = [
        artifacts.get("latest_revalidation_scaffold"),
        artifacts.get("latest_revalidation_result"),
    ]
    for candidate in candidates:
        if not candidate:
            continue
        payload = _read_json(candidate)
        found = _find_first_key(payload, ("downstream_agent", "revalidation_agent", "agent", "target_agent"))
        if found:
            return str(found)
    return None


def _read_json(path: str | Path) -> Any:
    target = Path(path)
    if not target.exists() or not target.is_file():
        return {}
    try:
        return json.loads(target.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError, UnicodeDecodeError):
        return {}


def _find_first_key(payload: Any, keys: tuple[str, ...]) -> Any:
    if isinstance(payload, dict):
        for key in keys:
            if key in payload:
                return payload[key]
        for value in payload.values():
            found = _find_first_key(value, keys)
            if found:
                return found
    elif isinstance(payload, list):
        for item in payload:
            found = _find_first_key(item, keys)
            if found:
                return found
    return None


def _safe_final_effect(value: str) -> str:
    if value in {"NONE", "NON_FINAL_NON_SOLVER_RECORD_ONLY"}:
        return value
    return "NONE"


def _combine_unique(values: list[Any], extra: list[Any]) -> list[Any]:
    result: list[Any] = []
    for item in [*values, *extra]:
        if item not in result:
            result.append(item)
    return result


def _assert_recommendation_safe(recommendation: dict[str, Any]) -> None:
    if recommendation["final_evidence_effect"] in {"FINAL_EVIDENCE_APPROVAL", "FINAL_VERDICT_FREEZE"}:
        raise ValueError("unsafe final evidence effect")
    unsafe_true_flags = [
        "auto_execute_allowed",
        "codex_execution_allowed",
        "solver_approved",
        "odb_approved",
        "metrics_approved",
        "final_evidence_approved",
        "final_verdict_frozen",
    ]
    for key in unsafe_true_flags:
        if recommendation.get(key) is True:
            raise ValueError(f"unsafe recommendation flag: {key}")
