from __future__ import annotations

from typing import Any


PASS = "CONTROLLED_SOLVER_REQUEST_PREFLIGHT_PASS_NO_EXECUTION"
PASS_WARN = "CONTROLLED_SOLVER_REQUEST_PREFLIGHT_PASS_WITH_WARNINGS_NO_EXECUTION"
MISSING = "CONTROLLED_SOLVER_REQUEST_PREFLIGHT_BLOCKED_MISSING_SOURCE_ARTIFACT"
GATE_INVALID = "CONTROLLED_SOLVER_REQUEST_PREFLIGHT_BLOCKED_SOURCE_GATE_INVALID"
HANDOFF_INVALID = "CONTROLLED_SOLVER_REQUEST_PREFLIGHT_BLOCKED_HANDOFF_INVALID"
DRAFT_INVALID = "CONTROLLED_SOLVER_REQUEST_PREFLIGHT_BLOCKED_REQUEST_DRAFT_INVALID"
HASH_MISMATCH = "CONTROLLED_SOLVER_REQUEST_PREFLIGHT_BLOCKED_CANDIDATE_HASH_MISMATCH"
COMMAND_POLICY = "CONTROLLED_SOLVER_REQUEST_PREFLIGHT_BLOCKED_SOLVER_COMMAND_POLICY"
OUTPUT_POLICY = "CONTROLLED_SOLVER_REQUEST_PREFLIGHT_BLOCKED_OUTPUT_DIR_POLICY"
RESOURCE_POLICY = "CONTROLLED_SOLVER_REQUEST_PREFLIGHT_BLOCKED_RESOURCE_POLICY"
ACTIVE_REQUEST = "CONTROLLED_SOLVER_REQUEST_PREFLIGHT_BLOCKED_ACTIVE_REQUEST"
REQUEST_CREATED = "CONTROLLED_SOLVER_REQUEST_PREFLIGHT_BLOCKED_SOLVER_REQUEST_CREATED"
EXECUTION_ALLOWED = "CONTROLLED_SOLVER_REQUEST_PREFLIGHT_BLOCKED_EXECUTION_ALLOWED"
QUEUE_OR_ODB = "CONTROLLED_SOLVER_REQUEST_PREFLIGHT_BLOCKED_QUEUE_OR_ODB"
FINAL_EVIDENCE = "CONTROLLED_SOLVER_REQUEST_PREFLIGHT_BLOCKED_FINAL_EVIDENCE"
REVIEW_REQUIRED = "CONTROLLED_SOLVER_REQUEST_PREFLIGHT_REVIEW_REQUIRED"


def validate_controlled_solver_request_preflight_result(result: dict[str, Any]) -> dict[str, Any]:
    required = {
        "result_type": "CONTROLLED_SOLVER_REQUEST_PREFLIGHT",
        "stage_id": "STAGE5_2I",
        "source_stage_id": "STAGE5_2H",
        "source_gate_validated": True,
        "source_handoff_draft_validated": True,
        "source_request_draft_validated": True,
        "candidate_hash_verified": True,
        "solver_command_label_validated": True,
        "solver_command_path_not_invoked": True,
        "output_dir_policy_validated": True,
        "output_dir_created": False,
        "cpu_policy_validated": True,
        "memory_policy_validated": True,
        "timeout_policy_validated": True,
        "log_capture_policy_validated": True,
        "preflight_only": True,
        "active_request_created": False,
        "request_active": False,
        "executable_request": False,
        "future_execution_stage_required": True,
        "target_agent": "ExecutionAgent",
        "solver_execution_allowed": False,
        "solver_request_created": False,
        "solver_run": False,
        "queue_runner_launched": False,
        "odb_opened": False,
        "odb_metrics_approved": False,
        "final_evidence_approved": False,
        "final_verdict_frozen": False,
        "task_final_evidence_ledger_updated": False,
        "downstream_execution_auto_start": False,
    }
    checks = {f"{key}_ok": result.get(key) == value for key, value in required.items()}
    status = _status_for(result, checks)
    return {
        "schema_version": "0.1",
        "stage": "Stage 5.2I",
        "validation_status": status,
        "checks": checks,
        "preflight_passed": status in {PASS, PASS_WARN},
        "preflight_only": result.get("preflight_only") is True,
        "active_request_created": result.get("active_request_created") is True,
        "request_active": result.get("request_active") is True,
        "executable_request": result.get("executable_request") is True,
        "solver_execution_allowed": result.get("solver_execution_allowed") is True,
        "solver_request_created": result.get("solver_request_created") is True,
        "solver_run": result.get("solver_run") is True,
        "queue_runner_launched": result.get("queue_runner_launched") is True,
        "odb_opened": result.get("odb_opened") is True,
        "odb_metrics_approved": result.get("odb_metrics_approved") is True,
        "final_evidence_approved": result.get("final_evidence_approved") is True,
        "final_verdict_frozen": result.get("final_verdict_frozen") is True,
        "task_final_evidence_ledger_updated": result.get("task_final_evidence_ledger_updated") is True,
    }


def _status_for(result: dict[str, Any], checks: dict[str, bool]) -> str:
    if not checks["result_type_ok"] or not checks["stage_id_ok"]:
        return REVIEW_REQUIRED
    if not checks["source_gate_validated_ok"]:
        return GATE_INVALID
    if not checks["source_handoff_draft_validated_ok"]:
        return HANDOFF_INVALID
    if not checks["source_request_draft_validated_ok"]:
        return DRAFT_INVALID
    if not checks["candidate_hash_verified_ok"]:
        return HASH_MISMATCH
    if not checks["solver_command_label_validated_ok"] or not checks["solver_command_path_not_invoked_ok"]:
        return COMMAND_POLICY
    if not checks["output_dir_policy_validated_ok"] or result.get("output_dir_created") is True:
        return OUTPUT_POLICY
    if not checks["cpu_policy_validated_ok"] or not checks["memory_policy_validated_ok"] or not checks["timeout_policy_validated_ok"] or not checks["log_capture_policy_validated_ok"]:
        return RESOURCE_POLICY
    if result.get("active_request_created") is True or result.get("request_active") is True or result.get("executable_request") is True:
        return ACTIVE_REQUEST
    if result.get("solver_request_created") is True:
        return REQUEST_CREATED
    if result.get("solver_execution_allowed") is True or result.get("solver_run") is True or result.get("downstream_execution_auto_start") is True:
        return EXECUTION_ALLOWED
    if result.get("queue_runner_launched") is True or result.get("odb_opened") is True or result.get("odb_metrics_approved") is True:
        return QUEUE_OR_ODB
    if result.get("final_evidence_approved") is True or result.get("final_verdict_frozen") is True or result.get("task_final_evidence_ledger_updated") is True:
        return FINAL_EVIDENCE
    return PASS if all(checks.values()) else REVIEW_REQUIRED
