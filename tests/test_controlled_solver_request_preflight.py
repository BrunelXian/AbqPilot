from pathlib import Path

from abqpilot.gui.controlled_solver_execution_handoff_draft import create_controlled_solver_execution_handoff_draft_no_exec
from abqpilot.gui.controlled_solver_real_gate_creation import SMOKE_TASK_ID, create_controlled_solver_real_gate_smoke
from abqpilot.gui.controlled_solver_request_draft import create_controlled_solver_request_draft_no_exec
from abqpilot.gui.controlled_solver_request_preflight import create_controlled_solver_request_preflight_no_exec


def test_request_preflight_passes_without_execution(tmp_path: Path) -> None:
    create_controlled_solver_real_gate_smoke(tmp_path)
    create_controlled_solver_execution_handoff_draft_no_exec(tmp_path)
    create_controlled_solver_request_draft_no_exec(tmp_path)
    result = create_controlled_solver_request_preflight_no_exec(tmp_path)
    assert result["command_verdict"] == "CONTROLLED_SOLVER_REQUEST_PREFLIGHT_REPORT_READY_NO_EXECUTION"
    assert result["preflight_status"] == "CONTROLLED_SOLVER_REQUEST_PREFLIGHT_PASS_NO_EXECUTION"
    assert result["preflight_passed"] is True
    assert result["source_gate_validated"] is True
    assert result["source_handoff_draft_validated"] is True
    assert result["source_request_draft_validated"] is True
    assert result["candidate_hash_verified"] is True
    assert result["solver_command_label_validated"] is True
    assert result["solver_command_path_not_invoked"] is True
    assert result["output_dir_policy_validated"] is True
    assert result["output_dir_created"] is False
    assert result["cpu_policy_validated"] is True
    assert result["memory_policy_validated"] is True
    assert result["timeout_policy_validated"] is True
    assert result["log_capture_policy_validated"] is True
    assert result["preflight_only"] is True
    assert result["active_request_created"] is False
    assert result["request_active"] is False
    assert result["executable_request"] is False
    assert result["solver_execution_allowed"] is False
    assert result["solver_request_created"] is False
    assert result["solver_run"] is False
    assert result["queue_runner_launched"] is False
    assert result["odb_opened"] is False
    assert result["odb_metrics_approved"] is False
    assert result["final_evidence_approved"] is False
    assert result["final_verdict_frozen"] is False
    assert result["task_final_evidence_ledger_updated"] is False
    assert result["downstream_execution_auto_start"] is False
    task = tmp_path / "runs" / "tasks" / SMOKE_TASK_ID
    assert (task / "artifacts" / "request_preflight" / "CONTROLLED_SOLVER_REQUEST_PREFLIGHT_RESULT.json").exists()
    assert not (task / "solver_request.json").exists()
    assert not (task / "job_request.json").exists()
    assert not (task / "abaqus_job.json").exists()


def test_request_preflight_blocks_missing_source(tmp_path: Path) -> None:
    result = create_controlled_solver_request_preflight_no_exec(tmp_path)
    assert result["command_verdict"] == "CONTROLLED_SOLVER_REQUEST_PREFLIGHT_BLOCKED_MISSING_SOURCE_ARTIFACT"
    assert result["preflight_passed"] is False
    assert result["solver_request_created"] is False
