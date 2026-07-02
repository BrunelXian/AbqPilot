from __future__ import annotations

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from abqpilot.core.hash_utils import sha256_file


APPROVAL_PHRASE = "I_APPROVE_ABQJOBPILOT_REAL_ENQUEUE_FOR_THIS_TASK"
APPROVAL_TYPE = "abqjobpilot_real_enqueue"
SCHEMA_VERSION = "0.1"
VOLATILE_HASH_KEYS = {"timestamp", "created_at", "updated_at"}


def create_approval_request(
    task_id: str,
    step_dir: str | Path,
    candidate_inp_path: str | Path,
    job_request_path: str | Path,
    preflight_result_path: str | Path,
    dry_run_result_path: str | Path,
) -> dict[str, Any]:
    candidate_inp = Path(candidate_inp_path)
    job_request = Path(job_request_path)
    preflight_result = Path(preflight_result_path)
    dry_run_result = Path(dry_run_result_path)
    job_request_payload = _read_json(job_request)
    preflight_payload = _read_json(preflight_result)
    dry_run_payload = _read_json(dry_run_result)
    return {
        "schema_version": SCHEMA_VERSION,
        "approval_type": APPROVAL_TYPE,
        "task_id": task_id,
        "step": "05_jobpilot_enqueue_authorization",
        "created_at": _now(),
        "status": "APPROVAL_REQUIRED",
        "candidate_inp_path": str(candidate_inp),
        "candidate_inp_sha256": sha256_file(candidate_inp),
        "job_request_path": str(job_request),
        "job_request_sha256": sha256_file(job_request),
        "preflight_result_path": str(preflight_result),
        "preflight_result_sha256": sha256_file(preflight_result),
        "dry_run_result_path": str(dry_run_result),
        "dry_run_result_sha256": sha256_file(dry_run_result),
        "required_conditions": {
            "preflight_status": preflight_payload.get("status"),
            "dry_run_enqueue_status": dry_run_payload.get("status"),
            "runtime_mutation_detected": bool(dry_run_payload.get("runtime_mutation_detected")),
            "allow_solver_submit": bool(job_request_payload.get("allow_solver_submit")),
            "submission_mode": job_request_payload.get("submission_mode"),
        },
        "human_instructions": [
            "Review the candidate INP, guard reports, preflight result, and dry-run enqueue result.",
            "Only create an approval token if you intentionally authorize a future real enqueue stage.",
            "This approval request does not enqueue or submit a solver job.",
        ],
    }


def request_conditions_are_safe(request: dict[str, Any]) -> tuple[bool, list[str]]:
    conditions = request.get("required_conditions", {})
    errors = []
    if conditions.get("preflight_status") != "PREVIEW_READY":
        errors.append("preflight_status must be PREVIEW_READY")
    if conditions.get("dry_run_enqueue_status") != "DRY_RUN_READY":
        errors.append("dry_run_enqueue_status must be DRY_RUN_READY")
    if conditions.get("runtime_mutation_detected") is not False:
        errors.append("runtime_mutation_detected must be false")
    if conditions.get("allow_solver_submit") is not False:
        errors.append("allow_solver_submit must be false")
    if conditions.get("submission_mode") != "preview_only":
        errors.append("submission_mode must be preview_only")
    return not errors, errors


def approval_token_path(task_dir: str | Path) -> Path:
    return Path(task_dir) / "approvals" / "jobpilot_enqueue_approval_token.json"


def approval_request_path(task_dir: str | Path) -> Path:
    return Path(task_dir) / "steps" / "05_jobpilot_enqueue_authorization" / "jobpilot_enqueue_approval_request.json"


def create_approval_token(
    task_dir: str | Path,
    approved_by: str,
    approval_phrase: str,
    expires_hours: int | float,
) -> dict[str, Any]:
    if approval_phrase != APPROVAL_PHRASE:
        return {
            "status": "APPROVAL_TOKEN_INVALID",
            "success": False,
            "errors": ["approval phrase does not match required phrase"],
            "approval_token_path": None,
        }
    request_path = approval_request_path(task_dir)
    if not request_path.exists():
        return {
            "status": "APPROVAL_TOKEN_MISSING",
            "success": False,
            "errors": [f"approval request does not exist: {request_path}"],
            "approval_token_path": None,
        }
    request = _read_json(request_path)
    safe, errors = request_conditions_are_safe(request)
    if not safe:
        return {
            "status": "APPROVAL_UNSAFE_CONDITIONS",
            "success": False,
            "errors": errors,
            "approval_token_path": None,
        }
    created_at = datetime.now()
    expires_at = created_at + timedelta(hours=float(expires_hours))
    token = {
        "schema_version": SCHEMA_VERSION,
        "approval_type": APPROVAL_TYPE,
        "task_id": request["task_id"],
        "approved_step": "future_real_abqjobpilot_enqueue",
        "approved_by": approved_by,
        "approval_phrase": approval_phrase,
        "created_at": created_at.isoformat(timespec="seconds"),
        "expires_at": expires_at.isoformat(timespec="seconds"),
        "candidate_inp_sha256": request["candidate_inp_sha256"],
        "job_request_sha256": request["job_request_sha256"],
        "preflight_result_sha256": request["preflight_result_sha256"],
        "dry_run_result_sha256": request["dry_run_result_sha256"],
        "conditions": {
            "preflight_status": "PREVIEW_READY",
            "dry_run_enqueue_status": "DRY_RUN_READY",
            "runtime_mutation_detected": False,
            "allow_solver_submit": False,
            "submission_mode": "preview_only",
        },
    }
    path = approval_token_path(task_dir)
    _write_json(path, token)
    return {
        "status": "APPROVAL_TOKEN_CREATED",
        "success": True,
        "approval_token_path": str(path),
        "token": token,
        "errors": [],
        "warnings": [],
    }


