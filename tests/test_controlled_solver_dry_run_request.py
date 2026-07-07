from pathlib import Path

from abqpilot.gui.controlled_solver_dry_run_request import create_controlled_solver_dry_run_request_no_exec
from abqpilot.gui.controlled_solver_execution_handoff_draft import create_controlled_solver_execution_handoff_draft_no_exec
from abqpilot.gui.controlled_solver_real_gate_creation import SMOKE_TASK_ID, create_controlled_solver_real_gate_smoke
from abqpilot.gui.controlled_solver_request_draft import create_controlled_solver_request_draft_no_exec
from abqpilot.gui.controlled_solver_request_preflight import create_controlled_solver_request_preflight_no_exec


def _source_chain(root: Path) -> Path:
    create_controlled_solver_real_gate_smoke(root)
    create_controlled_solver_execution_handoff_draft_no_exec(root)
    create_controlled_solver_request_draft_no_exec(root)
    create_controlled_solver_request_preflight_no_exec(root)
    return root / "runs" / "tasks" / SMOKE_TASK_ID


def test_dry_run_request_materializes_without_execution(tmp_path: Path) -> None:
    task = _source_chain(tmp_path)
    result = create_controlled_solver_dry_run_request_no_exec(tmp_path)
    request = result["dry_run_request"]
    assert result["command_verdict"] == "CONTROLLED_SOLVER_DRY_RUN_REQUEST_MATERIALIZED_NO_EXECUTION"
    assert result["materialization_status"] == "CONTROLLED_SOLVER_DRY_RUN_REQUEST_MATERIALIZED_NO_EXECUTION"
    assert request["request_type"] == "CONTROLLED_SOLVER_DRY_RUN_REQUEST"
    assert request["source_preflight_status"] == "CONTROLLED_SOLVER_REQUEST_PREFLIGHT_PASS_NO_EXECUTION"
    assert request["dry_run_only"] is True
    assert request["materialized_request_artifact"] is True
    assert request["active_request_created"] is False
    assert request["request_active"] is False
    assert request["executable_request"] is False
    assert request["solver_execution_allowed"] is False
    assert request["solver_request_created"] is False
    assert request["solver_run"] is False
    assert request["queue_runner_launched"] is False
    assert request["queue_entry_created"] is False
    assert request["output_dir_created"] is False
    assert request["odb_opened"] is False
    assert request["odb_metrics_approved"] is False
    assert request["final_evidence_approved"] is False
    assert request["final_verdict_frozen"] is False
    assert request["task_final_evidence_ledger_updated"] is False
    assert request["downstream_execution_auto_start"] is False
    assert (task / "artifacts" / "dry_run_requests" / "CONTROLLED_SOLVER_DRY_RUN_REQUEST.json").exists()
    assert (task / "artifacts" / "dry_run_requests" / "CONTROLLED_SOLVER_DRY_RUN_REQUEST.md").exists()
    assert not (task / "solver_request.json").exists()
    assert not (task / "job_request.json").exists()
    assert not (task / "abaqus_job.json").exists()
    assert not (task / "future_controlled_solver_outputs").exists()


def test_dry_run_request_blocks_missing_source(tmp_path: Path) -> None:
    result = create_controlled_solver_dry_run_request_no_exec(tmp_path)
    assert result["command_verdict"] == "CONTROLLED_SOLVER_DRY_RUN_REQUEST_BLOCKED_MISSING_SOURCE_ARTIFACT"
    assert result["dry_run_request_materialized"] is False
    assert result["solver_request_created"] is False
