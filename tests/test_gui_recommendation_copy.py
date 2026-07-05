from abqpilot.gui.recommendation_copy import FORBIDDEN_ACTION_GUIDANCE, recommendation_safety_notes


def test_recommendation_copy_imports_and_lists_forbidden_actions() -> None:
    notes = recommendation_safety_notes()
    assert "Recommendation only; no automatic execution" in notes
    assert "Final evidence remains locked" in notes
    assert "GUI does not call Codex CLI" in notes
    assert "Run Solver" in FORBIDDEN_ACTION_GUIDANCE
    assert "Freeze Final Verdict" in FORBIDDEN_ACTION_GUIDANCE
