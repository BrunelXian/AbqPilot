from __future__ import annotations

from pathlib import Path
from typing import Any

from abqpilot.diagnostics import diagnose_job_output
from abqpilot.solver.solver_artifacts import read_json, result, tail_text, write_json


def monitor_solver_run(solver_run_dir: str | Path) -> dict[str, Any]:
    run_dir = Path(solver_run_dir)
    monitor = classify_solver_run(run_dir)
    write_json(run_dir / "solver_monitor_result.json", monitor)
    return result("monitor-solver-run", monitor["status"], True, run_dir, monitor)


def classify_solver_run(solver_run_dir: str | Path) -> dict[str, Any]:
    run_dir = Path(solver_run_dir)
    preflight = read_json(run_dir / "solver_preflight_result.json")
    job_name = preflight.get("job_name") or _infer_job_name(run_dir)
    odb = run_dir / f"{job_name}.odb"
    lck = run_dir / f"{job_name}.lck"
    sta = run_dir / f"{job_name}.sta"
    dat = run_dir / f"{job_name}.dat"
    msg = run_dir / f"{job_name}.msg"
    log = run_dir / f"{job_name}.log"
    run_result = read_json(run_dir / "solver_run_result.json")
    diagnosis = diagnose_job_output(run_dir, job_name, write_artifacts=True)
    status = _solver_status_from_diagnosis(diagnosis["diagnosis_status"])
    dat_tail = tail_text(dat)
    sta_tail = tail_text(sta)
    msg_tail = tail_text(msg)
    log_tail = tail_text(log)
    if status == "SOLVER_UNKNOWN" and preflight and not run_result and not odb.exists() and not lck.exists():
        status = "SOLVER_PREPARED"
    return {
        "stage": "Stage 4.0",
        "solver_run_dir": str(run_dir),
        "job_name": job_name,
        "status": status,
        "odb_path": str(odb),
        "odb_exists": odb.exists(),
        "lock_path": str(lck),
        "lock_exists": lck.exists(),
        "sta_path": str(sta),
        "msg_path": str(msg),
        "dat_path": str(dat),
        "log_path": str(log),
        "return_code": run_result.get("return_code"),
        "diagnosis_status": diagnosis.get("diagnosis_status"),
        "failure_category": diagnosis.get("failure_category"),
        "odb_acceptable_for_metrics": diagnosis.get("odb_acceptable_for_metrics"),
        "submitted_solver": bool(run_result.get("solver_launched", False)),
        "queue_runner_launched": False,
        "opened_odb": False,
        "sta_tail": sta_tail,
        "msg_tail": msg_tail,
        "dat_tail": dat_tail,
        "log_tail": log_tail,
        "errors": [],
        "warnings": [],
    }


def _infer_job_name(run_dir: Path) -> str:
    previews = read_json(run_dir / "solver_command_preview.json")
    for item in previews.get("command", []):
        if isinstance(item, str) and item.startswith("job="):
            return item.split("=", 1)[1]
    return "candidate_sanity_base_power_x2_stage4"


def _solver_status_from_diagnosis(diagnosis_status: str) -> str:
    if diagnosis_status == "JOB_COMPLETED_ODB_ACCEPTABLE":
        return "SOLVER_COMPLETED"
    if diagnosis_status == "JOB_RUNNING_LOCK_ACTIVE":
        return "SOLVER_RUNNING"
    if diagnosis_status == "JOB_LOCKED_STALE":
        return "SOLVER_LOCKED"
    if diagnosis_status in {
        "JOB_INPUT_PROCESSOR_FAILED",
        "JOB_SOLVER_CONVERGENCE_FAILED",
        "JOB_NUMERICAL_INSTABILITY_FAILED",
        "JOB_MESH_DISTORTION_FAILED",
        "JOB_CONTACT_CONSTRAINT_FAILED",
        "JOB_MATERIAL_MODEL_FAILED",
        "JOB_THERMAL_COUPLING_FAILED",
        "JOB_LICENSE_OR_ENVIRONMENT_FAILED",
        "JOB_TERMINATED_BY_ERRORS",
        "JOB_FAILED_WITH_PARTIAL_ODB",
        "JOB_FAILED_NO_ODB",
    }:
        return "SOLVER_FAILED"
    if diagnosis_status in {"JOB_COMPLETED_ODB_MISSING", "JOB_OUTPUT_MISSING"}:
        return "SOLVER_ODB_MISSING"
    return "SOLVER_UNKNOWN"
