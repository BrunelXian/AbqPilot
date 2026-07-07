from abqpilot.gui.controlled_solver_real_gate_card import build_controlled_solver_real_gate_card


def test_real_gate_card_smoke_task_only_and_callback_free(tmp_path) -> None:
    card = build_controlled_solver_real_gate_card(tmp_path)
    assert card["title"] == "Controlled Solver Human Gate [SMOKE TASK CREATED]"
    assert card["smoke_task_only"] is True
    assert card["arbitrary_task_gate_write_enabled"] is False
    assert card["solver_execution_allowed"] is False
    assert card["solver_request_created"] is False
    assert card["backend_callback"] is None
    assert "final evidence remains locked" in card["required_copy"]
