from abqpilot.gui.action_panels import build_controlled_solver_gate_panel
from abqpilot.gui.controlled_solver_demo_smoke_v2_card import build_controlled_solver_demo_smoke_v2_card


def test_demo_smoke_v2_card_copy_and_callback(tmp_path) -> None:
    card = build_controlled_solver_demo_smoke_v2_card(tmp_path)
    assert "Stage 5.3A-v2" in card["title"]
    assert card["smoke_demo_only"] is True
    assert card["arbitrary_task_execution_allowed"] is False
    assert card["backend_callback"] is None
    assert "ODB not opened" in card["copy"]
    assert "Metrics not extracted" in card["copy"]
    assert "Final evidence remains locked" in card["copy"]


def test_demo_smoke_v2_panel_action_is_report_only() -> None:
    panel = build_controlled_solver_gate_panel()
    actions = {action["action_id"]: action for action in panel["actions"]}
    action = actions["report_controlled_solver_stage5_3a_v2_demo_smoke_status"]
    assert action["executable"] is False
    assert action["backend_method"] is None
    assert action["arbitrary_task_execution_allowed"] is False
