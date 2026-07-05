from abqpilot.gui.high_risk_prerequisites import get_prerequisites_for_action


def _ids(action_id: str) -> set[str]:
    return {str(item["prerequisite_id"]) for item in get_prerequisites_for_action(action_id)}


def test_controlled_solver_prerequisites_include_core_guards() -> None:
    ids = _ids("CONTROLLED_SOLVER_RUN")
    assert {"static_validator_pass", "diff_guard_pass", "physics_guard_pass", "mcpguard_pass"} <= ids


def test_odb_prerequisites_include_future_acceptance_gate() -> None:
    ids = _ids("OPEN_ODB_FOR_DIAGNOSIS")
    assert "future_odb_acceptance_gate" in ids


def test_final_freeze_prerequisites_include_future_explicit_stage() -> None:
    ids = _ids("FREEZE_FINAL_VERDICT")
    assert "future_final_freeze_stage" in ids


def test_codex_gui_prerequisites_keep_runtime_bridge_future_only() -> None:
    ids = _ids("RUN_CODEX_FROM_GUI")
    assert {"future_runtime_bridge_design", "secret_leakage_controls", "abort_rollback_policy"} <= ids
