from abqpilot.gui.controlled_solver_real_gate_creation import create_controlled_solver_real_gate_smoke
from abqpilot.gui.controlled_solver_real_gate_validator import validate_controlled_solver_real_gate_smoke


def test_real_gate_validator_reports_no_execution(tmp_path) -> None:
    result = create_controlled_solver_real_gate_smoke(tmp_path)
    validation = result["validation"]
    assert validation["validation_status"] == "CONTROLLED_SOLVER_REAL_GATE_VALID_NO_EXECUTION"
    assert validation["no_solver_request_files_found"] is True
    assert validation["no_queue_files_found"] is True
    assert validation["no_odb_files_found"] is True
    assert validation["no_execution_handoff_found"] is True
    assert validation["no_task_final_evidence_ledger"] is True


def test_real_gate_validator_blocks_active_execution_handoff(tmp_path) -> None:
    result = create_controlled_solver_real_gate_smoke(tmp_path)
    task = tmp_path / "runs" / "tasks" / "stage5_2f_controlled_solver_real_gate_smoke"
    handoff = task / "handoffs" / "BAD_ACTIVE_EXECUTION.md"
    handoff.write_text("solver_auto_start: true\n", encoding="utf-8")
    validation = validate_controlled_solver_real_gate_smoke(task, result["validation"] | {}, {})
    assert validation["no_execution_handoff_found"] is False
