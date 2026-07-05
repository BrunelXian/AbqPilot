from abqpilot.gui.high_risk_gate_catalog import assert_high_risk_catalog_safety, get_high_risk_gate_catalog
from abqpilot.gui.safe_action_catalog import get_disabled_high_risk_actions


REQUIRED_ACTIONS = {
    "CONTROLLED_SOLVER_RUN",
    "QUEUE_JOB",
    "OPEN_ODB_FOR_DIAGNOSIS",
    "EXTRACT_ODB_METRICS",
    "MUTATE_SOURCE_CAE",
    "MUTATE_SOURCE_INP",
    "ACCEPT_METRICS_FOR_EVIDENCE",
    "APPROVE_FINAL_EVIDENCE",
    "FREEZE_FINAL_VERDICT",
    "DELETE_OR_OVERWRITE_HISTORICAL_ARTIFACT",
    "RUN_CODEX_FROM_GUI",
    "AUTO_SCHEDULE_AGENT",
}


def test_high_risk_gate_catalog_imports_and_contains_required_actions() -> None:
    catalog = get_high_risk_gate_catalog()
    assert {str(action["action_id"]) for action in catalog} == REQUIRED_ACTIONS


def test_every_high_risk_action_is_disabled_preview_only_and_future_gated() -> None:
    forbidden_effects = {
        "FINAL_EVIDENCE_APPROVAL",
        "FINAL_VERDICT_FREEZE",
        "SOLVER_APPROVAL",
        "ODB_ACCEPTANCE",
        "METRICS_APPROVAL",
    }
    for action in get_high_risk_gate_catalog():
        assert action["default_allowed"] is False
        assert action["executable_in_stage_5_2a"] is False
        assert action["preview_only"] is True
        assert action["requires_human_gate"] is True
        assert action["requires_future_stage"] is True
        assert action["final_evidence_effect"] not in forbidden_effects
    assert_high_risk_catalog_safety()


def test_disabled_high_risk_actions_remain_callback_free() -> None:
    disabled = get_disabled_high_risk_actions()
    assert disabled
    assert all(action["allowed"] is False for action in disabled)
    assert all(action.get("backend_method") is None for action in disabled)
