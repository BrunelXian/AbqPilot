from abqpilot.gui.app import AbqPilotGui
from abqpilot.gui.controlled_solver_gate_card import build_controlled_solver_gate_card


def test_controlled_solver_gate_card_copy_and_callback_status(tmp_path) -> None:
    card = build_controlled_solver_gate_card(tmp_path)
    copy = "\n".join(card["copy"])
    assert "Preview only; not a solver approval" in copy
    assert "No Abaqus solver command is executed" in copy
    assert "Final evidence remains locked" in copy
    assert card["backend_callback"] is None
    assert card["action_allowed"] is False


def test_gui_app_imports_for_controlled_solver_gate_card() -> None:
    assert AbqPilotGui is not None
