from __future__ import annotations

from typing import Any


READY = "CONTROLLED_SOLVER_DRY_RUN_REQUEST_MATERIALIZED_NO_EXECUTION"
MISSING_SOURCE = "CONTROLLED_SOLVER_DRY_RUN_REQUEST_BLOCKED_MISSING_SOURCE_ARTIFACT"
SOURCE_GATE_INVALID = "CONTROLLED_SOLVER_DRY_RUN_REQUEST_BLOCKED_SOURCE_GATE_INVALID"
HANDOFF_INVALID = "CONTROLLED_SOLVER_DRY_RUN_REQUEST_BLOCKED_HANDOFF_INVALID"
REQUEST_DRAFT_INVALID = "CONTROLLED_SOLVER_DRY_RUN_REQUEST_BLOCKED_REQUEST_DRAFT_INVALID"
PREFLIGHT_INVALID = "CONTROLLED_SOLVER_DRY_RUN_REQUEST_BLOCKED_PREFLIGHT_INVALID"
PREFLIGHT_NOT_PASS = "CONTROLLED_SOLVER_DRY_RUN_REQUEST_BLOCKED_PREFLIGHT_NOT_PASS"
HASH_MISMATCH = "CONTROLLED_SOLVER_DRY_RUN_REQUEST_BLOCKED_CANDIDATE_HASH_MISMATCH"
ACTIVE_REQUEST = "CONTROLLED_SOLVER_DRY_RUN_REQUEST_BLOCKED_ACTIVE_REQUEST"
EXECUTABLE_REQUEST = "CONTROLLED_SOLVER_DRY_RUN_REQUEST_BLOCKED_EXECUTABLE_REQUEST"
SOLVER_REQUEST_CREATED = "CONTROLLED_SOLVER_DRY_RUN_REQUEST_BLOCKED_SOLVER_REQUEST_CREATED"
EXECUTION_ALLOWED = "CONTROLLED_SOLVER_DRY_RUN_REQUEST_BLOCKED_EXECUTION_ALLOWED"
QUEUE_OR_ODB = "CONTROLLED_SOLVER_DRY_RUN_REQUEST_BLOCKED_QUEUE_OR_ODB"
FINAL_EVIDENCE = "CONTROLLED_SOLVER_DRY_RUN_REQUEST_BLOCKED_FINAL_EVIDENCE"
REVIEW_REQUIRED = "CONTROLLED_SOLVER_DRY_RUN_REQUEST_REVIEW_REQUIRED"


def validate_controlled_solver_dry_run_request(request: dict[str, Any]) -> dict[str, Any]:
    required = {
        "request_type": "CONTROLLED_SOLVER_DRY_RUN_REQUEST",
        "stage_id": "STAGE5_2J",
        "source_stage_id": "STAGE5_2I",
        "source_gate_validated": True,
        "source_handoff_draft_validated": True,
        "source_request_draft_validated": True,
        "source_preflight_validated": True,
        "source_preflight_status": "CONTROLLED_SOLVER_REQUEST_PREFLIGHT_PASS_NO_EXECUTION",
        "candidate_hash_verified": True,
        "target_agent": "ExecutionAgent",
        "target_future_stage": "FUTURE_CONTROLLED_SOLVER_EXECUTION_STAGE",
        "dry_run_only": True,
        "materialized_request_artifact": True,
        "materialized_request_filename": "CONTROLLED_SOLVER_DRY_RUN_REQUEST.json",
        "active_request_created": False,
        "request_active": False,
        "executable_request": False,
        "future_execution_stage_required": True,
        "solver_command_label_validated": True,
        "solver_command_path_included": False,
        "solver_command_not_invoked": True,
        "output_dir_policy_validated": True,
        "output_dir_created": False,
        "cpu_policy_validated": True,
        "memory_policy_validated": True,
        "timeout_policy_validated": True,
        "log_capture_policy_validated": True,
        "solver_approved_by_source_gate": True,
        "solver_execution_allowed": False,
        "solver_request_created": False,
        "solver_run": False,
        "queue_runner_launched": False,
        "queue_entry_created": False,
        "odb_opened": False,
        "odb_metrics_approved": False,
        "final_evidence_approved": False,
        "final_verdict_frozen": False,
        "task_final_evidence_ledger_updated": False,
        "downstream_execution_auto_start": False,
    }
    checks = {f"{key}_ok": request.get(key) == value for key, value in required.items()}
    status = _status_for(request, checks)
    return {
        "schema_version": "0.1",
        "stage": "Stage 5.2J",
        "validation_status": status,
        "checks": checks,
        "dry_run_request_valid": status == READY,
        "dry_run_only": request.get("dry_run_only") is True,
        "request_active": request.get("request_active") is True,
        "executable_request": request.get("executable_request") is True,
        "solver_execution_allowed": request.get("solver_execution_allowed") is True,
        "solver_request_created": request.get("solver_request_created") is True,
        "solver_run": request.get("solver_run") is True,
        "queue_runner_launched": request.get("queue_runner_launched") is True,
        "queue_entry_created": request.get("queue_entry_created") is True,
        "output_dir_created": request.get("output_dir_created") is True,
        "odb_opened": request.get("odb_opened") is True,
        "odb_metrics_approved": request.get("odb_metrics_approved") is True,
        "final_evidence_approved": request.get("final_evidence_approved") is True,
        "final_verdict_frozen": request.get("final_verdict_frozen") is True,
        "task_final_evidence_ledger_updated": request.get("task_final_evidence_ledger_updated") is True,
    }


def _status_for(request: dict[str, Any], checks: dict[str, bool]) -> str:
    if not checks["request_type_ok"] or not checks["stage_id_ok"]:
        return REVIEW_REQUIRED
    if not checks["source_gate_validated_ok"]:
        return SOURCE_GATE_INVALID
    if not checks["source_handoff_draft_validated_ok"]:
        return HANDOFF_INVALID
    if not checks["source_request_draft_validated_ok"]:
        return REQUEST_DRAFT_INVALID
    if not checks["source_preflight_validated_ok"]:
        return PREFLIGHT_INVALID
    if not checks["source_preflight_status_ok"]:
        return PREFLIGHT_NOT_PASS
    if not checks["candidate_hash_verified_ok"]:
        return HASH_MISMATCH
    if request.get("active_request_created") is True or request.get("request_active") is True:
        return ACTIVE_REQUEST
    if request.get("executable_request") is True:
        return EXECUTABLE_REQUEST
    if request.get("solver_request_created") is True:
        return SOLVER_REQUEST_CREATED
    if (
        request.get("solver_execution_allowed") is True
        or request.get("solver_run") is True
        or request.get("downstream_execution_auto_start") is True
    ):
        return EXECUTION_ALLOWED
    if (
        request.get("queue_runner_launched") is True
        or request.get("queue_entry_created") is True
        or request.get("odb_opened") is True
        or request.get("odb_metrics_approved") is True
        or request.get("output_dir_created") is True
    ):
        return QUEUE_OR_ODB
    if (
        request.get("final_evidence_approved") is True
        or request.get("final_verdict_frozen") is True
        or request.get("task_final_evidence_ledger_updated") is True
    ):
        return FINAL_EVIDENCE
    return READY if all(checks.values()) else REVIEW_REQUIRED
