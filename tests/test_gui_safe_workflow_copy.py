from __future__ import annotations

from pathlib import Path

from abqpilot.gui.workflow_presenter import build_gui_workflow_presenter, render_workflow_presenter_text


def test_workflow_copy_mentions_final_evidence_locked_and_no_solver_paths():
    task = Path("D:/Projects/AbqPilot-v2/runs/tasks/stage5_0f_non_solver_revalidation_smoke")
    text = render_workflow_presenter_text(build_gui_workflow_presenter(task, "D:/Projects/AbqPilot-v2"))
    assert "Non-final / non-solver record" in text
    assert "Final evidence remains locked" in text
    assert "Supervisor acknowledgement does not freeze final verdict" in text
    assert "Solver, ODB, metrics, and model mutation are disabled in this stage" in text


def test_workflow_presenter_mentions_codex_revalidation_boundary():
    task = Path("D:/Projects/AbqPilot-v2/runs/tasks/stage5_0f_non_solver_revalidation_smoke")
    presenter = build_gui_workflow_presenter(task, "D:/Projects/AbqPilot-v2")
    safety = presenter["sections"]["Safety / Audit Status"]
    assert safety["codex_result_copy"] == "Codex results require AbqPilot revalidation."
    assert presenter["sections"]["Downstream Revalidation"]["high_risk_agent_warning"].startswith("GuardAgent")
