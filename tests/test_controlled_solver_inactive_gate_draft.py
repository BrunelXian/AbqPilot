from pathlib import Path

from abqpilot.gui.controlled_solver_inactive_gate_draft import (
    build_controlled_solver_inactive_gate_draft,
    write_controlled_solver_inactive_gate_draft,
)


def test_inactive_gate_draft_required_flags(tmp_path: Path) -> None:
    draft = build_controlled_solver_inactive_gate_draft(tmp_path)
    assert draft["draft_type"] == "CONTROLLED_SOLVER_RUN_HUMAN_GATE_DRAFT"
    assert draft["gate_type"] == "CONTROLLED_SOLVER_RUN"
    assert draft["preview_only"] is True
    assert draft["inactive_draft"] is True
    assert draft["approval_status"] == "NOT_APPROVED"
    assert draft["gate_decision"] == "PREVIEW_ONLY_NOT_APPROVED"
    assert draft["execution_status"] == "NOT_EXECUTABLE"
    for field in (
        "real_gate_created",
        "active_gate_record_created",
        "task_gate_record_created",
        "solver_approved",
        "solver_run",
        "solver_request_created",
        "queue_runner_launched",
        "odb_opened",
        "odb_metrics_approved",
        "final_evidence_approved",
        "final_verdict_frozen",
        "task_final_evidence_ledger_updated",
    ):
        assert draft[field] is False


def test_write_inactive_gate_draft_outputs(tmp_path: Path) -> None:
    result = write_controlled_solver_inactive_gate_draft(tmp_path, task_dir=tmp_path)
    assert result["verdict"] == "CONTROLLED_SOLVER_INACTIVE_GATE_DRAFT_REPORT_READY"
    for path in result["output_paths"].values():
        assert Path(path).exists()
    draft = result["details"]
    assert draft["inactive_draft"] is True
    assert draft["active_gate_record_created"] is False
    assert draft["solver_request_created"] is False
    assert draft["task_final_evidence_ledger_updated"] is False
