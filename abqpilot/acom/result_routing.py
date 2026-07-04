from __future__ import annotations

import re
from typing import Any


ROUTES: dict[str, dict[str, Any]] = {
    "stage_implementation": {
        "downstream_agents": ["SoftwareQAAgent", "DocsStatusAgent"],
        "primary_downstream_agent": "SoftwareQAAgent",
        "revalidation_run_name": "SOFTWARE_QA_REVALIDATION",
    },
    "read_only_audit": {
        "downstream_agents": ["AuditAgent", "EvidenceReportAgent"],
        "primary_downstream_agent": "AuditAgent",
        "revalidation_run_name": "AUDIT_REVALIDATION",
    },
    "guarded_candidate_preview": {
        "downstream_agents": ["CandidateBuilderAgent", "GuardAgent"],
        "primary_downstream_agent": "GuardAgent",
        "revalidation_run_name": "GUARD_REVALIDATION",
    },
    "controlled_execution_planning": {
        "downstream_agents": ["PipelineSupervisor"],
        "primary_downstream_agent": "PipelineSupervisor",
        "revalidation_run_name": "SUPERVISOR_GATE_REVIEW",
    },
    "job_odb_diagnosis_review": {
        "downstream_agents": ["DiagnosisAgent"],
        "primary_downstream_agent": "DiagnosisAgent",
        "revalidation_run_name": "DIAGNOSIS_REVALIDATION",
    },
    "mcpguard_review": {
        "downstream_agents": ["GuardAgent"],
        "primary_downstream_agent": "GuardAgent",
        "revalidation_run_name": "GUARD_REVALIDATION",
    },
    "abqjobpilot_record_audit": {
        "downstream_agents": ["DiagnosisAgent"],
        "primary_downstream_agent": "DiagnosisAgent",
        "revalidation_run_name": "DIAGNOSIS_REVALIDATION",
    },
    "docs_status_update": {
        "downstream_agents": ["DocsStatusAgent"],
        "primary_downstream_agent": "DocsStatusAgent",
        "revalidation_run_name": "DOCS_STATUS_REVALIDATION",
    },
    "test_expansion": {
        "downstream_agents": ["SoftwareQAAgent"],
        "primary_downstream_agent": "SoftwareQAAgent",
        "revalidation_run_name": "SOFTWARE_QA_REVALIDATION",
    },
    "safety_secret_audit": {
        "downstream_agents": ["SoftwareQAAgent"],
        "primary_downstream_agent": "SoftwareQAAgent",
        "revalidation_run_name": "SOFTWARE_QA_REVALIDATION",
    },
    "documentation_update": {
        "downstream_agents": ["DocsStatusAgent"],
        "primary_downstream_agent": "DocsStatusAgent",
        "revalidation_run_name": "DOCS_STATUS_REVALIDATION",
    },
    "model_condition_guard_review": {
        "downstream_agents": ["GuardAgent"],
        "primary_downstream_agent": "GuardAgent",
        "revalidation_run_name": "GUARD_REVALIDATION",
    },
    "diagnosis_review": {
        "downstream_agents": ["DiagnosisAgent"],
        "primary_downstream_agent": "DiagnosisAgent",
        "revalidation_run_name": "DIAGNOSIS_REVALIDATION",
    },
}


def route_for_template(template_id: str | None, task_type: str | None = None) -> dict[str, Any]:
    key = template_id or task_type or "read_only_audit"
    return ROUTES.get(
        key,
        {
            "downstream_agents": ["AuditAgent"],
            "primary_downstream_agent": "AuditAgent",
            "revalidation_run_name": "ABQPILOT_REVALIDATION",
        },
    ) | {"template_id": key}


def handoff_agent_token(agent_name: str) -> str:
    token = agent_name
    if token.endswith("Agent"):
        token = token[: -len("Agent")]
    token = re.sub(r"(?<!^)(?=[A-Z])", "_", token)
    token = token.replace("Q_A", "QA").replace("O_D_B", "ODB")
    token = "".join(ch if ch.isalnum() else "_" for ch in token).strip("_")
    return token.upper() + "_AGENT"
