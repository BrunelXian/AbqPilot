from __future__ import annotations

from abqpilot.gui.action_controller import GuiActionController


def test_acom_gui_actions_import():
    controller = GuiActionController("D:/Projects/AbqPilot-v2")
    assert callable(controller.generate_codex_handoff)
    assert callable(controller.validate_codex_handoff)
    assert callable(controller.intake_codex_result)
    assert callable(controller.report_codex_handoff)
