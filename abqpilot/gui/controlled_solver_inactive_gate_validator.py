from __future__ import annotations

from typing import Any


REQUIRED_FALSE_FIELDS = (
    "real_gate_created",
    "active_gate_record_created",
    "task_gate_record_created",
    "solver_approved",
    "solver_run",
    "solver_request_created",
    "queue_runner_launched",
    "odb_opened",
    "odb_metrics_approved",
    "final_evidence_approved",
    "final_verdict_frozen",
    "task_final_evidence_ledger_updated",
)

REQUIRED_FIELDS = {
    "draft_type",
    "gate_type",
    "preview_only",
    "inactive_draft",
    "approval_status",
    "gate_decision",
    "execution_status",
    *REQUIRED_FALSE_FIELDS,
}


def validate_controlled_solver_inactive_gate_draft(draft: dict[str, Any]) -> dict[str, Any]:
    missing = sorted(field for field in REQUIRED_FIELDS if field not in draft)
    if missing:
        return _result("INACTIVE_GATE_DRAFT_INVALID_MISSING_FIELDS", missing_fields=missing)
    if draft.get("draft_type") != "CONTROLLED_SOLVER_RUN_HUMAN_GATE_DRAFT" or draft.get("gate_type") != "CONTROLLED_SOLVER_RUN":
        return _result("INACTIVE_GATE_DRAFT_INVALID_MISSING_FIELDS")
    if draft.get("preview_only") is not True or draft.get("inactive_draft") is not True:
        return _result("INACTIVE_GATE_DRAFT_INVALID_MISSING_FIELDS")
    if draft.get("approval_status") != "NOT_APPROVED" or draft.get("gate_decision") != "PREVIEW_ONLY_NOT_APPROVED":
        return _result("INACTIVE_GATE_DRAFT_BLOCKED_ACTIVE_APPROVAL")
    if draft.get("execution_status") != "NOT_EXECUTABLE":
        return _result("INACTIVE_GATE_DRAFT_BLOCKED_EXECUTION_REQUEST")
    token = draft.get("human_approval_token_preview") or {}
    if token.get("active_approval") is True or draft.get("active_approval") is True:
        return _result("INACTIVE_GATE_DRAFT_BLOCKED_ACTIVE_APPROVAL")
    if draft.get("active_solver_request_path") or draft.get("solver_request_created") is True or draft.get("solver_run") is True:
        return _result("INACTIVE_GATE_DRAFT_BLOCKED_EXECUTION_REQUEST")
    if draft.get("active_task_gate_output_path") or draft.get("active_gate_record_created") is True or draft.get("task_gate_record_created") is True:
        return _result("INACTIVE_GATE_DRAFT_BLOCKED_ACTIVE_GATE_RECORD")
    if draft.get("queue_mutation_output_path") or draft.get("queue_runner_launched") is True:
        return _result("INACTIVE_GATE_DRAFT_BLOCKED_EXECUTION_REQUEST")
    if draft.get("odb_metrics_output_path") or draft.get("odb_metrics_approved") is True:
        return _result("INACTIVE_GATE_DRAFT_BLOCKED_FINAL_EVIDENCE")
    if draft.get("final_evidence_approved") is True or draft.get("final_verdict_frozen") is True or draft.get("task_final_evidence_ledger_updated") is True:
        return _result("INACTIVE_GATE_DRAFT_BLOCKED_FINAL_EVIDENCE")
    for field in REQUIRED_FALSE_FIELDS:
        if draft.get(field) is not False:
            return _result("INACTIVE_GATE_DRAFT_REVIEW_REQUIRED", offending_field=field)
    if draft.get("missing_prerequisites"):
        return _result("INACTIVE_GATE_DRAFT_VALID_WITH_WARNINGS")
    return _result("INACTIVE_GATE_DRAFT_VALID")


def _result(status: str, **extra: Any) -> dict[str, Any]:
    payload = {
        "schema_version": "0.1",
        "stage": "Stage 5.2C",
        "validation_status": status,
        "preview_only": True,
        "inactive_draft": True,
        "active_approval": False,
        "real_gate_created": False,
        "active_gate_record_created": False,
        "task_gate_record_created": False,
        "solver_request_created": False,
        "solver_run": False,
        "final_evidence_approved": False,
        "final_verdict_frozen": False,
    }
    payload.update(extra)
    return payload