def validate_approval_token(request: dict[str, Any], token_path: str | Path | None) -> dict[str, Any]:
    safe, safety_errors = request_conditions_are_safe(request)
    if not safe:
        return _validation_result("APPROVAL_UNSAFE_CONDITIONS", False, safety_errors, token_path)
    if not token_path or not Path(token_path).exists():
        return _validation_result("APPROVAL_TOKEN_MISSING", False, ["approval token is missing"], token_path)
    token = _read_json(token_path)
    if token.get("approval_type") != APPROVAL_TYPE or token.get("task_id") != request.get("task_id"):
        return _validation_result("APPROVAL_TOKEN_INVALID", False, ["approval token type or task id does not match"], token_path)
    if token.get("approval_phrase") != APPROVAL_PHRASE:
        return _validation_result("APPROVAL_TOKEN_INVALID", False, ["approval phrase is invalid"], token_path)
    try:
        expires_at = datetime.fromisoformat(str(token.get("expires_at")))
    except ValueError:
        return _validation_result("APPROVAL_TOKEN_INVALID", False, ["approval token expires_at is invalid"], token_path)
    if expires_at <= datetime.now():
        return _validation_result("APPROVAL_TOKEN_EXPIRED", False, ["approval token is expired"], token_path)

    hash_fields = (
        "candidate_inp_sha256",
        "job_request_sha256",
        "preflight_result_sha256",
        "dry_run_result_sha256",
    )
    mismatches = [field for field in hash_fields if token.get(field) != request.get(field)]
    if mismatches:
        return _validation_result("APPROVAL_HASH_MISMATCH", False, [f"hash mismatch: {field}" for field in mismatches], token_path)

    conditions = token.get("conditions", {})
    required = request.get("required_conditions", {})
    if conditions.get("preflight_status") != required.get("preflight_status"):
        return _validation_result("APPROVAL_TOKEN_INVALID", False, ["preflight status condition does not match"], token_path)
    if conditions.get("dry_run_enqueue_status") != required.get("dry_run_enqueue_status"):
        return _validation_result("APPROVAL_TOKEN_INVALID", False, ["dry-run status condition does not match"], token_path)
    if conditions.get("runtime_mutation_detected") != required.get("runtime_mutation_detected"):
        return _validation_result("APPROVAL_TOKEN_INVALID", False, ["runtime mutation condition does not match"], token_path)
    if conditions.get("allow_solver_submit") != required.get("allow_solver_submit"):
        return _validation_result("APPROVAL_TOKEN_INVALID", False, ["allow_solver_submit condition does not match"], token_path)
    if conditions.get("submission_mode") != required.get("submission_mode"):
        return _validation_result("APPROVAL_TOKEN_INVALID", False, ["submission_mode condition does not match"], token_path)
    return _validation_result("APPROVAL_TOKEN_VALID", True, [], token_path)


def write_authorization_artifacts(
    step_dir: str | Path,
    request: dict[str, Any],
    validation: dict[str, Any],
) -> dict[str, str]:
    target_dir = Path(step_dir)
    target_dir.mkdir(parents=True, exist_ok=True)
    request_path = target_dir / "jobpilot_enqueue_approval_request.json"
    report_json = target_dir / "jobpilot_enqueue_authorization_report.json"
    report_md = target_dir / "jobpilot_enqueue_authorization_report.md"
    status = "APPROVAL_REQUIRED" if validation["status"] == "APPROVAL_TOKEN_MISSING" else validation["status"]
    report = {
        "schema_version": SCHEMA_VERSION,
        "approval_type": APPROVAL_TYPE,
        "task_id": request.get("task_id"),
        "status": status,
        "approval_request_path": str(request_path),
        "approval_token_path": validation.get("approval_token_path"),
        "errors": validation.get("errors", []),
        "warnings": validation.get("warnings", []),
        "required_conditions": request.get("required_conditions", {}),
    }
    _write_json(request_path, request)
    _write_json(report_json, report)
    report_md.write_text(_render_report_markdown(report), encoding="utf-8")
    return {
        "jobpilot_enqueue_approval_request": str(request_path),
        "jobpilot_enqueue_authorization_report_json": str(report_json),
        "jobpilot_enqueue_authorization_report_md": str(report_md),
    }


def _validation_result(status: str, valid: bool, errors: list[str], token_path: str | Path | None) -> dict[str, Any]:
    return {
        "status": status,
        "valid": valid,
        "approval_token_path": str(token_path) if token_path else None,
        "errors": errors,
        "warnings": [],
    }


def _render_report_markdown(report: dict[str, Any]) -> str:
    return f"""# abqjobpilot Enqueue Authorization

Status: {report.get("status")}

Approval token: {report.get("approval_token_path")}

This authorization gate does not enqueue a job and does not submit Abaqus.
"""


def _read_json(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _write_json(path: str | Path, payload: dict[str, Any]) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def _now() -> str:
    return datetime.now().isoformat(timespec="seconds")
