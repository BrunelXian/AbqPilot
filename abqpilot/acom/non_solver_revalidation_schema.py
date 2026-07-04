from __future__ import annotations

from typing import Any


SCHEMA_VERSION = "0.1"
STAGE = "Stage 5.0F"

SUPPORTED_NON_SOLVER_AGENTS = {
    "DocsStatusAgent",
    "SoftwareQAAgent",
    "AuditAgent",
    "EvidenceReportAgent",
    "PipelineSupervisor",
}

HIGH_RISK_BLOCKED_AGENTS = {
    "GuardAgent",
    "CandidateBuilderAgent",
    "DiagnosisAgent",
    "ExecutionAgent",
    "MetricsAgent",
}

RESULT_STATUSES = {
    "NON_SOLVER_REVALIDATION_PASS_PENDING_SUPERVISOR",
    "NON_SOLVER_REVALIDATION_WARNING_PENDING_SUPERVISOR",
    "NON_SOLVER_REVALIDATION_FAIL_BLOCKED",
    "NON_SOLVER_REVALIDATION_BLOCKED_MISSING_SCAFFOLD",
    "NON_SOLVER_REVALIDATION_BLOCKED_ACOM_INTAKE_NOT_ACCEPTED",
    "NON_SOLVER_REVALIDATION_BLOCKED_UNSUPPORTED_AGENT",
    "NON_SOLVER_REVALIDATION_BLOCKED_HIGH_RISK_AGENT",
    "NON_SOLVER_REVALIDATION_BLOCKED_MISSING_INPUTS",
    "NON_SOLVER_REVALIDATION_BLOCKED_PROTOCOL_INVALID",
    "NON_SOLVER_REVALIDATION_REVIEW_REQUIRED",
}

PASS_STATUS = "NON_SOLVER_REVALIDATION_PASS_PENDING_SUPERVISOR"
WARNING_STATUS = "NON_SOLVER_REVALIDATION_WARNING_PENDING_SUPERVISOR"
FAIL_STATUS = "NON_SOLVER_REVALIDATION_FAIL_BLOCKED"


def validate_non_solver_revalidation_result(payload: dict[str, Any]) -> tuple[bool, list[str]]:
    errors: list[str] = []
    required = [
        "schema_version",
        "stage",
        "task_id",
        "task_dir",
        "revalidation_dir",
        "downstream_agent",
        "result_status",
        "checks",
        "pass_items",
        "warning_items",
        "fail_items",
        "gate_decision",
        "automatic_execution_performed",
        "final_evidence_approved",
        "codex_summary_is_final_evidence",
        "safety_flags",
    ]
    for key in required:
        if key not in payload:
            errors.append(f"missing required field: {key}")
    if payload.get("schema_version") != SCHEMA_VERSION:
        errors.append("schema_version must be 0.1")
    if payload.get("stage") != STAGE:
        errors.append("stage must be Stage 5.0F")
    if payload.get("result_status") not in RESULT_STATUSES:
        errors.append("unknown non-solver revalidation status")
    agent = payload.get("downstream_agent")
    if agent not in SUPPORTED_NON_SOLVER_AGENTS and agent not in HIGH_RISK_BLOCKED_AGENTS:
        errors.append("unknown downstream agent")
    if payload.get("automatic_execution_performed") is not False:
        errors.append("automatic_execution_performed must be false")
    if payload.get("final_evidence_approved") is not False:
        errors.append("final_evidence_approved must be false")
    if payload.get("codex_summary_is_final_evidence") is not False:
        errors.append("codex_summary_is_final_evidence must be false")
    if payload.get("gate_decision") == "APPROVED":
        errors.append("gate_decision must never be APPROVED in Stage 5.0F")
    safety = payload.get("safety_flags")
    if isinstance(safety, dict):
        for key in [
            "codex_cli_called",
            "solver_run",
            "queue_runner_launched",
            "odb_opened",
            "source_cae_mutated",
            "source_inp_mutated",
            "env_read",
            "shell_true_used",
            "automatic_scheduling_added",
            "high_risk_agent_executed",
        ]:
            if safety.get(key) is not False:
                errors.append(f"safety flag must be false: {key}")
    else:
        errors.append("safety_flags must be an object")
    return not errors, errors
