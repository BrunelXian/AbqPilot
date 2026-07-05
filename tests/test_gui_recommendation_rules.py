from abqpilot.gui.recommendation_rules import NextStepStatus, recommendation_for_workflow_state


def _state(value: str) -> dict:
    return {
        "state": value,
        "current_stage_label": value,
        "latest_status": None,
        "gate_records": {"latest_decision": None},
        "warning_messages": [],
    }


def test_recommendation_rules_imports() -> None:
    assert NextStepStatus.READY.value == "NEXT_STEP_READY"


def test_all_required_workflow_states_map_deterministically() -> None:
    cases = {
        "GUI_STATE_NO_TASK_SELECTED": "NEXT_STEP_NO_TASK_SELECTED",
        "GUI_STATE_TASK_SCAFFOLDED": "NEXT_STEP_READY",
        "GUI_STATE_ACOM_HANDOFF_READY": "NEXT_STEP_WAITING_FOR_EXTERNAL_CODEX_RESULT",
        "GUI_STATE_ACOM_RESULT_PENDING_INTAKE": "NEXT_STEP_READY",
        "GUI_STATE_ACOM_RESULT_ACCEPTED_PENDING_REVALIDATION": "NEXT_STEP_PENDING_REVALIDATION",
        "GUI_STATE_NON_SOLVER_REVALIDATION_PENDING_SUPERVISOR": "NEXT_STEP_PENDING_SUPERVISOR_REVIEW",
        "GUI_STATE_SUPERVISOR_REVIEW_ACCEPTED_FOR_NON_SOLVER_LEDGER": "NEXT_STEP_READY",
        "GUI_STATE_NON_SOLVER_SUMMARY_READY_PENDING_ACK": "NEXT_STEP_PENDING_SUMMARY_ACK",
        "GUI_STATE_NON_SOLVER_SUMMARY_ACKNOWLEDGED": "NEXT_STEP_NON_SOLVER_WORKFLOW_ACKNOWLEDGED",
        "GUI_STATE_BLOCKED": "NEXT_STEP_BLOCKED",
        "GUI_STATE_REVIEW_REQUIRED": "NEXT_STEP_REVIEW_REQUIRED",
    }
    for state, expected in cases.items():
        result = recommendation_for_workflow_state(_state(state))
        assert result["recommendation_status"] == expected
        assert result["auto_execute_allowed"] is False
        assert result["final_evidence_effect"] != "FINAL_EVIDENCE_APPROVAL"
        assert result["final_evidence_effect"] != "FINAL_VERDICT_FREEZE"


def test_acom_handoff_ready_waits_for_external_codex_result() -> None:
    result = recommendation_for_workflow_state(_state("GUI_STATE_ACOM_HANDOFF_READY"))
    assert result["recommendation_status"] == "NEXT_STEP_WAITING_FOR_EXTERNAL_CODEX_RESULT"
    assert result["codex_execution_allowed"] is False
    assert any("GUI does not call Codex CLI" in item for item in result["warnings"])


def test_revalidation_scaffold_low_risk_agent_can_recommend_non_solver_revalidation() -> None:
    result = recommendation_for_workflow_state(_state("GUI_STATE_REVALIDATION_SCAFFOLD_READY"), downstream_agent="DocsStatusAgent")
    assert result["recommendation_status"] == "NEXT_STEP_READY"
    assert result["recommended_action_id"] == "execute_non_solver_revalidation"


def test_revalidation_scaffold_high_risk_agent_is_blocked_for_execution() -> None:
    result = recommendation_for_workflow_state(_state("GUI_STATE_REVALIDATION_SCAFFOLD_READY"), downstream_agent="GuardAgent")
    assert result["recommendation_status"] == "NEXT_STEP_REVIEW_REQUIRED"
    assert result["recommended_action_id"] != "execute_non_solver_revalidation"
    assert result["blocked_reasons"]


def test_non_solver_acknowledged_says_final_evidence_locked() -> None:
    result = recommendation_for_workflow_state(_state("GUI_STATE_NON_SOLVER_SUMMARY_ACKNOWLEDGED"))
    assert result["recommendation_status"] == "NEXT_STEP_NON_SOLVER_WORKFLOW_ACKNOWLEDGED"
    assert any("Final evidence remains locked" in item for item in result["warnings"])
