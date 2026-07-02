from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def build_sanitized_task_summary(task_dir: str | Path, max_chars: int = 12000) -> dict[str, Any]:
    task = Path(task_dir)
    state = _read_json(task / "task_state.json")
    artifacts = _read_json(task / "artifacts.json").get("artifacts", []) if (task / "artifacts.json").exists() else []
    view_model = _build_view_model(task)
    right_panel = view_model.get("right_panel", {})
    step_statuses = {
        name: {
            "status": step.get("status"),
            "verdict": step.get("verdict"),
            "rerun_count": step.get("rerun_count", 0),
        }
        for name, step in state.get("steps", {}).items()
    }
    jobpilot = _jobpilot_summary(task, artifacts)
    summary = {
        "schema_version": "0.1",
        "task_id": state.get("task_id") or task.name,
        "overall_status": state.get("status"),
        "current_module": view_model.get("current_module") or state.get("current_step"),
        "right_panel": {
            "module_name": right_panel.get("module_name"),
            "status": right_panel.get("status"),
            "next_allowed_action": right_panel.get("next_allowed_action"),
        },
        "pipeline": {
            "latest_step": state.get("current_step"),
            "step_statuses": step_statuses,
            "completed_steps": state.get("completed_steps", []),
            "failed_steps": state.get("failed_steps", []),
            "skipped_steps": state.get("skipped_steps", []),
            "stop_reason": state.get("stop_reason"),
        },
        "jobpilot": jobpilot,
        "evaluation_summary": _named_json_summary(artifacts, "evaluation_json", allowed_keys={"evaluation_verdict", "verdict"}),
        "repair_plan_summary": _named_json_summary(
            artifacts,
            "repair_plan_json",
            allowed_keys={"evaluation_verdict", "repair_required", "recommended_next_action", "requires_human_review"},
        ),
        "artifact_refs": [
            {"name": item.get("name"), "kind": item.get("kind"), "file": _basename(item.get("path"))}
            for item in artifacts[:40]
        ],
        "safety_boundaries": {
            "llm_can_execute_actions": False,
            "solver_submit_allowed": False,
            "queue_runner_allowed": False,
            "auto_inp_mutation_allowed": False,
            "direct_odb_open_allowed": False,
            "real_enqueue_requires_approval_token": True,
            "includes_full_inp": False,
            "includes_odb_content": False,
            "includes_cae_content": False,
            "includes_secret": False,
            "includes_full_logs": False,
        },
    }
    summary = _enforce_limit(summary, max_chars)
    return summary


def _read_json(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def _build_view_model(task: Path) -> dict[str, Any]:
    try:
        from abqpilot.ui_state.view_model import build_task_view_model

        return build_task_view_model(task)
    except Exception:
        return {}


def _jobpilot_summary(task: Path, artifacts: list[dict[str, Any]]) -> dict[str, Any]:
    real_enqueue = _read_known_step_json(task, "06_abqjobpilot_real_enqueue", "abqjobpilot_real_enqueue_result.json")
    status = _read_known_step_json(task, "07_abqjobpilot_status_poll", "abqjobpilot_status_summary.json")
    return {
        "job_id": status.get("job_id") or real_enqueue.get("job_id"),
        "raw_status": status.get("raw_status"),
        "normalized_status": status.get("normalized_status"),
        "expected_odb_known": bool(status.get("expected_odb_path")),
        "odb_exists": bool(status.get("odb_exists")),
        "lock_exists": bool(status.get("lock_exists")),
        "queue_only": _bool_or_none(real_enqueue.get("queue_only")),
        "solver_started": _bool_or_none(real_enqueue.get("solver_started")),
        "runner_started": _bool_or_none(real_enqueue.get("runner_started")),
        "gui_required": _bool_or_none(real_enqueue.get("gui_required")),
    }


def _read_known_step_json(task: Path, step: str, filename: str) -> dict[str, Any]:
    direct = task / "steps" / step / filename
    if direct.exists():
        return _read_json(direct)
    return {}


def _named_json_summary(artifacts: list[dict[str, Any]], name: str, allowed_keys: set[str]) -> dict[str, Any]:
    for artifact in artifacts:
        if artifact.get("name") != name:
            continue
        path = Path(str(artifact.get("path", "")))
        if not path.exists():
            return {"artifact": name, "available": False}
        payload = _read_json(path)
        return {key: payload.get(key) for key in sorted(allowed_keys) if key in payload}
    return {}


def _basename(path: Any) -> str | None:
    if not path:
        return None
    return Path(str(path)).name


def _bool_or_none(value: Any) -> bool | None:
    if value is None:
        return None
    return bool(value)


def _enforce_limit(summary: dict[str, Any], max_chars: int) -> dict[str, Any]:
    summary["input_truncated"] = False
    if len(json.dumps(summary, ensure_ascii=False, sort_keys=True)) <= max_chars:
        return summary
    summary["input_truncated"] = True
    summary["artifact_refs"] = summary.get("artifact_refs", [])[:12]
    if len(json.dumps(summary, ensure_ascii=False, sort_keys=True)) <= max_chars:
        return summary
    statuses = summary.get("pipeline", {}).get("step_statuses", {})
    summary["pipeline"]["step_statuses"] = {
        key: value for key, value in statuses.items() if value.get("status") in {"FAILED", "RUNNING", "WAITING_FOR_MANUAL_ACTION"}
    }
    if len(json.dumps(summary, ensure_ascii=False, sort_keys=True)) <= max_chars:
        return summary
    summary["evaluation_summary"] = {}
    summary["repair_plan_summary"] = {}
    return summary
