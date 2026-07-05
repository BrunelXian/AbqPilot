from abqpilot.gui.controlled_solver_future_gate_shape import build_expected_future_active_gate_shape
from abqpilot.gui.controlled_solver_inactive_gate_draft import build_controlled_solver_inactive_gate_draft


def test_future_active_gate_shape_is_expected_shape_only(tmp_path) -> None:
    shape = build_expected_future_active_gate_shape("task")
    assert shape["gate_type"] == "CONTROLLED_SOLVER_RUN"
    assert shape["solver_approved"] is True
    assert shape["solver_execution_allowed"] is False
    assert shape["stage_5_2c_expected_shape_only"] is True
    assert shape["active_gate_record_created"] is False


def test_solver_approved_true_only_inside_expected_future_shape(tmp_path) -> None:
    draft = build_controlled_solver_inactive_gate_draft(tmp_path)
    assert draft["solver_approved"] is False
    assert draft["expected_future_active_gate_shape"]["solver_approved"] is True
    assert draft["active_task_gate_output_path"] is None
