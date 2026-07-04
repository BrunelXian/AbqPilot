from __future__ import annotations

from typing import Any

from abqpilot.acom.handoff_schema import FORBIDDEN_ACTIONS
from abqpilot.acom.task_templates import DEFAULT_ALLOWED_COMMANDS, DEFAULT_FORBIDDEN_COMMANDS
from abqpilot.acom.template_schema import AcomTemplate, validate_template_definition


MODEL_CONDITION_EVIDENCE = {
    "requires_mcpguard_result_for_model_mutation_or_inp_patch": True,
    "requires_target_patch_isolation": True,
    "requires_original_condition_preservation_check": True,
}

REJECTED_HIGH_RISK_TEMPLATE_IDS = {
    "automatic_solver_run",
    "automatic_solver_retry",
    "automatic_queue_enqueue",
    "automatic_codex_execution",
    "direct_odb_metrics_extraction",
    "source_cae_mutation",
    "source_inp_mutation",
}


def _template(
    template_id: str,
    name: str,
    purpose: str,
    risk: str,
    producer: str,
    receiver: str,
    required: list[str],
    optional: list[str] | None = None,
    requires_mcpguard: bool = False,
    gate_required: bool = False,
    required_context_items: list[str] | None = None,
    evidence_overrides: dict[str, Any] | None = None,
) -> AcomTemplate:
    return AcomTemplate(
        template_id=template_id,
        template_name=name,
        template_version="0.1",
        risk_level=risk,
        allowed_for_stage5_0c=True,
        requires_human_operator=True,
        codex_auto_execution_allowed=False,
        codex_summary_is_final_evidence=False,
        requires_pipeline_protocol=True,
        requires_run_record=True,
        requires_handoff_record=True,
        requires_gate_record_if_high_risk=True,
        requires_mcpguard=requires_mcpguard,
        parameters={"required": required, "optional": optional or []},
        default_forbidden_actions=list(FORBIDDEN_ACTIONS),
        default_required_outputs=[
            "codex_result/structured_result.json",
            "artifact hash list",
            "test result summary when applicable",
            "safety audit summary",
            "secret audit summary",
            "known limitations",
        ],
        default_acceptance_criteria=[
            "Generated handoff remains bounded by allowed and forbidden paths.",
            "Codex is a human-operated external operator only.",
            "Codex summary is not final evidence.",
            "AbqPilot deterministic revalidation is required.",
        ],
        pipeline_mapping={
            "producer_agent": producer,
            "acom_agent": "ACOMAgent",
            "expected_receiver_agent": receiver,
            "run_record_name": f"ACOM_{template_id.upper()}",
            "handoff_record_name": "ACOM_TO_CODEX_OPERATOR",
            "gate_required": gate_required,
        },
        default_allowed_commands=list(DEFAULT_ALLOWED_COMMANDS),
        default_forbidden_commands=list(DEFAULT_FORBIDDEN_COMMANDS),
        default_allowed_paths=["<project_root>", "<task_dir>"],
        default_forbidden_paths=["<project_root>/.env", "<project_root>/CAE_model/sanity_base/sanity_base_v01.cae"],
        purpose=purpose,
        required_context_items=required_context_items or required,
        evidence_contract_overrides=evidence_overrides or (dict(MODEL_CONDITION_EVIDENCE) if requires_mcpguard else {}),
    )


