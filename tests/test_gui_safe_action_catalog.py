from __future__ import annotations

from abqpilot.gui.safe_action_catalog import get_disabled_high_risk_actions, get_safe_action_catalog, group_actions_by_panel


def test_safe_action_catalog_contains_stage5_groups():
    panels = group_actions_by_panel()
    assert "ACOM Handoff" in panels
    assert "ACOM Result Intake" in panels
    assert "Downstream Revalidation" in panels
    assert "Non-Solver Revalidation Execution" in panels
    assert "PipelineSupervisor Review" in panels
    assert "EvidenceReportAgent Non-Solver Summary" in panels
    assert "PipelineSupervisor Summary Ack" in panels


def test_high_risk_actions_present_but_disabled():
    disabled = get_disabled_high_risk_actions()
    labels = {str(action["display_name"]) for action in disabled}
    assert "Run Solver [DISABLED]" in labels
    assert "Open ODB [DISABLED]" in labels
    assert "Queue Job [DISABLED]" in labels
    assert "Run Codex [DISABLED]" in labels
    assert "Auto Schedule Agent [DISABLED]" in labels
    assert "Approve Final Evidence [DISABLED]" in labels
    assert "Freeze Final Verdict [DISABLED]" in labels
    assert "Approve Solver / ODB / Metrics [DISABLED]" in labels
    for action in disabled:
        assert action["allowed"] is False
        assert action["disabled_reason"]
        assert action["backend_method"] is None


def test_no_action_can_approve_or_freeze_final_evidence():
    actions = get_safe_action_catalog()
    assert actions
    for action in actions:
        assert action["final_evidence_effect"] in {"NONE", "NON_FINAL_NON_SOLVER_RECORD_ONLY"}
        assert action["final_evidence_effect"] != "FINAL_EVIDENCE_APPROVAL"
        assert action["final_evidence_effect"] != "FINAL_VERDICT_FREEZE"


def test_catalog_contains_safe_workflow_actions():
    ids = {str(action["action_id"]) for action in get_safe_action_catalog()}
    assert "generate_pipeline_acom_handoff" in ids
    assert "intake_acom_result" in ids
    assert "scaffold_acom_revalidation" in ids
    assert "execute_non_solver_revalidation" in ids
    assert "supervisor_review_non_solver_revalidation" in ids
    assert "generate_non_solver_evidence_summary" in ids
    assert "supervisor_ack_non_solver_summary" in ids
