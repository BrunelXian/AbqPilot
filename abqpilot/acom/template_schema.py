from __future__ import annotations

from dataclasses import dataclass
from typing import Any


REQUIRED_TEMPLATE_KEYS = (
    "template_id",
    "template_name",
    "template_version",
    "risk_level",
    "allowed_for_stage5_0c",
    "requires_human_operator",
    "codex_auto_execution_allowed",
    "codex_summary_is_final_evidence",
    "requires_pipeline_protocol",
    "requires_run_record",
    "requires_handoff_record",
    "requires_gate_record_if_high_risk",
    "requires_mcpguard",
    "parameters",
    "default_forbidden_actions",
    "default_required_outputs",
    "default_acceptance_criteria",
    "pipeline_mapping",
)


@dataclass(frozen=True)
class AcomTemplate:
    template_id: str
    template_name: str
    template_version: str
    risk_level: str
    allowed_for_stage5_0c: bool
    requires_human_operator: bool
    codex_auto_execution_allowed: bool
    codex_summary_is_final_evidence: bool
    requires_pipeline_protocol: bool
    requires_run_record: bool
    requires_handoff_record: bool
    requires_gate_record_if_high_risk: bool
    requires_mcpguard: bool
    parameters: dict[str, list[str]]
    default_forbidden_actions: list[str]
    default_required_outputs: list[str]
    default_acceptance_criteria: list[str]
    pipeline_mapping: dict[str, Any]
    default_allowed_commands: list[str]
    default_forbidden_commands: list[str]
    default_allowed_paths: list[str]
    default_forbidden_paths: list[str]
    purpose: str
    required_context_items: list[str]
    evidence_contract_overrides: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "template_id": self.template_id,
            "template_name": self.template_name,
            "template_version": self.template_version,
            "risk_level": self.risk_level,
            "allowed_for_stage5_0c": self.allowed_for_stage5_0c,
            "requires_human_operator": self.requires_human_operator,
            "codex_auto_execution_allowed": self.codex_auto_execution_allowed,
            "codex_summary_is_final_evidence": self.codex_summary_is_final_evidence,
            "requires_pipeline_protocol": self.requires_pipeline_protocol,
            "requires_run_record": self.requires_run_record,
            "requires_handoff_record": self.requires_handoff_record,
            "requires_gate_record_if_high_risk": self.requires_gate_record_if_high_risk,
            "requires_mcpguard": self.requires_mcpguard,
            "parameters": self.parameters,
            "default_forbidden_actions": self.default_forbidden_actions,
            "default_required_outputs": self.default_required_outputs,
            "default_acceptance_criteria": self.default_acceptance_criteria,
            "pipeline_mapping": self.pipeline_mapping,
            "default_allowed_commands": self.default_allowed_commands,
            "default_forbidden_commands": self.default_forbidden_commands,
            "default_allowed_paths": self.default_allowed_paths,
            "default_forbidden_paths": self.default_forbidden_paths,
            "purpose": self.purpose,
            "required_context_items": self.required_context_items,
            "evidence_contract_overrides": self.evidence_contract_overrides,
        }


def validate_template_definition(template: AcomTemplate) -> list[str]:
    data = template.to_dict()
    errors = [f"missing template key: {key}" for key in REQUIRED_TEMPLATE_KEYS if key not in data]
    if template.codex_auto_execution_allowed is not False:
        errors.append("codex_auto_execution_allowed must be false")
    if template.requires_human_operator is not True:
        errors.append("requires_human_operator must be true")
    if template.codex_summary_is_final_evidence is not False:
        errors.append("codex_summary_is_final_evidence must be false")
    if template.requires_pipeline_protocol is not True:
        errors.append("requires_pipeline_protocol must be true")
    if template.requires_run_record is not True:
        errors.append("requires_run_record must be true")
    if template.requires_handoff_record is not True:
        errors.append("requires_handoff_record must be true")
    if template.risk_level == "high" and template.requires_gate_record_if_high_risk is not True:
        errors.append("high-risk templates must require a gate record")
    if template.template_id in {"guarded_candidate_preview", "mcpguard_review"} and template.requires_mcpguard is not True:
        errors.append(f"{template.template_id} must require MCPGuard")
    if template.pipeline_mapping.get("acom_agent") != "ACOMAgent":
        errors.append("pipeline_mapping.acom_agent must be ACOMAgent")
    if not template.pipeline_mapping.get("run_record_name"):
        errors.append("pipeline_mapping.run_record_name is required")
    if not template.pipeline_mapping.get("handoff_record_name"):
        errors.append("pipeline_mapping.handoff_record_name is required")
    return errors
