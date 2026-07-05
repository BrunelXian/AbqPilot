from __future__ import annotations

from pathlib import Path

from abqpilot.gui.action_controller import GuiActionController
from abqpilot.gui.workflow_presenter import build_gui_workflow_presenter


def test_gui_presenter_exposes_required_sections():
    task = Path("D:/Projects/AbqPilot-v2/runs/tasks/stage5_0f_non_solver_revalidation_smoke")
    presenter = build_gui_workflow_presenter(task, "D:/Projects/AbqPilot-v2")
    sections = presenter["sections"]
    for name in [
        "Project Status",
        "Task Workspace",
        "Pipeline Trace",
        "ACOM Handoff",
        "ACOM Result Intake",
        "Downstream Revalidation",
        "Non-Solver Revalidation Execution",
        "PipelineSupervisor Review",
        "EvidenceReportAgent Non-Solver Summary",
        "PipelineSupervisor Summary Ack",
        "Safety / Audit Status",
        "Disabled High-Risk Actions",
    ]:
        assert name in sections


def test_gui_presenter_shows_non_final_boundary():
    task = Path("D:/Projects/AbqPilot-v2/runs/tasks/stage5_0f_non_solver_revalidation_smoke")
    presenter = build_gui_workflow_presenter(task, "D:/Projects/AbqPilot-v2")
    safety = presenter["sections"]["Safety / Audit Status"]
    assert "Non-final" in safety["non_final_boundary"]
    assert "Final evidence remains locked" in safety["badges"]


def test_gui_controller_imports_workflow_helpers(tmp_path):
    controller = GuiActionController(project_root=tmp_path)
    assert controller.workflow_state(None)["verdict"] == "GUI_WORKFLOW_STATE_READY"
    assert controller.workflow_presenter(None)["verdict"] == "GUI_WORKFLOW_PRESENTER_READY"
    assert controller.safe_action_catalog()["verdict"] == "GUI_SAFE_ACTION_CATALOG_READY"


def test_gui_app_imports():
    from abqpilot.gui.app import AbqPilotGui

    assert AbqPilotGui is not None
