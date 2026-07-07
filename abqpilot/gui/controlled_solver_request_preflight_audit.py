from __future__ import annotations

from pathlib import Path
from typing import Any


PASS = "CONTROLLED_SOLVER_REQUEST_PREFLIGHT_NO_EXECUTION_AUDIT_PASS"
FAIL = "CONTROLLED_SOLVER_REQUEST_PREFLIGHT_NO_EXECUTION_AUDIT_FAIL"
ACTIVE_REQUEST_NAMES = {"solver_request.json", "job_request.json", "abaqus_job.json"}


def audit_controlled_solver_request_preflight_no_execution(task_dir: str | Path, preflight: dict[str, Any] | None = None) -> dict[str, Any]:
    task = Path(task_dir)
    active_request_files = [str(path) for path in task.rglob("*") if path.is_file() and path.name in ACTIVE_REQUEST_NAMES] if task.exists() else []
    bat_files = [str(path) for path in task.rglob("*.bat")] if task.exists() else []
    cmd_files = [str(path) for path in task.rglob("*.cmd")] if task.exists() else []
    queue_files = [str(path) for path in task.rglob("*") if path.name.lower() in {"queue.json", "live_status.json"}] if task.exists() else []
    odb_files = [str(path) for path in task.rglob("*.odb")] if task.exists() else []
    metrics_files = [str(path) for path in task.rglob("*metrics*") if path.is_file()] if task.exists() else []
    active_handoffs = _active_handoff_files(task / "handoffs") if (task / "handoffs").exists() else []
    final_ledger = task / "TASK_FINAL_EVIDENCE_LEDGER.md"
    preflight = preflight or {}
    checks = {
        "no_solver_request_files_found": not any(Path(path).name == "solver_request.json" for path in active_request_files),
        "no_job_request_files_found": not any(Path(path).name == "job_request.json" for path in active_request_files),
        "no_abaqus_job_files_found": not any(Path(path).name == "abaqus_job.json" for path in active_request_files),
        "no_bat_solver_launcher_found": not bat_files,
        "no_cmd_solver_launcher_found": not cmd_files,
        "no_active_handoff_files_found": not active_handoffs,
        "no_queue_files_found": not queue_files,
        "no_odb_files_found": not odb_files,
        "no_metrics_files_found": not metrics_files,
        "no_task_final_evidence_ledger": not final_ledger.exists(),
        "preflight_solver_run_false": preflight.get("solver_run") is not True,
        "preflight_solver_execution_allowed_false": preflight.get("solver_execution_allowed") is not True,
        "preflight_request_active_false": preflight.get("request_active") is not True,
        "preflight_executable_request_false": preflight.get("executable_request") is not True,
        "preflight_downstream_execution_auto_start_false": preflight.get("downstream_execution_auto_start") is not True,
    }
    return {
        "schema_version": "0.1",
        "stage": "Stage 5.2I",
        "audit_status": PASS if all(checks.values()) else FAIL,
        "checks": checks,
        "active_request_files": active_request_files,
        "bat_files": bat_files,
        "cmd_files": cmd_files,
        "active_handoff_files": active_handoffs,
        "queue_files": queue_files,
        "odb_files": odb_files,
        "metrics_files": metrics_files,
        "no_solver_request_files_found": checks["no_solver_request_files_found"],
        "no_active_handoff_files_found": checks["no_active_handoff_files_found"],
        "no_queue_files_found": checks["no_queue_files_found"],
        "no_odb_files_found": checks["no_odb_files_found"],
        "no_metrics_files_found": checks["no_metrics_files_found"],
        "solver_execution_allowed": False,
        "solver_request_created": False,
        "solver_run": False,
        "final_evidence_approved": False,
        "final_verdict_frozen": False,
    }


def _active_handoff_files(handoff_dir: Path) -> list[str]:
    active: list[str] = []
    for path in handoff_dir.glob("HANDOFF_*.md"):
        text = path.read_text(encoding="utf-8").lower()
        if "handoff_active_for_execution: true" in text or "solver_auto_start: true" in text:
            active.append(str(path))
    return active
