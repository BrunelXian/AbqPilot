from abqpilot.gui.action_panels import build_controlled_solver_gate_panel
from abqpilot.gui.app import main
from abqpilot.gui.controlled_solver_execution_handoff_card import build_controlled_solver_execution_handoff_card


def test_gui_app_imports_for_stage5_2g() -> None:
    assert main is not None


def test_execution_handoff_card_is_callback_free() -> None:
    card = build_controlled_solver_execution_handoff_card()
    assert card["title"] == "Controlled Solver Execution Handoff Draft [DRAFT ONLY]"
    assert card["active_execution_handoff"] is False
    assert card["handoff_active_for_execution"] is False
    assert card["solver_execution_allowed"] is False
    assert card["solver_request_created"] is False
    assert card["backend_callback"] is None
    assert "No solver execution" in card["required_copy"]
    assert "Future ExecutionAgent stage is required" in card["required_copy"]
    assert "Final evidence remains locked" in card["required_copy"]


def test_execution_handoff_panel_action_has_no_execute_callback() -> None:
    panel = build_controlled_solver_gate_panel()
    action = [item for item in panel["actions"] if item["action_id"] == "report_controlled_solver_stage5_2g_handoff_draft"][0]
    assert action["executable"] is False
    assert action["backend_method"] is None
