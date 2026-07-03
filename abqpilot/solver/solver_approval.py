from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from abqpilot.core.hash_utils import sha256_file
from abqpilot.solver.solver_artifacts import read_json, result, write_json


SOLVER_APPROVAL_PHRASE = "I_APPROVE_ABQPILOT_CONTROLLED_ABAQUS_SOLVER_RUN"
SOLVER_APPROVAL_TYPE = "abqpilot_controlled_abaqus_solver_run"


def approve_solver_run(
    solver_run_dir: str | Path,
    approved_by: str,
    approval_phrase: str,
    expires_hours: int | float = 24,
) -> dict[str, Any]:
    run_dir = Path(solver_run_dir)
    request = read_json(run_dir / "solver_approval_request.json")
    if approval_phrase != SOLVER_APPROVAL_PHRASE:
        return result("approve-solver-run", "APPROVAL_TOKEN_INVALID", False, run_dir, {"errors": ["approval phrase does not match required phrase"]})
    safe, errors = _request_is_safe(request)
    if not safe:
        return result("approve-solver-run", "APPROVAL_UNSAFE_CONDITIONS", False, run_dir, {"errors": errors})
    created_at = datetime.now()
    token = {
        "schema_version": "0.1",
        "approval_type": SOLVER_APPROVAL_TYPE,
        "approved_step": "controlled_abaqus_solver_run",
        "approved_by": approved_by,
        "approval_phrase": approval_phrase,
        "created_at": created_at.isoformat(timespec="seconds"),
        "expires_at": (created_at + timedelta(hours=float(expires_hours))).isoformat(timespec="seconds"),
        "candidate_inp_path": request["candidate_inp_path"],
        "candidate_inp_sha256": request["candidate_inp_sha256"],
        "source_inp_sha256": request["source_inp_sha256"],
        "solver_run_dir": request["solver_run_dir"],
        "job_name": request["job_name"],
        "expected_odb_path": request["expected_odb_path"],
        "abaqus_command_preview_sha256": request["abaqus_command_preview_sha256"],
        "cpus": request["cpus"],
        "static_validator_status": request["static_validator_status"],
        "diff_guard_status": request["diff_guard_status"],
        "physics_guard_status": request["physics_guard_status"],
        "unrelated_changes_count": request["unrelated_changes_count"],
    }
    token_path = run_dir / "approvals" / "solver_run_approval_token.json"
    write_json(token_path, token)
    details = {"approval_token_path": str(token_path), "token_status": "APPROVAL_TOKEN_CREATED", "errors": [], "warnings": []}
    return result("approve-solver-run", "APPROVAL_TOKEN_CREATED", True, run_dir, details)


def validate_solver_approval_token(solver_run_dir: str | Path, token_path: str | Path | None = None) -> dict[str, Any]:
    run_dir = Path(solver_run_dir)
    request = read_json(run_dir / "solver_approval_request.json")
    safe, errors = _request_is_safe(request)
    if not safe:
        return {"status": "APPROVAL_UNSAFE_CONDITIONS", "valid": False, "errors": errors}
    token_file = Path(token_path) if token_path else run_dir / "approvals" / "solver_run_approval_token.json"
    if not token_file.exists():
        return {"status": "APPROVAL_TOKEN_MISSING", "valid": False, "errors": ["approval token is missing"]}
    token = read_json(token_file)
    if token.get("approval_type") != SOLVER_APPROVAL_TYPE or token.get("approval_phrase") != SOLVER_APPROVAL_PHRASE:
        return {"status": "APPROVAL_TOKEN_INVALID", "valid": False, "errors": ["approval token type or phrase is invalid"]}
    try:
        expires_at = datetime.fromisoformat(str(token.get("expires_at")))
    except ValueError:
        return {"status": "APPROVAL_TOKEN_INVALID", "valid": False, "errors": ["approval token expires_at is invalid"]}
    if expires_at <= datetime.now():
        return {"status": "APPROVAL_TOKEN_EXPIRED", "valid": False, "errors": ["approval token is expired"]}
    fields = [
        "candidate_inp_sha256",
        "source_inp_sha256",
        "solver_run_dir",
        "job_name",
        "expected_odb_path",
        "abaqus_command_preview_sha256",
        "cpus",
        "static_validator_status",
        "diff_guard_status",
        "physics_guard_status",
        "unrelated_changes_count",
    ]
    mismatches = [field for field in fields if token.get(field) != request.get(field)]
    candidate = Path(str(request.get("candidate_inp_path", "")))
    if candidate.exists() and sha256_file(candidate) != request.get("candidate_inp_sha256"):
        mismatches.append("candidate_file_current_sha256")
    if mismatches:
        return {"status": "APPROVAL_HASH_MISMATCH", "valid": False, "errors": [f"mismatch: {field}" for field in mismatches]}
    return {"status": "APPROVAL_TOKEN_VALID", "valid": True, "token_path": str(token_file), "errors": []}


def _request_is_safe(request: dict[str, Any]) -> tuple[bool, list[str]]:
    errors: list[str] = []
    if not request:
        errors.append("solver approval request is missing")
        return False, errors
    if request.get("static_validator_status") != "PASS":
        errors.append("StaticValidator must pass")
    if request.get("diff_guard_status") != "PASS":
        errors.append("DiffGuard must pass")
    if request.get("physics_guard_status") != "PASS":
        errors.append("PhysicsGuard must pass")
    if request.get("unrelated_changes_count") != 0:
        errors.append("unrelated_changes_count must be zero")
    if request.get("required_conditions", {}).get("candidate_traceability") != "sanity-base-derived":
        errors.append("candidate must be sanity-base-derived")
    if request.get("required_conditions", {}).get("queue_runner_allowed") is not False:
        errors.append("external queue worker must not be allowed")
    if request.get("required_conditions", {}).get("llm_execution_authority") is not False:
        errors.append("LLM execution authority must be false")
    return not errors, errors
