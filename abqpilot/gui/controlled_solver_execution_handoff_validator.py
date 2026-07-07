from __future__ import annotations

from typing import Any


READY = "CONTROLLED_SOLVER_EXECUTION_HANDOFF_DRAFT_READY"
MISSING_SOURCE = "CONTROLLED_SOLVER_EXECUTION_HANDOFF_DRAFT_BLOCKED_MISSING_SOURCE_GATE_OR_CANDIDATE"
SOURCE_INVALID = "CONTROLLED_SOLVER_EXECUTION_HANDOFF_DRAFT_BLOCKED_SOURCE_GATE_INVALID"
HASH_MISMATCH = "CONTROLLED_SOLVER_EXECUTION_HANDOFF_DRAFT_BLOCKED_CANDIDATE_HASH_MISMATCH"
EXECUTION_ALLOWED = "CONTROLLED_SOLVER_EXECUTION_HANDOFF_DRAFT_BLOCKED_EXECUTION_ALLOWED"
SOLVER_REQUEST = "CONTROLLED_SOLVER_EXECUTION_HANDOFF_DRAFT_BLOCKED_SOLVER_REQUEST"
QUEUE_OR_ODB = "CONTROLLED_SOLVER_EXECUTION_HANDOFF_DRAFT_BLOCKED_QUEUE_OR_ODB"
FINAL_EVIDENCE = "CONTROLLED_SOLVER_EXECUTION_HANDOFF_DRAFT_BLOCKED_FINAL_EVIDENCE"
REVIEW_REQUIRED = "CONTROLLED_SOLVER_EXECUTION_HANDOFF_DRAFT_REVIEW_REQUIRED"


def validate_controlled_solver_execution_handoff_draft(draft: dict[str, Any]) -> dict[str, Any]:
    required = {
        "draft_type": "CONTROLLED_SOLVER_EXECUTION_HANDOFF_DRAFT",
        "stage_id": "STAGE5_2G",
        "source_stage_id": "STAGE5_2F",
        "source_gate_decision": "APPROVED_BY_HUMAN",
        "source_gate_validated": True,
        "candidate_hash_verified": True,
        "to_agent": "ExecutionAgent",
        "draft_only": True,
        "active_execution_handoff": False,
        "handoff_active_for_execution": False,
        "execution_status": "NOT_EXECUTABLE",
        "future_stage_required": True,
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
    checks = {f"{key}_ok": draft.get(key) == value for key, value in required.items()}
    if not checks["draft_type_ok"] or not checks["stage_id_ok"]:
        status = REVIEW_REQUIRED
    elif not checks["source_stage_id_ok"] or not checks["source_gate_decision_ok"] or not checks["source_gate_validated_ok"]:
        status = SOURCE_INVALID
    elif not checks["candidate_hash_verified_ok"]:
        status = HASH_MISMATCH
    elif (
        draft.get("solver_execution_allowed") is True
        or draft.get("solver_run") is True
        or draft.get("downstream_execution_auto_start") is True
        or draft.get("active_execution_handoff") is True
        or draft.get("handoff_active_for_execution") is True
    ):
        status = EXECUTION_ALLOWED
    elif draft.get("solver_request_created") is True:
        status = SOLVER_REQUEST
    elif draft.get("queue_runner_launched") is True or draft.get("odb_opened") is True or draft.get("odb_metrics_approved") is True:
        status = QUEUE_OR_ODB
    elif (
        draft.get("final_evidence_approved") is True
        or draft.get("final_verdict_frozen") is True
        or draft.get("task_final_evidence_ledger_updated") is True
    ):
        status = FINAL_EVIDENCE
    else:
        status = READY if all(checks.values()) else REVIEW_REQUIRED
    return {
        "schema_version": "0.1",
        "stage": "Stage 5.2G",
        "validation_status": status,
        "checks": checks,
        "draft_only": draft.get("draft_only") is True,
        "active_execution_handoff": draft.get("active_execution_handoff") is True,
        "handoff_active_for_execution": draft.get("handoff_active_for_execution") is True,
        "solver_execution_allowed": draft.get("solver_execution_allowed") is True,
        "solver_request_created": draft.get("solver_request_created") is True,
        "solver_run": draft.get("solver_run") is True,
        "queue_runner_launched": draft.get("queue_runner_launched") is True,
        "odb_opened": draft.get("odb_opened") is True,
        "odb_metrics_approved": draft.get("odb_metrics_approved") is True,
        "final_evidence_approved": draft.get("final_evidence_approved") is True,
        "final_verdict_frozen": draft.get("final_verdict_frozen") is True,
        "task_final_evidence_ledger_updated": draft.get("task_final_evidence_ledger_updated") is True,
    }
