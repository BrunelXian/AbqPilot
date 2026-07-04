from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RevalidationProfile:
    downstream_agent: str
    run_name: str
    risk_level: str
    next_agent: str
    checklist: tuple[str, ...]
    expected_outputs: tuple[str, ...]


PROFILES: dict[str, RevalidationProfile] = {
    "GuardAgent": RevalidationProfile(
        downstream_agent="GuardAgent",
        run_name="GUARD_AGENT_REVALIDATION",
        risk_level="MEDIUM",
        next_agent="PipelineSupervisor",
        checklist=(
            "StaticValidator review if candidate artifact exists",
            "DiffGuard review if diff artifact exists or candidate/source pair exists",
            "PhysicsGuard review if physical mutation could be involved",
            "MCPGuard review if model condition / INP patch is involved",
            "target patch isolation review",
            "original model condition preservation review",
            "Codex file claims checked against actual files",
            "Codex summary not final evidence",
        ),
        expected_outputs=("Guard revalidation findings", "PENDING_REVALIDATION gate recommendation"),
    ),
    "DocsStatusAgent": RevalidationProfile(
        downstream_agent="DocsStatusAgent",
        run_name="DOCS_STATUS_AGENT_REVALIDATION",
        risk_level="LOW",
        next_agent="PipelineSupervisor",
        checklist=(
            "docs/status files reviewed",
            "no behavior-changing code modifications unless explicitly allowed",
            "PROJECT_STATUS_CURRENT.* consistency checked",
            "ABQPILOT.md / AGENTS.md consistency checked",
            "Codex summary not final evidence",
        ),
        expected_outputs=("Docs/status revalidation findings",),
    ),
    "SoftwareQAAgent": RevalidationProfile(
        downstream_agent="SoftwareQAAgent",
        run_name="SOFTWARE_QA_AGENT_REVALIDATION",
        risk_level="MEDIUM",
        next_agent="PipelineSupervisor",
        checklist=(
            "pytest command review",
            "test result review",
            "safety audit review",
            "secret audit review",
            "subprocess audit review",
            "no unsafe path added",
            "Codex summary not final evidence",
        ),
        expected_outputs=("Software QA revalidation findings",),
    ),
    "DiagnosisAgent": RevalidationProfile(
        downstream_agent="DiagnosisAgent",
        run_name="DIAGNOSIS_AGENT_REVALIDATION",
        risk_level="MEDIUM",
        next_agent="PipelineSupervisor",
        checklist=(
            "job/log/report paths reviewed",
            "abqjobpilot record source reviewed if applicable",
            "diagnosis status reviewed",
            "ODB acceptability criteria reviewed",
            "no direct ODB open",
            "Codex summary not final evidence",
        ),
        expected_outputs=("Diagnosis revalidation findings",),
    ),
    "AuditAgent": RevalidationProfile(
        downstream_agent="AuditAgent",
        run_name="AUDIT_AGENT_REVALIDATION",
        risk_level="LOW",
        next_agent="PipelineSupervisor",
        checklist=(
            "audit questions answered",
            "read-only guarantee checked",
            "input files reviewed",
            "output audit report reviewed",
            "no mutation confirmed",
            "Codex summary not final evidence",
        ),
        expected_outputs=("Audit revalidation findings",),
    ),
    "EvidenceReportAgent": RevalidationProfile(
        downstream_agent="EvidenceReportAgent",
        run_name="EVIDENCE_REPORT_AGENT_REVALIDATION",
        risk_level="MEDIUM",
        next_agent="PipelineSupervisor",
        checklist=(
            "artifact list reviewed",
            "claim boundary reviewed",
            "known limitations reviewed",
            "no final evidence accepted without deterministic checks",
            "Codex summary not final evidence",
        ),
        expected_outputs=("Evidence report revalidation findings",),
    ),
    "PipelineSupervisor": RevalidationProfile(
        downstream_agent="PipelineSupervisor",
        run_name="PIPELINE_SUPERVISOR_REVALIDATION",
        risk_level="MEDIUM",
        next_agent="PipelineSupervisor",
        checklist=(
            "no execution performed",
            "eligibility gates reviewed",
            "human approval requirements reviewed",
            "no automatic approval",
            "Codex summary not final evidence",
        ),
        expected_outputs=("Supervisor gate review package",),
    ),
    "CandidateBuilderAgent": RevalidationProfile(
        downstream_agent="CandidateBuilderAgent",
        run_name="CANDIDATE_BUILDER_AGENT_REVALIDATION",
        risk_level="MEDIUM",
        next_agent="GuardAgent",
        checklist=(
            "candidate file paths exist",
            "source artifacts unchanged",
            "candidate was copied, not in-place mutation",
            "target change declared",
            "forbidden scope preserved",
            "handoff to GuardAgent required",
            "Codex summary not final evidence",
        ),
        expected_outputs=("Candidate builder revalidation findings", "handoff requirement to GuardAgent"),
    ),
}


TEMPLATE_TO_AGENT = {
    "mcpguard_review": "GuardAgent",
    "model_condition_guard_review": "GuardAgent",
    "guarded_candidate_preview": "GuardAgent",
    "docs_status_update": "DocsStatusAgent",
    "documentation_update": "DocsStatusAgent",
    "test_expansion": "SoftwareQAAgent",
    "safety_secret_audit": "SoftwareQAAgent",
    "stage_implementation": "SoftwareQAAgent",
    "job_odb_diagnosis_review": "DiagnosisAgent",
    "abqjobpilot_record_audit": "DiagnosisAgent",
    "diagnosis_review": "DiagnosisAgent",
    "read_only_audit": "AuditAgent",
    "controlled_execution_planning": "PipelineSupervisor",
}


def profile_for_agent(agent: str) -> RevalidationProfile | None:
    return PROFILES.get(agent)


def agent_for_template(template_id: str | None, fallback_agent: str | None = None) -> str | None:
    if template_id and template_id in TEMPLATE_TO_AGENT:
        return TEMPLATE_TO_AGENT[template_id]
    return fallback_agent
