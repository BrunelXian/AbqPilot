from abqpilot.gui.controlled_solver_request_shape import build_expected_future_solver_request_shape


def test_future_request_shape_is_design_only() -> None:
    shape = build_expected_future_solver_request_shape("task", "GATE_001", "HANDOFF_DRAFT", "candidate.inp", "abc")
    assert shape["request_type"] == "CONTROLLED_SOLVER_RUN"
    assert shape["candidate_inp_sha256"] == "abc"
    assert shape["stage5_2h_shape_only"] is True
    assert shape["active_request_file_created"] is False
    assert shape["solver_execution_allowed"] is False
    assert shape["no_queue_unless_separately_gated"] is True
    assert shape["no_odb_acceptance"] is True
    assert shape["no_metrics_acceptance"] is True
    assert shape["no_final_evidence_approval"] is True
