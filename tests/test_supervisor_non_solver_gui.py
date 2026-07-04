from __future__ import annotations

from pathlib import Path

from abqpilot.gui.action_controller import GuiActionController


def test_supervisor_non_solver_gui_actions_import(tmp_path):
    controller = GuiActionController(project_root=Path(tmp_path))
    assert hasattr(controller, "supervisor_review_non_solver_revalidation")
    assert hasattr(controller, "report_supervisor_non_solver_review")
