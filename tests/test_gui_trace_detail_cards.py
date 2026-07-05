from __future__ import annotations

from pathlib import Path

from abqpilot.gui.trace_detail_cards import build_trace_detail_card, render_trace_detail_text


SMOKE_TASK = Path("D:/Projects/AbqPilot-v2/runs/tasks/stage5_0f_non_solver_revalidation_smoke")


def test_trace_detail_cards_module_imports():
    card = build_trace_detail_card(SMOKE_TASK, "supervisor_ack")
    assert card["read_only"] is True
    assert card["action_allowed"] is False
    assert card["related_files"]["JSON"]


def test_trace_detail_text_contains_required_copy():
    text = render_trace_detail_text(build_trace_detail_card(SMOKE_TASK, "evidence_summary"))
    assert "Read-only trace viewer" in text
    assert "Final evidence remains locked" in text
    assert "Solver / ODB / metrics are disabled" in text
    assert "Codex output is displayed as structured input, not final evidence" in text
    assert "Non-solver summary acknowledgement is non-final" in text
