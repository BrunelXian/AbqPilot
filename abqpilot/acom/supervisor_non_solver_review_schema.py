from __future__ import annotations

from typing import Any

from abqpilot.acom.non_solver_revalidation_schema import HIGH_RISK_BLOCKED_AGENTS, SUPPORTED_NON_SOLVER_AGENTS


SCHEMA_VERSION = "0.1"
STAGE = "Stage 5.0G"

ACCEPTED_STATUS = "SUPERVISOR_NON_SOLVER_REVIEW_ACCEPTED_FOR_LEDGER"
ACCEPTED_WARNINGS_STATUS = "SUPERVISOR_NON_SOLVER_REVIEW_ACCEPTED_WITH_WARNINGS_FOR_LEDGER"

REVIEW_STATUSES = {
    ACCEPTED_STATUS,
    ACCEPTED_WARNINGS_STATUS,
    "SUPERVISOR_NON_SOLVER_REVIEW_BLOCKED_FAILED_REVALIDATION",
    "SUPERVISOR_NON_SOLVER_REVIEW_BLOCKED_HIGH_RISK_AGENT",
    "SUPERVISOR_NON_SOLVER_REVIEW_BLOCKED_UNSUPPORTED_AGENT",
    "SUPERVISOR_NON_SOLVER_REVIEW_BLOCKED_MISSING_RESULT",
    "SUPERVISOR_NON_SOLVER_REVIEW_BLOCKED_MISSING_RECORDS",
    "SUPERVISOR_NON_SOLVER_REVIEW_BLOCKED_UNSAFE_FLAGS",
    "SUPERVISOR_NON_SOLVER_REVIEW_BLOCKED_FINAL_EVIDENCE_APPROVAL_ATTEMPT",
    "SUPERVISOR_NON_SOLVER_REVIEW_BLOCKED_AUTOMATIC_EXECUTION",
    "SUPERVISOR_NON_SOLVER_REVIEW_REQUIRES_HUMAN_REVIEW",
}

ACCEPTED_GATE_DECISIONS = {
    "ACCEPTED_FOR_NON_SOLVER_EVIDENCE_LEDGER",
    "ACCEPTED_WITH_WARNINGS_FOR_NON_SOLVER_EVIDENCE_LEDGER",
}


def validate_supervisor_non_solver_review(payload: dict[str, Any]) -> tuple[bool, list[str]]:
    errors: list[str] = []
    required = [
        "schema_version",
        "stage",
        "task_id",
        "task_dir",
        "review_status",
        "reviewed_agent",
        "reviewed_status",
        "gate_decision",
        "automatic_execution_performed",
        "final_evidence_approved",
        "final_verdict_frozen",
        "solver_approved",
        "odb_metrics_approved",
        "non_solver_ledger_entry_created",
        "checks",
        "pass_items",
        "warning_items",
        "fail_items",
        "safety_flags",
    ]
    for key in required:
        if key not in payload:
            errors.append(f"missing required field: {key}")
    if payload.get("schema_version") != SCHEMA_VERSION:
        errors.append("schema_version must be 0.1")
    if payload.get("stage") != STAGE:
        errors.append("stage must be Stage 5.0G")
    if payload.get("review_status") not in REVIEW_STATUSES:
        errors.append("unknown supervisor review status")
    agent = payload.get("reviewed_agent")
    if (
        agent not in SUPPORTED_NON_SOLVER_AGENTS
        and agent not in HIGH_RISK_BLOCKED_AGENTS
        and payload.get("review_status") != "SUPERVISOR_NON_SOLVER_REVIEW_BLOCKED_UNSUPPORTED_AGENT"
    ):
        errors.append("unknown reviewed agent")
    if payload.get("gate_decision") == "APPROVED":
        errors.append("gate_decision must never be APPROVED")
    for key in ["automatic_execution_performed", "final_evidence_approved", "final_verdict_frozen", "solver_approved", "odb_metrics_approved"]:
        if payload.get(key) is not False:
            errors.append(f"{key} must be false")
    safety = payload.get("safety_flags")
    if isinstance(safety, dict):
        for key, value in safety.items():
            if value is not False:
                errors.append(f"safety flag must be false: {key}")
    else:
        errors.append("safety_flags must be an object")
    if payload.get("review_status") in {ACCEPTED_STATUS, ACCEPTED_WARNINGS_STATUS}:
        if payload.get("gate_decision") not in ACCEPTED_GATE_DECISIONS:
            errors.append("accepted review must use a non-solver ledger gate decision")
        if payload.get("non_solver_ledger_entry_created") is not True:
            errors.append("accepted review must create a non-solver ledger entry")
    return not errors, errors
