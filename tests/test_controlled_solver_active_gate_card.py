from abqpilot.gui.controlled_solver_active_gate_card import build_controlled_solver_active_gate_card


def test_active_gate_card_is_design_only_callback_free(tmp_path) -> None:
    card = build_controlled_solver_active_gate_card(tmp_path)
    assert card["title"] == "Controlled Solver Active Human Gate Record [DESIGN ONLY]"
    assert card["action_allowed"] is False
    assert card["backend_callback"] is None
    assert "Active gate record design only" in card["required_copy"]
    assert "Human approval does not execute solver" in card["required_copy"]
    assert "Final evidence remains locked" in card["required_copy"]
