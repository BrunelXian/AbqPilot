from __future__ import annotations

from pathlib import Path

from abqpilot.gui.layout_sections import build_layout_sections
from abqpilot.gui.workflow_presenter import build_gui_workflow_presenter


def test_status_cards_include_required_copy():
    task = Path("D:/Projects/AbqPilot-v2/runs/tasks/stage5_0f_non_solver_revalidation_smoke")
    layout = build_layout_sections(task, "D:/Projects/AbqPilot-v2")
    copy = "\n".join(layout["copy"])
    assert "Final evidence remains locked" in copy
    assert "Non-final / non-solver" in copy
    assert "GUI does not call Codex CLI" in copy
    assert "Solver, ODB, metrics, and model mutation are disabled" in copy


def test_gui_presenter_exposes_timeline_text():
    task = Path("D:/Projects/AbqPilot-v2/runs/tasks/stage5_0f_non_solver_revalidation_smoke")
    presenter = build_gui_workflow_presenter(task, "D:/Projects/AbqPilot-v2")
    assert "Supervisor Ack" in presenter["workflow_timeline_text"]
