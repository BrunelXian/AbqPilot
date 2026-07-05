from abqpilot.gui.recommendation_cards import build_next_step_recommendation_card, render_next_step_recommendation_text


def test_recommendation_card_imports_and_contains_required_copy() -> None:
    card = build_next_step_recommendation_card(None)
    text = render_next_step_recommendation_text(card)
    assert card["read_only"] is True
    assert card["action_allowed"] is False
    assert card["auto_execute_allowed"] is False
    assert "Recommendation only; no automatic execution" in text
    assert "Final evidence remains locked" in text
    assert "Non-final / non-solver" in text
    assert "GUI does not call Codex CLI" in text
    assert "Solver / ODB / metrics remain disabled" in text
    assert card["final_evidence_effect"] != "FINAL_EVIDENCE_APPROVAL"
    assert card["final_evidence_effect"] != "FINAL_VERDICT_FREEZE"


def test_recommendation_card_disabled_actions_have_no_callbacks() -> None:
    card = build_next_step_recommendation_card(None)
    disabled = card["disabled_actions"]
    assert disabled
    assert all(item["backend_method"] is None for item in disabled)
