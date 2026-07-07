import json
from pathlib import Path

from abqpilot.gui.controlled_solver_execution_handoff_draft import create_controlled_solver_execution_handoff_draft_no_exec
from abqpilot.gui.controlled_solver_real_gate_creation import SMOKE_TASK_ID, create_controlled_solver_real_gate_smoke
from abqpilot.gui.controlled_solver_request_draft import create_controlled_solver_request_draft_no_exec


def test_request_draft_created_from_source_gate_and_handoff(tmp_path: Path) -> None:
    create_controlled_solver_real_gate_smoke(tmp_path)
    create_controlled_solver_execution_handoff_draft_no_exec(tmp_path)
    result = create_controlled_solver_request_draft_no_exec(tmp_path)
    assert result["command_verdict"] == "CONTROLLED_SOLVER_REQUEST_DRAFT_SCHEMA_CREATED_NO_EXECUTION"
    assert result["source_gate_validation_status"] == "CONTROLLED_SOLVER_REAL_GATE_VALID_NO_EXECUTION"
    assert result["source_handoff_validation_status"] == "CONTROLLED_SOLVER_EXECUTION_HANDOFF_DRAFT_READY"
    assert result["candidate_hash_verified"] is True
    task = tmp_path / "runs" / "tasks" / SMOKE_TASK_ID
    schema = task / "artifacts" / "request_drafts" / "CONTROLLED_SOLVER_REQUEST_DRAFT_SCHEMA.json"
    example = task / "artifacts" / "request_drafts" / "CONTROLLED_SOLVER_REQUEST_DRAFT_EXAMPLE.json"
    validation = task / "artifacts" / "request_drafts" / "CONTROLLED_SOLVER_REQUEST_DRAFT_VALIDATION.json"
    assert schema.exists()
    assert example.exists()
    assert validation.exists()
    draft = json.loads(schema.read_text(encoding="utf-8"))
    assert draft["draft_type"] == "CONTROLLED_SOLVER_REQUEST_DRAFT"
    assert draft["draft_only"] is True
    assert draft["request_active"] is False
    assert draft["executable_request"] is False
    assert draft["target_agent"] == "ExecutionAgent"
    assert draft["solver_command_path_included"] is False
    assert draft["solver_command_not_invoked"] is True
    assert draft["output_dir_created"] is False
    assert draft["solver_execution_allowed"] is False
    assert draft["solver_request_created"] is False
    assert draft["solver_run"] is False
    assert draft["queue_runner_launched"] is False
    assert draft["odb_opened"] is False
    assert draft["odb_metrics_approved"] is False
    assert draft["final_evidence_approved"] is False
    assert draft["final_verdict_frozen"] is False
    assert draft["task_final_evidence_ledger_updated"] is False
    assert draft["downstream_execution_auto_start"] is False
    for name in ("solver_request.json", "job_request.json", "abaqus_job.json", "run_solver.bat", "run_solver.cmd", "TASK_FINAL_EVIDENCE_LEDGER.md"):
        assert not (task / name).exists()


def test_request_draft_blocks_missing_source(tmp_path: Path) -> None:
    result = create_controlled_solver_request_draft_no_exec(tmp_path)
    assert result["command_verdict"] == "CONTROLLED_SOLVER_REQUEST_DRAFT_BLOCKED_MISSING_SOURCE_GATE_OR_HANDOFF"
    assert result["draft_created"] is False
    assert result["solver_request_created"] is False
