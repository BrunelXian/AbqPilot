from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from abqpilot.diagnostics.diagnosis_artifacts import write_diagnosis_artifacts
from abqpilot.diagnostics.diagnosis_report import render_diagnosis_summary
from abqpilot.diagnostics.diagnosis_schema import (
    JOB_COMPLETED_ODB_ACCEPTABLE,
    JOB_COMPLETED_ODB_MISSING,
    JOB_CONTACT_CONSTRAINT_FAILED,
    JOB_INPUT_PROCESSOR_FAILED,
    JOB_LICENSE_OR_ENVIRONMENT_FAILED,
    JOB_LOCKED_STALE,
    JOB_MATERIAL_MODEL_FAILED,
    JOB_MESH_DISTORTION_FAILED,
    JOB_NUMERICAL_INSTABILITY_FAILED,
    JOB_ODB_EXISTS_BUT_COMPLETION_NOT_PROVEN,
    JOB_RUNNING_LOCK_ACTIVE,
    JOB_SOLVER_CONVERGENCE_FAILED,
    JOB_STATUS_UNKNOWN,
    JOB_TERMINATED_BY_ERRORS,
    JOB_THERMAL_COUPLING_FAILED,
    SCHEMA_VERSION,
    STAGE,
    category_for_status,
)
from abqpilot.diagnostics.job_log_parser import parse_job_logs
from abqpilot.diagnostics.abqjobpilot_record_reader import normalize_abqjobpilot_record


STALE_LOCK_SECONDS = 30 * 60


def diagnose_job_output(
    job_dir: str | Path,
    job_name: str,
    dat: str | Path | None = None,
    msg: str | Path | None = None,
    sta: str | Path | None = None,
    log: str | Path | None = None,
    com: str | Path | None = None,
    prt: str | Path | None = None,
    odb: str | Path | None = None,
    lck: str | Path | None = None,
    diagnosis_input_mode: str = "directory",
    abqjobpilot_record: dict[str, Any] | None = None,
    artifact_dir: str | Path | None = None,
    write_artifacts: bool = True,
) -> dict[str, Any]:
    root = Path(job_dir)
    normalized_record = normalize_abqjobpilot_record(abqjobpilot_record or {}, abqjobpilot_record.get("record_path") if abqjobpilot_record else None) if abqjobpilot_record else None
    files = (
        _resolve_files_from_record(root, job_name, normalized_record)
        if normalized_record
        else _resolve_files(root, job_name, dat=dat, msg=msg, sta=sta, log=log, com=com, prt=prt, odb=odb, lck=lck)
    )
    request = {
        "schema_version": SCHEMA_VERSION,
        "stage": STAGE,
        "diagnosis_input_mode": diagnosis_input_mode,
        "job_dir": str(root),
        "job_name": job_name,
        "files": {key: str(path) for key, path in files.items()},
        "abqjobpilot_record": _record_request_summary(normalized_record),
        "opened_odb": False,
        "submitted_solver": False,
        "queue_runner_launched": False,
        "llm_used": False,
    }
    parsed = parse_job_logs(files)
    evidence = _file_evidence(files, parsed["flags"])
    status = _decide_status(evidence, parsed["flags"], files)
    category = category_for_status(status)
    acceptable = status == JOB_COMPLETED_ODB_ACCEPTABLE and evidence["odb_exists"] and not evidence["lock_exists"]
    result = {
        "schema_version": SCHEMA_VERSION,
        "stage": STAGE,
        "diagnosis_input_mode": diagnosis_input_mode,
        "abqjobpilot_record": _record_result_summary(normalized_record),
        "job_dir": str(root),
        "job_name": job_name,
        "diagnosis_status": status,
        "failure_category": category,
        "odb_acceptable_for_metrics": acceptable,
        "recommended_next_action": _recommended_next_action(status),
        "evidence": evidence,
        "failure_location": parsed["failure_location"],
        "parser_mode": parsed.get("attempt", {}).get("parser_mode", "whole_file"),
        "attempt": parsed.get("attempt", {}),
        "files": {key: str(path) for key, path in files.items()},
        "important_lines": parsed["important_lines"],
        "safety_flags": {
            "opened_odb": False,
            "submitted_solver": False,
            "queue_runner_launched": False,
            "llm_used": False,
        },
        "warnings": [],
        "errors": [],
    }
    if write_artifacts:
        result["artifact_paths"] = write_diagnosis_artifacts(
            artifact_dir or root,
            request,
            result,
            render_diagnosis_summary(result),
        )
    return result


