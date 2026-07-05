from __future__ import annotations

from pathlib import Path

from abqpilot.gui.layout_sections import build_layout_sections


def test_layout_sections_module_imports_and_builds_cards():
    task = Path("D:/Projects/AbqPilot-v2/runs/tasks/stage5_0f_non_solver_revalidation_smoke")
    layout = build_layout_sections(task, "D:/Projects/AbqPilot-v2")
    assert "top_project_header" in layout
    assert "task_sidebar" in layout
    assert "workflow_timeline" in layout
    assert "next_safe_action_card" in layout
    assert "disabled_high_risk_actions_card" in layout
    assert layout["top_project_header"]["workflow_family"] == "Stage 5 non-solver ACOM governance"


def test_next_safe_action_card_final_evidence_effect_is_non_final_only():
    task = Path("D:/Projects/AbqPilot-v2/runs/tasks/stage5_0f_non_solver_revalidation_smoke")
    card = build_layout_sections(task, "D:/Projects/AbqPilot-v2")["next_safe_action_card"]
    assert card["final_evidence_effect"] in {"NONE", "NON_FINAL_NON_SOLVER_RECORD_ONLY"}
    assert card["final_evidence_effect"] != "FINAL_EVIDENCE_APPROVAL"
    assert card["final_evidence_effect"] != "FINAL_VERDICT_FREEZE"
