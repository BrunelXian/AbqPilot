from __future__ import annotations

from typing import Any


SCHEMA_VERSION = "0.1"
STAGE = "Stage 5.0H"

READY_STATUS = "NON_SOLVER_EVIDENCE_SUMMARY_READY"
READY_WARNINGS_STATUS = "NON_SOLVER_EVIDENCE_SUMMARY_READY_WITH_WARNINGS"

SUMMARY_STATUSES = {
    READY_STATUS,
    READY_WARNINGS_STATUS,
    "NON_SOLVER_EVIDENCE_SUMMARY_BLOCKED_MISSING_LEDGER",
    "NON_SOLVER_EVIDENCE_SUMMARY_BLOCKED_EMPTY_LEDGER",
    "NON_SOLVER_EVIDENCE_SUMMARY_BLOCKED_LEDGER_INVALID",
    "NON_SOLVER_EVIDENCE_SUMMARY_BLOCKED_FINAL_EVIDENCE_APPROVAL_ATTEMPT",
    "NON_SOLVER_EVIDENCE_SUMMARY_BLOCKED_SOLVER_OR_ODB_APPROVAL_ATTEMPT",
    "NON_SOLVER_EVIDENCE_SUMMARY_BLOCKED_UNSAFE_ENTRY",
    "NON_SOLVER_EVIDENCE_SUMMARY_REVIEW_REQUIRED",
}

READY_GATE = "NON_SOLVER_SUMMARY_READY_PENDING_SUPERVISOR_ACK"
READY_WARNINGS_GATE = "NON_SOLVER_SUMMARY_READY_WITH_WARNINGS_PENDING_SUPERVISOR_ACK"

REQUIRED_ENTRY_FIELDS = {
    "task_id",
    "source_revalidation_agent",
    "source_revalidation_status",
    "supervisor_review_status",
    "ledger_decision",
    "final_evidence_approved",
    "final_verdict_frozen",
    "solver_approved",
    "odb_metrics_approved",
}


def validate_non_solver_ledger(payload: dict[str, Any]) -> tuple[bool, list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    if payload.get("schema_version") != SCHEMA_VERSION:
        errors.append("ledger schema_version must be 0.1")
    if payload.get("ledger_type") != "non_solver_evidence":
        errors.append("ledger_type must be non_solver_evidence")
    entries = payload.get("entries")
    if not isinstance(entries, list):
        errors.append("entries must be a list")
        return False, errors, warnings
    if not entries:
        errors.append("ledger contains no entries")
        return False, errors, warnings
    for index, entry in enumerate(entries):
        if not isinstance(entry, dict):
            errors.append(f"entry {index} must be an object")
            continue
        missing = sorted(REQUIRED_ENTRY_FIELDS - set(entry))
        if missing:
            errors.append(f"entry {index} missing fields: {', '.join(missing)}")
        if entry.get("final_evidence_approved") is not False or entry.get("final_verdict_frozen") is not False:
            errors.append(f"entry {index} attempts final evidence approval")
        if entry.get("solver_approved") is not False or entry.get("odb_metrics_approved") is not False:
            errors.append(f"entry {index} attempts solver or ODB metrics approval")
        if "WARNING" in str(entry.get("supervisor_review_status", "")) or "WARNING" in str(entry.get("ledger_decision", "")):
            warnings.append(f"entry {index} was accepted with warnings")
    return not errors, errors, warnings


def validate_non_solver_evidence_summary(payload: dict[str, Any]) -> tuple[bool, list[str]]:
    errors: list[str] = []
    required = [
        "schema_version",
        "stage",
        "task_id",
        "task_dir",
        "summary_status",
        "gate_decision",
        "ledger_json_path",
        "ledger_md_path",
        "entries_reviewed",
        "automatic_execution_performed",
        "final_evidence_approved",
        "final_verdict_frozen",
        "solver_approved",
        "odb_metrics_approved",
        "task_final_evidence_ledger_updated",
        "safety_flags",
    ]
    for key in required:
        if key not in payload:
            errors.append(f"missing required field: {key}")
    if payload.get("schema_version") != SCHEMA_VERSION:
        errors.append("schema_version must be 0.1")
    if payload.get("stage") != STAGE:
        errors.append("stage must be Stage 5.0H")
    if payload.get("summary_status") not in SUMMARY_STATUSES:
        errors.append("unknown non-solver evidence summary status")
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
    if payload.get("summary_status") in {READY_STATUS, READY_WARNINGS_STATUS}:
        if payload.get("gate_decision") not in {READY_GATE, READY_WARNINGS_GATE}:
            errors.append("ready summary must use pending supervisor ack gate decision")
        if not payload.get("handoff_path"):
            errors.append("ready summary must create a handoff to PipelineSupervisor")
    return not errors, errors
