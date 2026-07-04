from __future__ import annotations

from abqpilot.gui.action_controller import GuiActionController


def test_acom_revalidation_gui_actions_import():
    controller = GuiActionController("D:/Projects/AbqPilot-v2")
    assert callable(controller.scaffold_acom_revalidation)
    assert callable(controller.report_acom_revalidation)
