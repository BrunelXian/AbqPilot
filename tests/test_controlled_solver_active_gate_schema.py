from pathlib import Path

from abqpilot.gui.controlled_solver_active_gate_schema import (
    build_controlled_solver_active_gate_schema,
    build_future_execution_handoff_shape,
    write_controlled_solver_active_gate_design,
)


def test_active_gate_schema_required_design_flags(tmp_path: Path) -> None:
    candidate = tmp_path / "candidate.inp"
    candidate.write_text("*Heading\n", encoding="utf-8")
    schema = build_controlled_solver_active_gate_schema("task1", tmp_path, candidate)
    assert schema["gate_type"] == "CONTROLLED_SOLVER_RUN"
    assert schema["decision"] == "APPROVED_BY_HUMAN"
    assert schema["active_record_created_in_stage_5_2d"] is False
    assert schema["real_project_gate_written"] is False
    assert schema["solver_approved"] is True
    assert schema["solver_execution_allowed"] is False
    for field in (
        "solver_request_created",
        "solver_run",
        "queue_runner_launched",
        "odb_opened",
        "odb_metrics_approved",
        "final_evidence_approved",
        "final_verdict_frozen",
        "task_final_evidence_ledger_updated",
    ):
        assert schema[field] is False
    assert schema["candidate_artifact_hash"]


def test_write_active_gate_design_outputs_are_spec_only(tmp_path: Path) -> None:
    result = write_controlled_solver_active_gate_design(tmp_path, task_id="task1", task_dir=tmp_path)
    assert result["verdict"] == "CONTROLLED_SOLVER_ACTIVE_GATE_DESIGN_REPORT_READY"
    for path in result["output_paths"].values():
        assert Path(path).exists()
    details = result["details"]
    assert details["real_project_gate_written"] is False
    assert details["writer_enabled"] is False
    assert details["solver_request_created"] is False
    assert details["task_final_evidence_ledger_updated"] is False


def test_future_execution_handoff_shape_is_design_only() -> None:
    handoff = build_future_execution_handoff_shape()
    assert handoff["handoff_type"] == "CONTROLLED_SOLVER_APPROVAL_TO_EXECUTION"
    assert handoff["to_agent"] == "ExecutionAgent"
    assert handoff["expected_future_execution_handoff_shape"] is True
    assert handoff["active_execution_handoff_written_in_stage_5_2d"] is False
    assert handoff["solver_auto_start"] is False