def diagnose_abqjobpilot_record(
    record: dict[str, Any],
    artifact_dir: str | Path,
    write_artifacts: bool = True,
) -> dict[str, Any]:
    normalized = normalize_abqjobpilot_record(record, record.get("record_path"))
    work_dir = normalized.get("work_dir") or Path(artifact_dir)
    job_name = normalized.get("job_name") or normalized.get("job_id") or "abqjobpilot_job"
    return diagnose_job_output(
        job_dir=work_dir,
        job_name=str(job_name),
        diagnosis_input_mode="abqjobpilot_record",
        abqjobpilot_record=normalized,
        artifact_dir=artifact_dir,
        write_artifacts=write_artifacts,
    )


def _resolve_files(root: Path, job_name: str, **overrides: str | Path | None) -> dict[str, Path]:
    suffixes = {
        "dat": ".dat",
        "msg": ".msg",
        "sta": ".sta",
        "log": ".log",
        "com": ".com",
        "prt": ".prt",
        "odb": ".odb",
        "lck": ".lck",
    }
    files: dict[str, Path] = {}
    for key, suffix in suffixes.items():
        value = overrides.get(key)
        files[key] = Path(value) if value else root / f"{job_name}{suffix}"
    return files


def _resolve_files_from_record(root: Path, job_name: str, record: dict[str, Any]) -> dict[str, Path]:
    files = _resolve_files(root, job_name)
    for key, field in {
        "dat": "dat_path",
        "msg": "msg_path",
        "sta": "sta_path",
        "log": "log_path",
        "odb": "odb_path",
        "lck": "lck_path",
    }.items():
        value = record.get(field)
        if value:
            files[key] = Path(value)
    return files


def _record_request_summary(record: dict[str, Any] | None) -> dict[str, Any] | None:
    if not record:
        return None
    return {
        "record_path": record.get("record_path"),
        "record_kind": record.get("record_kind"),
        "job_id": record.get("job_id"),
        "raw_status": record.get("raw_status"),
        "fatal_reason": record.get("fatal_reason"),
        "return_code": record.get("return_code"),
        "paths_source": "abqjobpilot_record",
    }


def _record_result_summary(record: dict[str, Any] | None) -> dict[str, Any] | None:
    if not record:
        return None
    summary = _record_request_summary(record) or {}
    summary.update(
        {
            "status": record.get("status"),
            "job_name": record.get("job_name"),
            "inp_path": record.get("inp_path"),
            "work_dir": record.get("work_dir"),
            "sta_path": record.get("sta_path"),
            "msg_path": record.get("msg_path"),
            "dat_path": record.get("dat_path"),
            "log_path": record.get("log_path"),
            "odb_path": record.get("odb_path"),
            "missing_fields": record.get("missing_fields", []),
            "lck_path_source": record.get("lck_path_source"),
            "selection_reason": record.get("selection_reason"),
        }
    )
    return summary


def _file_evidence(files: dict[str, Path], flags: dict[str, bool]) -> dict[str, Any]:
    odb = files["odb"]
    lck = files["lck"]
    evidence = {
        "odb_exists": odb.exists(),
        "odb_size_bytes": odb.stat().st_size if odb.exists() else 0,
        "lock_exists": lck.exists(),
        "sta_exists": files["sta"].exists(),
        "dat_exists": files["dat"].exists(),
        "msg_exists": files["msg"].exists(),
        "log_exists": files["log"].exists(),
        "input_processor_error": flags["input_processor_error"],
        "solver_started": flags["solver_started"],
        "analysis_completed": flags["analysis_completed"],
        "analysis_not_completed": flags["analysis_not_completed"],
        "too_many_attempts": flags["too_many_attempts"],
        "terminated_due_to_errors": flags["terminated_due_to_errors"],
        "completed_line_found": flags["completed_line_found"],
        "error_lines_found": flags["error_lines_found"],
        "warning_lines_found": flags["warning_lines_found"],
        "license_error": flags["license_error"],
        "environment_error": flags["environment_error"],
        "odb_locked_or_stale": lck.exists(),
    }
    evidence.update(
        {
            "terminal_failure": flags["terminal_failure"],
            "convergence_failure": flags["convergence_failure"],
            "numerical_instability": flags["numerical_instability"],
            "mesh_distortion": flags["mesh_distortion"],
            "contact_constraint_failure": flags["contact_constraint_failure"],
            "material_model_failure": flags["material_model_failure"],
            "thermal_coupling_failure": flags["thermal_coupling_failure"],
        }
    )
    return evidence


