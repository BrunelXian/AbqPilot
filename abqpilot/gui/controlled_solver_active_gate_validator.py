from __future__ import annotations

from typing import Any


REQUIRED_TRUE_FIELDS = (
    "active_gate_record_schema",
    "human_approval_required",
    "human_approval_token_valid",
    "human_approval_token_consumed",
    "one_time_use_token",
    "approval_phrase_verified",
    "acknowledgement_flags_verified",
    "solver_approved",
    "downstream_execution_stage_required",
)

REQUIRED_FALSE_FIELDS = (
    "active_record_created_in_stage_5_2d",
    "real_project_gate_written",
    "solver_execution_allowed",
    "solver_request_created",
    "solver_run",
    "queue_runner_launched",
    "odb_opened",
    "odb_metrics_approved",
    "final_evidence_approved",
    "final_verdict_frozen",
    "task_final_evidence_ledger_updated",
    "token_reuse_allowed",
    "downstream_execution_auto_start",
    "odb_open_allowed",
    "metrics_extraction_allowed",
    "final_evidence_approval_allowed",
)

REQUIRED_FIELDS = {
    "doc_type",
    "gate_type",
    "decision",
    "approval_status",
    "execution_status",
    "task_id",
    "candidate_artifact_path",
    "candidate_artifact_hash",
    "candidate_artifact_hash_algorithm",
    *REQUIRED_TRUE_FIELDS,
    *REQUIRED_FALSE_FIELDS,
}


def validate_controlled_solver_active_gate_schema(record: dict[str, Any]) -> dict[str, Any]:
    missing = sorted(field for field in REQUIRED_FIELDS if field not in record)
    if missing:
        return _result("ACTIVE_SOLVER_GATE_SCHEMA_INVALID_MISSING_FIELDS", missing_fields=missing)
    if record.get("doc_type") != "gate_decision" or record.get("gate_type") != "CONTROLLED_SOLVER_RUN":
        return _result("ACTIVE_SOLVER_GATE_SCHEMA_INVALID_MISSING_FIELDS")
    if record.get("decision") != "APPROVED_BY_HUMAN" or record.get("approval_status") != "APPROVED_BY_HUMAN":
        return _result("ACTIVE_SOLVER_GATE_SCHEMA_REVIEW_REQUIRED")
    if record.get("solver_execution_allowed") is True or record.get("downstream_execution_auto_start") is True:
        return _result("ACTIVE_SOLVER_GATE_SCHEMA_BLOCKED_EXECUTION_ALLOWED")
    if record.get("solver_run") is True:
        return _result("ACTIVE_SOLVER_GATE_SCHEMA_BLOCKED_SOLVER_ALREADY_RUN")
    if record.get("solver_request_created") is True:
        return _result("ACTIVE_SOLVER_GATE_SCHEMA_BLOCKED_SOLVER_REQUEST_CREATED")
    if record.get("queue_runner_launched") is True:
        return _result("ACTIVE_SOLVER_GATE_SCHEMA_BLOCKED_QUEUE_MUTATION")
    if record.get("odb_opened") is True or record.get("odb_open_allowed") is True:
        return _result("ACTIVE_SOLVER_GATE_SCHEMA_BLOCKED_ODB_OPEN")
    if record.get("odb_metrics_approved") is True or record.get("metrics_extraction_allowed") is True:
        return _result("ACTIVE_SOLVER_GATE_SCHEMA_BLOCKED_METRICS_APPROVAL")
    if (
        record.get("final_evidence_approved") is True
        or record.get("final_verdict_frozen") is True
        or record.get("task_final_evidence_ledger_updated") is True
        or record.get("final_evidence_approval_allowed") is True
    ):
        return _result("ACTIVE_SOLVER_GATE_SCHEMA_BLOCKED_FINAL_EVIDENCE")
    if record.get("token_reuse_allowed") is True or record.get("one_time_use_token") is not True:
        return _result("ACTIVE_SOLVER_GATE_SCHEMA_BLOCKED_TOKEN_REUSE")
    for field in REQUIRED_TRUE_FIELDS:
        if record.get(field) is not True:
            return _result("ACTIVE_SOLVER_GATE_SCHEMA_REVIEW_REQUIRED", offending_field=field)
    for field in REQUIRED_FALSE_FIELDS:
        if record.get(field) is not False:
            return _result("ACTIVE_SOLVER_GATE_SCHEMA_REVIEW_REQUIRED", offending_field=field)
    warnings = []
    if not record.get("candidate_artifact_hash"):
        warnings.append("Candidate hash is absent because no allowed candidate artifact was supplied.")
    if warnings:
        return _result("ACTIVE_SOLVER_GATE_SCHEMA_VALID_WITH_WARNINGS", warnings=warnings)
    return _result("ACTIVE_SOLVER_GATE_SCHEMA_VALID")


def _result(status: str, **extra: Any) -> dict[str, Any]:
    payload = {
        "schema_version": "0.1",
        "stage": "Stage 5.2D",
        "validation_status": status,
        "active_record_created_in_stage_5_2d": False,
        "real_project_gate_written": False,
        "solver_execution_allowed": False,
        "solver_request_created": False,
        "solver_run": False,
        "queue_runner_launched": False,
        "odb_opened": False,
        "odb_metrics_approved": False,
        "final_evidence_approved": False,
        "final_verdict_frozen": False,
        "task_final_evidence_ledger_updated": False,
    }
    payload.update(extra)
    return payload
