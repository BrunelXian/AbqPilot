from pathlib import Path

from abqpilot.solver.solver_approval import (
    SOLVER_APPROVAL_PHRASE,
    approve_solver_run,
    validate_solver_approval_token,
)
from abqpilot.solver.solver_preflight import prepare_solver_run
from tests.test_solver_preflight import _valid_candidate


def test_approval_token_created_with_correct_phrase(tmp_path):
    run_dir = _prepared_run(tmp_path)

    result = approve_solver_run(run_dir, "human", SOLVER_APPROVAL_PHRASE, expires_hours=24)

    assert result["verdict"] == "APPROVAL_TOKEN_CREATED"
    assert (Path(run_dir) / "approvals" / "solver_run_approval_token.json").exists()
    assert validate_solver_approval_token(run_dir)["status"] == "APPROVAL_TOKEN_VALID"


def test_wrong_approval_phrase_rejected(tmp_path):
    run_dir = _prepared_run(tmp_path)

    result = approve_solver_run(run_dir, "human", "wrong", expires_hours=24)

    assert result["verdict"] == "APPROVAL_TOKEN_INVALID"


def test_approval_hash_mismatch_rejected(tmp_path):
    run_dir = Path(_prepared_run(tmp_path))
    approve_solver_run(run_dir, "human", SOLVER_APPROVAL_PHRASE, expires_hours=24)
    (run_dir / "candidate_sanity_base_power_x2_stage4.inp").write_text("changed", encoding="utf-8")

    validation = validate_solver_approval_token(run_dir)

    assert validation["status"] == "APPROVAL_HASH_MISMATCH"


def _prepared_run(tmp_path):
    candidate, source, evidence = _valid_candidate(tmp_path)
    result = prepare_solver_run(candidate, source, evidence, run_root=tmp_path / "runs", abaqus_command="abq.bat")
    assert result["success"] is True
    return result["details"]["solver_run_dir"]