def _decide_status(evidence: dict[str, Any], flags: dict[str, bool], files: dict[str, Path]) -> str:
    if evidence["lock_exists"]:
        return JOB_LOCKED_STALE if _lock_is_stale(files) else JOB_RUNNING_LOCK_ACTIVE
    if flags["input_processor_error"]:
        return JOB_INPUT_PROCESSOR_FAILED
    if _license_or_environment_failure(flags):
        return JOB_LICENSE_OR_ENVIRONMENT_FAILED
    if flags["terminal_failure"]:
        if flags["convergence_failure"]:
            return JOB_SOLVER_CONVERGENCE_FAILED
        if flags["mesh_distortion"]:
            return JOB_MESH_DISTORTION_FAILED
        if flags["numerical_instability"]:
            return JOB_NUMERICAL_INSTABILITY_FAILED
        if flags["contact_constraint_failure"]:
            return JOB_CONTACT_CONSTRAINT_FAILED
        if flags["material_model_failure"]:
            return JOB_MATERIAL_MODEL_FAILED
        if flags["thermal_coupling_failure"]:
            return JOB_THERMAL_COUPLING_FAILED
        return JOB_TERMINATED_BY_ERRORS
    if evidence["analysis_completed"] and evidence["odb_exists"]:
        return JOB_COMPLETED_ODB_ACCEPTABLE
    if evidence["analysis_completed"] and not evidence["odb_exists"]:
        return JOB_COMPLETED_ODB_MISSING
    if evidence["odb_exists"]:
        return JOB_ODB_EXISTS_BUT_COMPLETION_NOT_PROVEN
    return JOB_STATUS_UNKNOWN


def _license_or_environment_failure(flags: dict[str, bool]) -> bool:
    return bool((flags["license_error"] or flags["environment_error"]) and flags["terminal_failure"])


def _lock_is_stale(files: dict[str, Path]) -> bool:
    lck = files["lck"]
    if not lck.exists():
        return False
    related = [path for key, path in files.items() if key != "lck" and path.exists()]
    latest = max([lck.stat().st_mtime] + [path.stat().st_mtime for path in related])
    age = datetime.now(timezone.utc).timestamp() - latest
    return age > STALE_LOCK_SECONDS


def _recommended_next_action(status: str) -> str:
    mapping = {
        JOB_COMPLETED_ODB_ACCEPTABLE: "Proceed to gated metrics extraction.",
        JOB_RUNNING_LOCK_ACTIVE: "Wait for the Abaqus job to finish, then rerun diagnosis.",
        JOB_LOCKED_STALE: "Review the stale lock and job logs before accepting any ODB.",
        JOB_SOLVER_CONVERGENCE_FAILED: "Review convergence controls, step settings, and the last increment before retrying a guarded run.",
        JOB_NUMERICAL_INSTABILITY_FAILED: "Review constraints, rigid body modes, pivots, and numerical stability evidence.",
        JOB_INPUT_PROCESSOR_FAILED: "Fix the INP/preprocessor issue through deterministic guarded patching before rerun.",
        JOB_COMPLETED_ODB_MISSING: "Locate the expected ODB or treat output as missing.",
        JOB_ODB_EXISTS_BUT_COMPLETION_NOT_PROVEN: "Do not extract metrics; find completion evidence or rerun diagnosis with complete logs.",
    }
    return mapping.get(status, "Review diagnosis evidence and do not extract metrics until completion is proven.")
