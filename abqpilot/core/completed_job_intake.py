from __future__ import annotations

import json
from pathlib import Path
from typing import Any


WAITING_STATUSES = {"JOB_QUEUED", "JOB_RUNNING"}


def continue_from_job_output(task_dir: str | Path, manual_odb_path: str | Path | None = None) -> dict[str, Any]:
    task = Path(task_dir)
    state = _read_json(task / "task_state.json")
    artifacts = _read_json(task / "artifacts.json") if (task / "artifacts.json").exists() else {"artifacts": []}
    task_id = state.get("task_id") or task.name
    status_summary = _latest_status_summary(task, artifacts)
    normalized = status_summary.get("normalized_status")
    manual_path = str(manual_odb_path) if manual_odb_path is not None else None
    manual_validation = _validate_manual_odb(manual_odb_path) if manual_odb_path is not None else None

    accepted_odb_path = None
    odb_exists = bool(status_summary.get("odb_exists"))
    lock_exists = bool(status_summary.get("lock_exists"))
    continue_to_solver_intake = False
    verdict = "WAITING_FOR_ABQJOBPILOT"
    errors: list[str] = []
    warnings: list[str] = []

    if manual_validation:
        if manual_validation["accepted"]:
            accepted_odb_path = manual_validation["path"]
            odb_exists = True
            lock_exists = False
            normalized = "JOB_OUTPUTS_READY"
            verdict = "JOB_OUTPUTS_READY"
            continue_to_solver_intake = True
        else:
            verdict = manual_validation["verdict"]
            errors.extend(manual_validation["errors"])
    elif normalized == "JOB_OUTPUTS_READY":
        accepted_odb_path = status_summary.get("expected_odb_path")
        continue_to_solver_intake = True
        verdict = "JOB_OUTPUTS_READY"
    elif normalized in WAITING_STATUSES:
        verdict = "WAITING_FOR_ABQJOBPILOT"
        warnings.append("abqjobpilot job is not complete yet")
    elif normalized == "JOB_ODB_MISSING":
        verdict = "WAITING_FOR_SOLVER_OUTPUTS"
        warnings.append("job status indicates completion, but expected ODB is missing")
    elif normalized == "JOB_FAILED":
        verdict = "SOLVER_JOB_FAILED"
        errors.append("abqjobpilot job status indicates failure")
    elif not normalized:
        verdict = "NEED_ABQJOBPILOT_STATUS_SUMMARY"
        errors.append("status poll summary is missing")
    else:
        verdict = str(normalized)

    summary = {
        "task_id": task_id,
        "job_id": status_summary.get("job_id"),
        "status_poll_status": status_summary.get("raw_status"),
        "normalized_status": normalized,
        "manual_odb_path": manual_path,
        "accepted_odb_path": accepted_odb_path,
        "odb_exists": odb_exists,
        "lock_exists": lock_exists,
        "continue_to_solver_intake": continue_to_solver_intake,
        "opened_odb": False,
        "submitted_solver": False,
        "verdict": verdict,
        "errors": errors,
        "warnings": warnings,
    }
    json_path = task / "stage2_8_completed_job_intake_summary.json"
    md_path = task / "stage2_8_completed_job_intake_summary.md"
    _write_json(json_path, summary)
    md_path.write_text(_render_summary_markdown(summary), encoding="utf-8")
    _record_artifact(artifacts, "stage2_8_completed_job_intake_summary", "generated", json_path, "stage2_8_completed_job_intake")
    _record_artifact(artifacts, "stage2_8_completed_job_intake_summary_md", "generated", md_path, "stage2_8_completed_job_intake")
    if accepted_odb_path:
        _record_artifact(artifacts, "accepted_odb", "referenced", accepted_odb_path, "stage2_8_completed_job_intake")
    _write_json(task / "artifacts.json", artifacts)
    _update_task_state(task / "task_state.json", state, summary)
    return {
        "command": "continue-from-job-output",
        "verdict": verdict,
        "success": not errors and verdict
        in {
            "JOB_OUTPUTS_READY",
            "WAITING_FOR_ABQJOBPILOT",
            "WAITING_FOR_SOLVER_OUTPUTS",
            "SOLVER_JOB_FAILED",
        },
        "output_paths": {
            "stage2_8_completed_job_intake_summary_json": str(json_path),
            "stage2_8_completed_job_intake_summary_md": str(md_path),
        },
        "warnings": warnings,
        "errors": errors,
        "details": summary,
    }


