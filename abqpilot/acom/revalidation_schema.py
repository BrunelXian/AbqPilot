from __future__ import annotations

from typing import Any


SCHEMA_VERSION = "0.1"
STAGE = "Stage 5.0E"

REVALIDATION_STATUSES = {
    "REVALIDATION_SCAFFOLD_READY",
    "REVALIDATION_SCAFFOLD_BLOCKED_MISSING_ACOM_INTAKE",
    "REVALIDATION_SCAFFOLD_BLOCKED_ACOM_RESULT_NOT_ACCEPTED",
    "REVALIDATION_SCAFFOLD_BLOCKED_UNKNOWN_DOWNSTREAM_AGENT",
    "REVALIDATION_SCAFFOLD_BLOCKED_MISSING_HANDOFF",
    "REVALIDATION_SCAFFOLD_BLOCKED_PROTOCOL_INVALID",
    "REVALIDATION_REVIEW_REQUIRED",
}

SUPPORTED_DOWNSTREAM_AGENTS = {
    "GuardAgent",
    "DocsStatusAgent",
    "SoftwareQAAgent",
    "DiagnosisAgent",
    "AuditAgent",
    "EvidenceReportAgent",
    "PipelineSupervisor",
    "CandidateBuilderAgent",
}


def validate_revalidation_scaffold(payload: dict[str, Any]) -> tuple[bool, list[str]]:
    errors: list[str] = []
    required = [
        "schema_version",
        "stage",
        "task_id",
        "status",
        "downstream_agent",
        "revalidation_id",
        "automatic_execution_performed",
        "codex_summary_is_final_evidence",
        "accepted_as_final_evidence",
        "gate_decision",
        "package_dir",
        "profile",
    ]
    for key in required:
        if key not in payload:
            errors.append(f"missing required field: {key}")
    if payload.get("schema_version") != SCHEMA_VERSION:
        errors.append("schema_version must be 0.1")
    if payload.get("stage") != STAGE:
        errors.append("stage must be Stage 5.0E")
    if payload.get("status") not in REVALIDATION_STATUSES:
        errors.append("unknown revalidation status")
    if payload.get("downstream_agent") not in SUPPORTED_DOWNSTREAM_AGENTS:
        errors.append("unknown downstream agent")
    if payload.get("automatic_execution_performed") is not False:
        errors.append("automatic_execution_performed must be false")
    if payload.get("codex_summary_is_final_evidence") is not False:
        errors.append("codex_summary_is_final_evidence must be false")
    if payload.get("accepted_as_final_evidence") is not False:
        errors.append("accepted_as_final_evidence must be false")
    if payload.get("gate_decision") not in {"PENDING_REVALIDATION", "BLOCKED"}:
        errors.append("gate_decision must be PENDING_REVALIDATION or BLOCKED")
    return not errors, errors
