from abqpilot.gui.controlled_solver_token_consumption import build_controlled_solver_token_consumption_design


def test_token_consumption_design_is_non_executing() -> None:
    design = build_controlled_solver_token_consumption_design()
    assert design["one_time_use_required"] is True
    assert design["binds_task_id"] is True
    assert design["binds_candidate_artifact_hash"] is True
    assert design["token_consumption_executes_solver"] is False
    assert design["token_consumption_approves_odb"] is False
    assert design["token_consumption_approves_metrics"] is False
    assert design["token_consumption_approves_final_evidence"] is False