def _latest_status_summary(task: Path, artifacts: dict[str, Any]) -> dict[str, Any]:
    artifact = next(
        (item for item in artifacts.get("artifacts", []) if item.get("name") == "abqjobpilot_status_summary"),
        None,
    )
    candidates = []
    if artifact:
        candidates.append(Path(artifact["path"]))
    candidates.append(task / "steps" / "07_abqjobpilot_status_poll" / "abqjobpilot_status_summary.json")
    for path in candidates:
        if path.exists():
            return _read_json(path)
    return {}


def _validate_manual_odb(path: str | Path | None) -> dict[str, Any]:
    target = Path(path) if path is not None else None
    if target is None:
        return {"accepted": False, "verdict": "MISSING_MANUAL_ODB_PATH", "errors": ["manual ODB path is required"]}
    if not target.exists():
        return {"accepted": False, "verdict": "MANUAL_ODB_MISSING", "path": str(target), "errors": [f"ODB does not exist: {target}"]}
    if target.suffix.lower() != ".odb":
        return {
            "accepted": False,
            "verdict": "MANUAL_ODB_INVALID_EXTENSION",
            "path": str(target),
            "errors": [f"manual output is not an .odb file: {target}"],
        }
    lock_path = target.with_suffix(".lck")
    if lock_path.exists():
        return {
            "accepted": False,
            "verdict": "MANUAL_ODB_LOCKED",
            "path": str(target),
            "errors": [f"lock file exists beside ODB: {lock_path}"],
        }
    return {"accepted": True, "verdict": "JOB_OUTPUTS_READY", "path": str(target), "errors": []}


def _update_task_state(path: Path, state: dict[str, Any], summary: dict[str, Any]) -> None:
    verdict = summary["verdict"]
    if verdict == "JOB_OUTPUTS_READY":
        state["status"] = "JOB_OUTPUTS_READY"
        state["stop_reason"] = "JOB_OUTPUTS_READY"
        state["requires_human_action"] = False
        state["human_action_reason"] = None
    elif verdict == "WAITING_FOR_ABQJOBPILOT":
        state["status"] = "WAITING_FOR_ABQJOBPILOT"
        state["stop_reason"] = "WAITING_FOR_ABQJOBPILOT"
        state["requires_human_action"] = False
        state["human_action_reason"] = None
    elif verdict == "WAITING_FOR_SOLVER_OUTPUTS":
        state["status"] = "WAITING_FOR_SOLVER_OUTPUTS"
        state["stop_reason"] = "WAITING_FOR_SOLVER_OUTPUTS"
        state["requires_human_action"] = True
        state["human_action_reason"] = "Existing solver output ODB is required before continuation."
    elif verdict == "SOLVER_JOB_FAILED":
        state["status"] = "SOLVER_JOB_FAILED"
        state["stop_reason"] = "SOLVER_JOB_FAILED"
        state["requires_human_action"] = True
        state["human_action_reason"] = "abqjobpilot reports that the queued solver job failed."
    _write_json(path, state)


def _record_artifact(
    artifacts: dict[str, Any],
    name: str,
    kind: str,
    path: str | Path,
    producer_step: str,
) -> None:
    payload = {
        "name": name,
        "kind": kind,
        "path": str(path),
        "exists": Path(path).exists(),
        "producer_step": producer_step,
    }
    for item in artifacts.setdefault("artifacts", []):
        if item.get("name") == name:
            item.update(payload)
            return
    artifacts["artifacts"].append(payload)


def _render_summary_markdown(summary: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# Stage 2.8 Completed Job Intake Summary",
            "",
            f"Task ID: `{summary.get('task_id')}`",
            f"Verdict: `{summary.get('verdict')}`",
            "",
            "## Evidence",
            "",
            f"- Job ID: `{summary.get('job_id')}`",
            f"- Status poll status: `{summary.get('status_poll_status')}`",
            f"- Normalized status: `{summary.get('normalized_status')}`",
            f"- Manual ODB path: `{summary.get('manual_odb_path')}`",
            f"- Accepted ODB path: `{summary.get('accepted_odb_path')}`",
            f"- ODB exists: `{summary.get('odb_exists')}`",
            f"- Lock exists: `{summary.get('lock_exists')}`",
            f"- Continue to solver intake: `{summary.get('continue_to_solver_intake')}`",
            "",
            "## Safety",
            "",
            "- Opened ODB: `False`",
            "- Submitted solver: `False`",
        ]
    ) + "\n"


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
