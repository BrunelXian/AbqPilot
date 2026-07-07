import json
from pathlib import Path

from abqpilot.gui.controlled_solver_execution_handoff_draft import (
    create_controlled_solver_execution_handoff_draft_no_exec,
)
from abqpilot.gui.controlled_solver_real_gate_creation import SMOKE_TASK_ID, create_controlled_solver_real_gate_smoke


def test_execution_handoff_draft_created_from_stage5_2f_source(tmp_path: Path) -> None:
    create_controlled_solver_real_gate_smoke(tmp_path)
    result = create_controlled_solver_execution_handoff_draft_no_exec(tmp_path)
    assert result["command_verdict"] == "CONTROLLED_SOLVER_EXECUTION_HANDOFF_DRAFT_CREATED_NO_EXECUTION"
    assert result["source_gate_validation_status"] == "CONTROLLED_SOLVER_REAL_GATE_VALID_NO_EXECUTION"
    assert result["candidate_hash_verified"] is True
    task = tmp_path / "runs" / "tasks" / SMOKE_TASK_ID
    draft_json = task / "artifacts" / "handoff_drafts" / "CONTROLLED_SOLVER_EXECUTION_HANDOFF_DRAFT.json"
    draft_md = task / "artifacts" / "handoff_drafts" / "CONTROLLED_SOLVER_EXECUTION_HANDOFF_DRAFT.md"
    assert draft_json.exists()
    assert draft_md.exists()
    draft = json.loads(draft_json.read_text(encoding="utf-8"))
    assert draft["draft_type"] == "CONTROLLED_SOLVER_EXECUTION_HANDOFF_DRAFT"
    assert draft["draft_only"] is True
    assert draft["active_execution_handoff"] is False
    assert draft["handoff_active_for_execution"] is False
    assert draft["to_agent"] == "ExecutionAgent"
    assert draft["execution_status"] == "NOT_EXECUTABLE"
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
    assert not (task / "handoffs" / "HANDOFF_002_CONTROLLED_SOLVER_EXECUTION.md").exists()


def test_execution_handoff_draft_blocks_missing_source(tmp_path: Path) -> None:
    result = create_controlled_solver_execution_handoff_draft_no_exec(tmp_path)
    assert result["command_verdict"] == "CONTROLLED_SOLVER_EXECUTION_HANDOFF_DRAFT_BLOCKED_MISSING_SOURCE_GATE_OR_CANDIDATE"
    assert result["draft_created"] is False
    assert result["solver_request_created"] is False
