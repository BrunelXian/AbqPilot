from abqpilot.gui.app import AbqPilotGui
from abqpilot.gui.controlled_solver_inactive_gate_card import build_controlled_solver_inactive_gate_card


def test_inactive_gate_card_required_copy_and_callback_status(tmp_path) -> None:
    card = build_controlled_solver_inactive_gate_card(tmp_path)
    text = "\n".join(card["copy"])
    assert "Inactive draft only; not an approval" in text
    assert "No active gate record is created in Stage 5.2C" in text
    assert "No Abaqus solver command is executed" in text
    assert "Final evidence remains locked" in text
    assert card["backend_callback"] is None
    assert card["action_allowed"] is False


def test_gui_app_imports_for_inactive_gate_card() -> None:
    assert AbqPilotGui is not None
