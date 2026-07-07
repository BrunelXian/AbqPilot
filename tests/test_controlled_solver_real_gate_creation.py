import json
from pathlib import Path

from abqpilot.gui.controlled_solver_real_gate_creation import (
    SMOKE_TASK_ID,
    build_stage5_2f_human_approval_token,
    create_controlled_solver_real_gate_smoke,
    validate_stage5_2f_human_approval_token,
)
from abqpilot.gui.controlled_solver_candidate_hash import compute_candidate_artifact_hash


def test_real_gate_creation_smoke_task_only(tmp_path: Path) -> None:
    result = create_controlled_solver_real_gate_smoke(tmp_path)
    assert result["command_verdict"] == "CONTROLLED_SOLVER_REAL_GATE_SMOKE_CREATED_NO_EXECUTION"
    task = tmp_path / "runs" / "tasks" / SMOKE_TASK_ID
    gate_json = task / "gates" / "GATE_001_CONTROLLED_SOLVER_HUMAN_APPROVAL.json"
    gate_md = task / "gates" / "GATE_001_CONTROLLED_SOLVER_HUMAN_APPROVAL.md"
    assert gate_json.exists()
    assert gate_md.exists()
    assert str(gate_json).endswith(r"stage5_2f_controlled_solver_real_gate_smoke\gates\GATE_001_CONTROLLED_SOLVER_HUMAN_APPROVAL.json")
    gate = json.loads(gate_json.read_text(encoding="utf-8"))
    assert gate["real_project_gate_written"] is True
    assert gate["smoke_task_only"] is True
    assert gate["solver_approved"] is True
    assert gate["solver_execution_allowed"] is False
    assert gate["solver_request_created"] is False
    assert gate["solver_run"] is False
    assert gate["queue_runner_launched"] is False
    assert gate["odb_opened"] is False
    assert gate["final_evidence_approved"] is False
    assert gate["final_verdict_frozen"] is False
    assert gate["task_final_evidence_ledger_updated"] is False
    candidate = task / "artifacts" / "candidates" / "candidate_controlled_solver_smoke.inp"
    token = json.loads((task / "artifacts" / "approvals" / "HUMAN_APPROVAL_TOKEN_PREVIEW.json").read_text(encoding="utf-8"))
    assert candidate.exists()
    assert compute_candidate_artifact_hash(candidate)["hash"] == token["candidate_artifact_hash"] == gate["candidate_artifact_hash"]
    assert token["consumed_once"] is True
    for name in ("solver_request.json", "job_request.json", "abaqus_job.json", "run_solver.bat", "run_solver.cmd", "TASK_FINAL_EVIDENCE_LEDGER.md"):
        assert not (task / name).exists()
    assert not any(task.rglob("*.odb"))


def test_stage5_2f_token_blocks_unsafe_inputs(tmp_path: Path) -> None:
    task = tmp_path / "runs" / "tasks" / SMOKE_TASK_ID
    candidate = task / "artifacts" / "candidates" / "candidate_controlled_solver_smoke.inp"
    candidate.parent.mkdir(parents=True, exist_ok=True)
    candidate.write_text("candidate", encoding="utf-8")
    token = build_stage5_2f_human_approval_token(task, candidate, compute_candidate_artifact_hash(candidate)["hash"])
    assert validate_stage5_2f_human_approval_token(token, task, candidate)["validation_status"] == "STAGE5_2F_TOKEN_VALID"
    wrong_task = dict(token)
    wrong_task["task_id"] = "wrong"
    assert validate_stage5_2f_human_approval_token(wrong_task, task, candidate)["validation_status"] == "STAGE5_2F_TOKEN_BLOCKED_TASK_MISMATCH"
    wrong_hash = dict(token)
    wrong_hash["candidate_artifact_hash"] = "bad"
    assert validate_stage5_2f_human_approval_token(wrong_hash, task, candidate)["validation_status"] == "STAGE5_2F_TOKEN_BLOCKED_CANDIDATE_HASH"
    exec_token = dict(token)
    exec_token["solver_execution_allowed"] = True
    assert validate_stage5_2f_human_approval_token(exec_token, task, candidate)["validation_status"] == "STAGE5_2F_TOKEN_BLOCKED_EXECUTION_ALLOWED"
    final_token = dict(token)
    final_token["final_evidence_approved"] = True
    assert validate_stage5_2f_human_approval_token(final_token, task, candidate)["validation_status"] == "STAGE5_2F_TOKEN_BLOCKED_FINAL_EVIDENCE"
