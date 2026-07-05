from __future__ import annotations

from pathlib import Path

from abqpilot.gui.action_controller import GuiActionController
from abqpilot.gui import actions


def test_supervisor_non_solver_summary_ack_gui_actions_import(tmp_path):
    controller = GuiActionController(project_root=Path(tmp_path))
    assert hasattr(controller, "supervisor_ack_non_solver_summary")
    assert hasattr(controller, "report_supervisor_non_solver_summary_ack")
    assert hasattr(actions, "supervisor_ack_non_solver_summary")
    assert hasattr(actions, "report_supervisor_non_solver_summary_ack")
