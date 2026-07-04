from __future__ import annotations

import pytest

from abqpilot.acom.task_templates import template_for_task_type


def test_safe_task_template_exists():
    template = template_for_task_type("model_condition_guard_review")
    assert "expected_outputs" in template
    assert any("QueueRunner" in item for item in template["forbidden_actions"])


def test_high_risk_task_type_is_not_supported():
    with pytest.raises(ValueError):
        template_for_task_type("solver_run")
