from __future__ import annotations

import json
from pathlib import Path

from abqpilot.gui.workflow_state import GuiWorkflowState, inspect_gui_workflow_state


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _scaffold(task: Path) -> Path:
    task.mkdir(parents=True, exist_ok=True)
    (task / "TRACE_INDEX.md").write_text("---\ndoc_type: trace_index\ntask_id: task\nstatus: SCAFFOLDED\n---\n", encoding="utf-8")
    (task / "trace").mkdir()
    (task / "handoffs").mkdir()
    (task / "gates").mkdir()
    return task


def test_gui_workflow_state_enum_includes_required_states():
    values = {state.value for state in GuiWorkflowState}
    assert "GUI_STATE_NON_SOLVER_SUMMARY_ACKNOWLEDGED" in values
    assert "GUI_STATE_ACOM_RESULT_ACCEPTED_PENDING_REVALIDATION" in values
    assert "FINAL_EVIDENCE_APPROVED" not in values
    assert "FINAL_VERDICT_FROZEN" not in values
    assert "SOLVER_APPROVED" not in values
    assert "ODB_APPROVED" not in values
    assert "METRICS_APPROVED" not in values


def test_stage5_0i_smoke_task_classified_as_acknowledged():
    task = Path("D:/Projects/AbqPilot-v2/runs/tasks/stage5_0f_non_solver_revalidation_smoke")
    result = inspect_gui_workflow_state(task)
    assert result["state"] == "GUI_STATE_NON_SOLVER_SUMMARY_ACKNOWLEDGED"
    assert result["final_evidence_locked"] is True
    assert result["high_risk_actions_disabled"] is True


def test_fresh_scaffold_task_classified(tmp_path):
    task = _scaffold(tmp_path / "fresh")
    assert inspect_gui_workflow_state(task)["state"] == "GUI_STATE_TASK_SCAFFOLDED"


def test_acom_handoff_task_classified(tmp_path):
    task = _scaffold(tmp_path / "handoff")
    (task / "codex_handoff").mkdir()
    assert inspect_gui_workflow_state(task)["state"] == "GUI_STATE_ACOM_HANDOFF_READY"


def test_acom_result_pending_intake_task_classified(tmp_path):
    task = _scaffold(tmp_path / "pending_intake")
    _write_json(task / "codex_result" / "structured_result.json", {"schema_version": "0.1"})
    assert inspect_gui_workflow_state(task)["state"] == "GUI_STATE_ACOM_RESULT_PENDING_INTAKE"


def test_acom_result_accepted_pending_revalidation_task_classified(tmp_path):
    task = _scaffold(tmp_path / "accepted_intake")
    _write_json(task / "codex_result" / "acom_result_intake.json", {"pipeline_intake_status": "ACOM_RESULT_ACCEPTED_PENDING_REVALIDATION"})
    assert inspect_gui_workflow_state(task)["state"] == "GUI_STATE_ACOM_RESULT_ACCEPTED_PENDING_REVALIDATION"


def test_revalidation_scaffold_task_classified(tmp_path):
    task = _scaffold(tmp_path / "reval_scaffold")
    _write_json(task / "revalidation" / "DocsStatusAgent_001" / "REVALIDATION_SCAFFOLD.json", {"scaffold_status": "REVALIDATION_SCAFFOLD_READY"})
    assert inspect_gui_workflow_state(task)["state"] == "GUI_STATE_REVALIDATION_SCAFFOLD_READY"


def test_non_solver_revalidation_pending_supervisor_task_classified(tmp_path):
    task = _scaffold(tmp_path / "pending_supervisor")
    _write_json(
        task / "revalidation" / "DocsStatusAgent_001" / "REVALIDATION_EXECUTION_RESULT.json",
        {"result_status": "NON_SOLVER_REVALIDATION_PASS_PENDING_SUPERVISOR"},
    )
    assert inspect_gui_workflow_state(task)["state"] == "GUI_STATE_NON_SOLVER_REVALIDATION_PENDING_SUPERVISOR"


def test_supervisor_review_accepted_task_classified(tmp_path):
    task = _scaffold(tmp_path / "reviewed")
    _write_json(task / "supervisor_review" / "SUPERVISOR_NON_SOLVER_REVIEW_RESULT.json", {"review_status": "SUPERVISOR_NON_SOLVER_REVIEW_ACCEPTED_FOR_LEDGER"})
    assert inspect_gui_workflow_state(task)["state"] == "GUI_STATE_SUPERVISOR_REVIEW_ACCEPTED_FOR_NON_SOLVER_LEDGER"


def test_non_solver_summary_ready_pending_ack_task_classified(tmp_path):
    task = _scaffold(tmp_path / "summary")
    _write_json(task / "evidence_report" / "NON_SOLVER_EVIDENCE_SUMMARY_RESULT.json", {"summary_status": "NON_SOLVER_EVIDENCE_SUMMARY_READY"})
    assert inspect_gui_workflow_state(task)["state"] == "GUI_STATE_NON_SOLVER_SUMMARY_READY_PENDING_ACK"


def test_missing_task_handled_safely(tmp_path):
    result = inspect_gui_workflow_state(tmp_path / "missing")
    assert result["state"] == "GUI_STATE_NO_TASK_SELECTED"
    assert result["final_evidence_locked"] is True
