from abqpilot.gui.controlled_solver_future_handoff_shape import build_expected_future_solver_execution_handoff_shape
from abqpilot.gui.controlled_solver_inactive_gate_draft import build_controlled_solver_inactive_gate_draft


def test_future_execution_handoff_shape_targets_execution_agent_only_as_future_shape() -> None:
    shape = build_expected_future_solver_execution_handoff_shape("task", "candidate.inp")
    assert shape["to_agent"] == "ExecutionAgent"
    assert shape["stage_5_2c_expected_shape_only"] is True
    assert shape["active_execution_handoff_created"] is False
    assert shape["no_odb_metrics_approval"] is True
    assert shape["no_final_evidence_approval"] is True


def test_future_execution_handoff_is_not_active_executable_handoff(tmp_path) -> None:
    draft = build_controlled_solver_inactive_gate_draft(tmp_path)
    handoff = draft["expected_future_solver_execution_handoff_shape"]
    assert handoff["to_agent"] == "ExecutionAgent"
    assert handoff["active_execution_handoff_created"] is False
    assert draft["solver_request_created"] is False
