from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from abqpilot.ui_state.event_stream import build_event_stream
from abqpilot.ui_state.module_registry import build_module_registry, module_id_for_step


def build_task_view_model(task_dir: str | Path) -> dict[str, Any]:
    task = Path(task_dir)
    state = _read_json(task / "task_state.json")
    artifacts = _read_json(task / "artifacts.json") if (task / "artifacts.json").exists() else {"artifacts": []}
    modules = build_module_registry(state, artifacts)
    events = build_event_stream(task)
    current_module_id = _select_current_module_id(state, modules)
    current_module = next((item for item in modules if item["module_id"] == current_module_id), modules[0] if modules else {})
    active_artifacts = [
        item for item in artifacts.get("artifacts", []) if item.get("producer_step") == current_module.get("step_name")
    ]
    return {
        "task_id": state.get("task_id") or task.name,
        "task_dir": str(task),
        "overall_status": state.get("status"),
        "current_module": current_module_id,
        "modules": modules,
        "events": events,
        "artifacts": artifacts.get("artifacts", []),
        "right_panel": {
            "module_name": current_module.get("display_name"),
            "status": state.get("status") or current_module.get("status"),
            "stage": current_module.get("stage"),
            "input_summary": _input_summary(state, artifacts, current_module.get("step_name")),
            "output_summary": _output_summary(events, current_module_id),
            "active_artifacts": active_artifacts,
            "last_artifact": current_module.get("last_artifact"),
            "guard_state": _guard_state(state),
            "next_allowed_action": _next_allowed_action(state.get("status"), current_module.get("last_message")),
        },
    }


def _select_current_module_id(state: dict[str, Any], modules: list[dict[str, Any]]) -> str | None:
    steps = state.get("steps", {})
    for wanted in ("FAILED", "RUNNING", "WAITING_FOR_MANUAL_ACTION", "STOPPED_BY_MODE_LIMIT"):
        for step_name, step in steps.items():
            if step.get("status") == wanted:
                return module_id_for_step(step_name)

    status_module = _module_from_status(state.get("status"))
    if status_module:
        return status_module

    current = module_id_for_step(state.get("current_step"))
    if current:
        return current

    completed_steps = list(state.get("completed_steps", []))
    if completed_steps:
        latest = completed_steps[-1]
        return module_id_for_step(latest)

    for module in reversed(modules):
        if module.get("status") == "COMPLETED":
            return module.get("module_id")
    return modules[0]["module_id"] if modules else None


def _input_summary(state: dict[str, Any], artifacts: dict[str, Any], step_name: str | None) -> str:
    if step_name == "07_abqjobpilot_status_poll":
        job_id = _artifact_field(artifacts, "abqjobpilot_real_enqueue_result", "job_id")
        return f"job_id={job_id}" if job_id else "job_id unavailable"
    return f"task_id={state.get('task_id')}"


def _output_summary(events: list[dict[str, Any]], module_id: str | None) -> str:
    for event in reversed(events):
        if event.get("module_id") == module_id and event.get("status"):
            return str(event["status"])
    return "No output yet"


def _guard_state(state: dict[str, Any]) -> str:
    flags = state.get("safety_flags", {})
    disabled = [name for name in ("allow_solver_submit", "allow_llm", "allow_codex_runtime") if flags.get(name) is False]
    return "Disabled: " + ", ".join(disabled)


def _next_allowed_action(status: str | None, last_message: str | None = None) -> str:
    status_text = status or last_message
    if status_text in {"WAITING_FOR_ABQJOBPILOT", "JOB_QUEUED", "JOB_RUNNING"}:
        return "Poll JobPilot Status"
    if status_text in {"APPROVAL_REQUIRED", "APPROVAL_TOKEN_MISSING"}:
        return "Create Approval Token"
    if status_text == "REAL_ENQUEUE_REJECTED_CONFIG_DISABLED":
        return "Enable real enqueue only with approval token"
    if status_text == "JOB_OUTPUTS_READY":
        return "Continue From Job Output"
    if status_text in {"INSUFFICIENT_METRICS", "NEED_ODB_METRICS_JSON"}:
        return "Run ODB Metrics"
    if status_text == "PASS":
        return "Export Run Report"
    if status == "STOPPED_BY_MODE_LIMIT":
        return "Resume or run the next safe deterministic step."
    if status and "FAILED" in status:
        return "Review artifacts and errors before retrying."
    return "Refresh task state."


def _module_from_status(status: str | None) -> str | None:
    if status == "WAITING_FOR_ABQJOBPILOT":
        return "status_poll"
    if status in {"JOB_OUTPUTS_READY", "JOB_ODB_MISSING", "WAITING_FOR_SOLVER_OUTPUTS", "SOLVER_JOB_FAILED"}:
        return "solver_intake"
    if status in {"APPROVAL_REQUIRED", "APPROVAL_TOKEN_MISSING", "APPROVAL_TOKEN_VALID"}:
        return "human_approval"
    if status in {"REAL_ENQUEUE_REJECTED_CONFIG_DISABLED", "REAL_ENQUEUE_COMPLETED"}:
        return "real_queue_enqueue"
    if status in {"INSUFFICIENT_METRICS", "REPAIR_RECOMMENDED", "PASS"}:
        return "evaluation"
    return None


def _artifact_field(artifacts: dict[str, Any], name: str, field: str) -> Any | None:
    for artifact in artifacts.get("artifacts", []):
        if artifact.get("name") != name:
            continue
        path = Path(artifact.get("path", ""))
        if not path.exists():
            return None
        payload = _read_json(path)
        return payload.get(field)
    return None


def _read_json(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return {}
