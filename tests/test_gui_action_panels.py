from __future__ import annotations

from abqpilot.gui.action_panels import build_action_panels, disabled_actions_have_no_callbacks


def test_action_panels_module_imports_and_groups_actions():
    panels = build_action_panels()
    names = {panel["panel"] for panel in panels}
    assert "Setup / Task" in names
    assert "ACOM" in names
    assert "Result Intake" in names
    assert "Revalidation" in names
    assert "Supervisor" in names
    assert "Evidence Summary" in names
    assert "Reports" in names
    assert "Safety / Disabled" in names


def test_high_risk_actions_render_disabled_without_callbacks():
    assert disabled_actions_have_no_callbacks()
    panels = build_action_panels()
    disabled = [action for panel in panels for action in panel["actions"] if not action["allowed"]]
    assert disabled
    for action in disabled:
        assert action["display_name"].endswith("[DISABLED]")
        assert action["backend_method"] is None
        assert action["disabled_reason"]
