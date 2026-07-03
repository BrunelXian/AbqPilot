from abqpilot.solver.dflux_guarded_solver_run import REQUIRED_GUARD_VALUES


def test_dflux_lifecycle_solver_gate_requires_all_stage4_3_fields():
    assert REQUIRED_GUARD_VALUES["static_validator"] == "PASS"
    assert REQUIRED_GUARD_VALUES["diff_guard"] == "PASS"
    assert REQUIRED_GUARD_VALUES["physics_guard"] == "PASS"
    assert REQUIRED_GUARD_VALUES["dflux_lifecycle_validator"] == "PASS"
    assert REQUIRED_GUARD_VALUES["cooling_step_has_dflux_op_new"] is True
    assert REQUIRED_GUARD_VALUES["cooling_step_positive_bf_lines"] == 0
    assert REQUIRED_GUARD_VALUES["scan_step_bf_preserved"] is True
    assert REQUIRED_GUARD_VALUES["unrelated_changes_count"] == 0
