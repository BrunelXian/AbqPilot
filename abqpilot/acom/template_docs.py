from __future__ import annotations

from abqpilot.acom.template_schema import AcomTemplate


def render_template_description(template: AcomTemplate) -> str:
    mapping = template.pipeline_mapping
    required = "\n".join(f"- `{item}`" for item in template.parameters.get("required", [])) or "- none"
    optional = "\n".join(f"- `{item}`" for item in template.parameters.get("optional", [])) or "- none"
    return f"""# ACOM Template: {template.template_id}

## Purpose
{template.purpose}

## Risk
`{template.risk_level}`

## Pipeline Mapping
- producer_agent: `{mapping.get('producer_agent')}`
- acom_agent: `{mapping.get('acom_agent')}`
- expected_receiver_agent: `{mapping.get('expected_receiver_agent')}`
- run_record_name: `{mapping.get('run_record_name')}`
- handoff_record_name: `{mapping.get('handoff_record_name')}`
- gate_required: `{mapping.get('gate_required')}`

## Required Parameters
{required}

## Optional Parameters
{optional}

## Safety
- requires_human_operator: `{template.requires_human_operator}`
- codex_auto_execution_allowed: `{template.codex_auto_execution_allowed}`
- codex_summary_is_final_evidence: `{template.codex_summary_is_final_evidence}`
- abqpilot_revalidation_required: `True`
- requires_mcpguard: `{template.requires_mcpguard}`
"""
