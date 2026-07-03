from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from abqpilot.repair.solver_failure_repair_schema import SCHEMA_VERSION, STAGE


def build_solver_failure_context(
    solver_run_dir: str | Path,
    diagnosis_path: str | Path | None = None,
) -> dict[str, Any]:
    run_dir = Path(solver_run_dir)
    diagnosis_file = Path(diagnosis_path) if diagnosis_path else run_dir / "job_odb_diagnosis_result.json"
    diagnosis = _read_json(diagnosis_file)
    preflight = _read_json(run_dir / "solver_preflight_result.json")
    manifest = _read_json(run_dir / "solver_candidate_manifest.json")
    command_preview = _read_json(run_dir / "solver_command_preview.json")
    abqjobpilot_record = diagnosis.get("abqjobpilot_record") or {}
    return {
        "schema_version": SCHEMA_VERSION,
        "stage": STAGE,
        "solver_run_dir": str(run_dir),
        "diagnosis_path": str(diagnosis_file),
        "diagnosis_exists": bool(diagnosis),
        "diagnosis_status": diagnosis.get("diagnosis_status"),
        "diagnosis_input_mode": diagnosis.get("diagnosis_input_mode", "directory"),
        "failure_category": diagnosis.get("failure_category"),
        "odb_acceptable_for_metrics": diagnosis.get("odb_acceptable_for_metrics"),
        "evidence": {
            "analysis_completed": diagnosis.get("evidence", {}).get("analysis_completed"),
            "analysis_not_completed": diagnosis.get("evidence", {}).get("analysis_not_completed"),
            "too_many_attempts": diagnosis.get("evidence", {}).get("too_many_attempts"),
            "terminated_due_to_errors": diagnosis.get("evidence", {}).get("terminated_due_to_errors"),
            "odb_acceptable_for_metrics": diagnosis.get("odb_acceptable_for_metrics"),
        },
        "important_lines": {
            "dat_error_lines": diagnosis.get("important_lines", {}).get("dat_error_lines", [])[:12],
            "msg_error_lines": diagnosis.get("important_lines", {}).get("msg_error_lines", [])[:12],
            "sta_tail": diagnosis.get("important_lines", {}).get("sta_tail", [])[-12:],
        },
        "job_name": diagnosis.get("job_name") or preflight.get("job_name"),
        "candidate_inp_path": preflight.get("candidate_inp_path") or manifest.get("candidate_inp_path"),
        "candidate_inp_sha256": preflight.get("candidate_inp_sha256") or manifest.get("candidate_inp_sha256"),
        "candidate_traceability": preflight.get("candidate_traceability") or manifest.get("candidate_traceability"),
        "guard_statuses": {
            "static_validator_status": preflight.get("static_validator_status"),
            "diff_guard_status": preflight.get("diff_guard_status"),
            "physics_guard_status": preflight.get("physics_guard_status"),
            "unrelated_changes_count": preflight.get("unrelated_changes_count"),
        },
        "solver_command_preview_sha256": command_preview.get("command_preview_sha256")
        or preflight.get("abaqus_command_preview_sha256"),
        "abqjobpilot_execution_record": {
            "available": bool(abqjobpilot_record),
            "job_id": abqjobpilot_record.get("job_id"),
            "raw_status": abqjobpilot_record.get("raw_status"),
            "fatal_reason": abqjobpilot_record.get("fatal_reason"),
            "return_code": abqjobpilot_record.get("return_code"),
            "record_path": abqjobpilot_record.get("record_path"),
            "record_kind": abqjobpilot_record.get("record_kind"),
        },
        "contains_full_inp_content": False,
        "contains_odb_content": False,
        "contains_env_secret": False,
    }


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))
