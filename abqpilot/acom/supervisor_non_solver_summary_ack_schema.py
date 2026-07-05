from __future__ import annotations

from typing import Any


SCHEMA_VERSION = "0.1"
STAGE = "Stage 5.0I"

ACK_ACCEPTED = "SUPERVISOR_NON_SOLVER_SUMMARY_ACK_ACCEPTED"
ACK_ACCEPTED_WARNINGS = "SUPERVISOR_NON_SOLVER_SUMMARY_ACK_ACCEPTED_WITH_WARNINGS"

ACK_STATUSES = {
    ACK_ACCEPTED,
    ACK_ACCEPTED_WARNINGS,
    "SUPERVISOR_NON_SOLVER_SUMMARY_ACK_BLOCKED_MISSING_SUMMARY",
    "SUPERVISOR_NON_SOLVER_SUMMARY_ACK_BLOCKED_INVALID_SUMMARY",
    "SUPERVISOR_NON_SOLVER_SUMMARY_ACK_BLOCKED_SUMMARY_NOT_READY",
    "SUPERVISOR_NON_SOLVER_SUMMARY_ACK_BLOCKED_MISSING_LEDGER",
    "SUPERVISOR_NON_SOLVER_SUMMARY_ACK_BLOCKED_LEDGER_INVALID",
    "SUPERVISOR_NON_SOLVER_SUMMARY_ACK_BLOCKED_FINAL_EVIDENCE_APPROVAL_ATTEMPT",
    "SUPERVISOR_NON_SOLVER_SUMMARY_ACK_BLOCKED_SOLVER_OR_ODB_APPROVAL_ATTEMPT",
    "SUPERVISOR_NON_SOLVER_SUMMARY_ACK_BLOCKED_TASK_FINAL_LEDGER_MUTATION",
    "SUPERVISOR_NON_SOLVER_SUMMARY_ACK_REVIEW_REQUIRED",
}

ACK_GATE = "ACKNOWLEDGED_NON_SOLVER_SUMMARY"
ACK_WARNINGS_GATE = "ACKNOWLEDGED_NON_SOLVER_SUMMARY_WITH_WARNINGS"


def validate_supervisor_non_solver_summary_ack(payload: dict[str, Any]) -> tuple[bool, list[str]]:
    errors: list[str] = []
    required = [
        "schema_version",
        "stage",
        "task_id",
        "task_dir",
        "ack_status",
        "gate_decision",
        "summary_result_path",
        "summary_report_path",
        "ledger_json_path",
        "ledger_md_path",
        "automatic_execution_performed",
        "final_evidence_approved",
        "final_verdict_frozen",
        "solver_approved",
        "odb_metrics_approved",
        "task_final_evidence_ledger_updated",
        "non_solver_summary_ack_ledger_entry_created",
        "safety_flags",
    ]
    for key in required:
        if key not in payload:
            errors.append(f"missing required field: {key}")
    if payload.get("schema_version") != SCHEMA_VERSION:
        errors.append("schema_version must be 0.1")
    if payload.get("stage") != STAGE:
        errors.append("stage must be Stage 5.0I")
    if payload.get("ack_status") not in ACK_STATUSES:
        errors.append("unknown supervisor non-solver summary ack status")
    if payload.get("gate_decision") == "APPROVED":
        errors.append("gate_decision must never be APPROVED")
    for key in [
        "automatic_execution_performed",
        "final_evidence_approved",
        "final_verdict_frozen",
        "solver_approved",
        "odb_metrics_approved",
        "task_final_evidence_ledger_updated",
    ]:
        if payload.get(key) is not False:
            errors.append(f"{key} must be false")
    safety = payload.get("safety_flags")
    if not isinstance(safety, dict):
        errors.append("safety_flags must be an object")
    else:
        for key, value in safety.items():
            if value is not False:
                errors.append(f"safety flag must be false: {key}")
    if payload.get("ack_status") in {ACK_ACCEPTED, ACK_ACCEPTED_WARNINGS}:
        if payload.get("gate_decision") not in {ACK_GATE, ACK_WARNINGS_GATE}:
            errors.append("accepted acknowledgement must use an acknowledgement gate decision")
        if payload.get("non_solver_summary_ack_ledger_entry_created") is not True:
            errors.append("accepted acknowledgement must create an acknowledgement ledger entry")
        if not payload.get("handoff_path"):
            errors.append("accepted acknowledgement must create a handoff")
    return not errors, errors
