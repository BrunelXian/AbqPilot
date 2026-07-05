from __future__ import annotations

from pathlib import Path

from abqpilot.gui.action_controller import GuiActionController
from abqpilot.gui import actions


def test_non_solver_evidence_summary_gui_actions_import(tmp_path):
    controller = GuiActionController(project_root=Path(tmp_path))
    assert hasattr(controller, "generate_non_solver_evidence_summary")
    assert hasattr(controller, "report_non_solver_evidence_summary")
    assert hasattr(actions, "generate_non_solver_evidence_summary")
    assert hasattr(actions, "report_non_solver_evidence_summary")
