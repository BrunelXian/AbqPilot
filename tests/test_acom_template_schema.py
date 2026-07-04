from __future__ import annotations

from abqpilot.acom.template_registry import list_templates
from abqpilot.acom.template_schema import validate_template_definition


def test_every_template_has_required_safety_flags() -> None:
    for template in list_templates():
        assert validate_template_definition(template) == []
        assert template.codex_auto_execution_allowed is False
        assert template.requires_human_operator is True
        assert template.codex_summary_is_final_evidence is False
        assert template.requires_pipeline_protocol is True
        assert template.requires_run_record is True
        assert template.requires_handoff_record is True