TEMPLATES: dict[str, AcomTemplate] = {
    template.template_id: template
    for template in (
        _template(
            "stage_implementation",
            "Stage implementation",
            "Generate a bounded Codex handoff for implementing a software development stage.",
            "medium",
            "ACOMAgent",
            "SoftwareQAAgent",
            ["current_accepted_status", "target_stage_name", "final_verdict"],
            ["allowed_modules", "forbidden_modules", "tests_to_add", "cli_smoke_commands", "docs_status_updates"],
        ),
        _template(
            "read_only_audit",
            "Read-only audit",
            "Generate a read-only Codex handoff for inspecting files and writing audit artifacts.",
            "low",
            "AuditAgent",
            "AuditAgent",
            ["files_to_inspect", "questions_to_answer", "output_audit_report_path"],
            ["search_terms"],
        ),
        _template(
            "guarded_candidate_preview",
            "Guarded candidate preview",
            "Generate a Codex handoff for creating copied preview candidates without execution.",
            "high",
            "CandidateBuilderAgent",
            "GuardAgent",
            ["source_candidate_path", "target_change", "forbidden_scope", "output_preview_path"],
            ["mcpguard_not_applicable_reason"],
            requires_mcpguard=True,
            gate_required=True,
        ),
        _template(
            "controlled_execution_planning",
            "Controlled execution planning",
            "Generate a planning-only Codex handoff for controlled execution requirements.",
            "high",
            "GuardAgent",
            "PipelineSupervisor",
            ["eligibility_gates", "approval_token_requirements", "expected_run_directory"],
            ["expected_command_preview", "monitoring_requirements", "diagnosis_requirements"],
            gate_required=True,
        ),
        _template(
            "job_odb_diagnosis_review",
            "Job ODB diagnosis review",
            "Generate a handoff for reviewing job/ODB diagnosis artifacts.",
            "medium",
            "ExecutionAgent",
            "DiagnosisAgent",
            ["job_dir", "job_name", "odb_acceptability_criteria"],
            ["abqjobpilot_record_source", "log_paths"],
        ),
        _template(
            "mcpguard_review",
            "MCPGuard review",
            "Generate a handoff for reviewing Model Condition Preservation Guard artifacts.",
            "medium",
            "CandidateBuilderAgent",
            "GuardAgent",
            ["source_jnl", "source_inp", "candidate_inp", "declared_target_changes"],
            ["solver_inp", "expected_condition_findings"],
            requires_mcpguard=True,
        ),
        _template(
            "abqjobpilot_record_audit",
            "abqjobpilot record audit",
            "Generate a read-only audit handoff for abqjobpilot queue/live_status/reports records.",
            "medium",
            "ExecutionAgent",
            "DiagnosisAgent",
            ["runtime_dir", "expected_fields"],
            ["record_filters"],
        ),
        _template(
            "docs_status_update",
            "Docs status update",
            "Generate a Codex handoff for updating docs/status after accepted stage.",
            "low",
            "EvidenceReportAgent",
            "DocsStatusAgent",
            ["accepted_verdict", "files_to_update", "status_summary"],
            ["behavior_changes_allowed"],
        ),
        _template(
            "test_expansion",
            "Test expansion",
            "Generate a Codex handoff for test expansion only.",
            "low",
            "SoftwareQAAgent",
            "SoftwareQAAgent",
            ["target_modules", "required_test_cases", "pytest_command"],
            ["forbidden_production_behavior_changes"],
        ),
        _template(
            "safety_secret_audit",
            "Safety and secret audit",
            "Generate a Codex handoff for safety/secret/subprocess audit review.",
            "low",
            "SoftwareQAAgent",
            "SoftwareQAAgent",
            ["safety_rg_commands", "secret_rg_commands", "subprocess_rg_commands", "audit_report_format"],
            ["allowed_hits", "forbidden_hits"],
        ),
    )
}


def list_templates() -> list[AcomTemplate]:
    return list(TEMPLATES.values())


def get_template(template_id: str) -> AcomTemplate:
    if template_id in REJECTED_HIGH_RISK_TEMPLATE_IDS:
        raise ValueError(f"high-risk ACOM template is not registered in Stage 5.0C: {template_id}")
    try:
        return TEMPLATES[template_id]
    except KeyError as exc:
        raise ValueError(f"unknown ACOM template id: {template_id}") from exc


def validate_template_pack() -> dict[str, Any]:
    errors: list[str] = []
    required = {
        "stage_implementation",
        "read_only_audit",
        "guarded_candidate_preview",
        "controlled_execution_planning",
        "job_odb_diagnosis_review",
        "mcpguard_review",
        "abqjobpilot_record_audit",
        "docs_status_update",
        "test_expansion",
        "safety_secret_audit",
    }
    missing = sorted(required - set(TEMPLATES))
    errors.extend(f"missing required template: {item}" for item in missing)
    for rejected in sorted(REJECTED_HIGH_RISK_TEMPLATE_IDS):
        if rejected in TEMPLATES:
            errors.append(f"high-risk execution template must not be registered: {rejected}")
    for template in TEMPLATES.values():
        errors.extend(f"{template.template_id}: {error}" for error in validate_template_definition(template))
    return {
        "verdict": "ACOM_TEMPLATE_PACK_VALID" if not errors else "ACOM_TEMPLATE_PACK_INVALID",
        "success": not errors,
        "template_count": len(TEMPLATES),
        "template_ids": sorted(TEMPLATES),
        "errors": errors,
    }
