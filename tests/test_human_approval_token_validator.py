from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path

from abqpilot.gui.human_approval_token import build_valid_preview_token
from abqpilot.gui.human_approval_token_validator import validate_controlled_solver_preview_token


def _candidate(tmp_path: Path) -> Path:
    path = tmp_path / "candidate.inp"
    path.write_text("*Heading\n", encoding="utf-8")
    return path


def test_valid_preview_token_returns_future_stage_status(tmp_path: Path) -> None:
    candidate = _candidate(tmp_path)
    token = build_valid_preview_token("task", tmp_path, candidate)
    result = validate_controlled_solver_preview_token(token, "task", tmp_path, candidate)
    assert result["validation_status"] == "TOKEN_PREVIEW_VALID_FOR_FUTURE_STAGE"


def test_task_mismatch_returns_invalid_task_mismatch(tmp_path: Path) -> None:
    candidate = _candidate(tmp_path)
    token = build_valid_preview_token("task", tmp_path, candidate)
    result = validate_controlled_solver_preview_token(token, "other", tmp_path, candidate)
    assert result["validation_status"] == "TOKEN_PREVIEW_INVALID_TASK_MISMATCH"


def test_candidate_hash_mismatch_returns_invalid_hash(tmp_path: Path) -> None:
    candidate = _candidate(tmp_path)
    token = build_valid_preview_token("task", tmp_path, candidate)
    candidate.write_text("*Heading\nchanged\n", encoding="utf-8")
    result = validate_controlled_solver_preview_token(token, "task", tmp_path, candidate)
    assert result["validation_status"] == "TOKEN_PREVIEW_INVALID_CANDIDATE_HASH"


def test_wrong_phrase_returns_invalid_phrase(tmp_path: Path) -> None:
    candidate = _candidate(tmp_path)
    token = build_valid_preview_token("task", tmp_path, candidate)
    token["approval_phrase_supplied"] = "wrong"
    result = validate_controlled_solver_preview_token(token, "task", tmp_path, candidate)
    assert result["validation_status"] == "TOKEN_PREVIEW_INVALID_APPROVAL_PHRASE"


def test_missing_acknowledgements_returns_invalid_acknowledgements(tmp_path: Path) -> None:
    candidate = _candidate(tmp_path)
    token = build_valid_preview_token("task", tmp_path, candidate)
    token["acknowledgement_flags"]["understands_solver_will_run"] = False
    result = validate_controlled_solver_preview_token(token, "task", tmp_path, candidate)
    assert result["validation_status"] == "TOKEN_PREVIEW_INVALID_ACKNOWLEDGEMENTS"


def test_expired_token_returns_invalid_expired(tmp_path: Path) -> None:
    candidate = _candidate(tmp_path)
    token = build_valid_preview_token("task", tmp_path, candidate)
    token["expires_at_optional"] = (datetime.now() - timedelta(hours=1)).isoformat(timespec="seconds")
    result = validate_controlled_solver_preview_token(token, "task", tmp_path, candidate)
    assert result["validation_status"] == "TOKEN_PREVIEW_INVALID_EXPIRED"


def test_active_approval_attempt_is_blocked(tmp_path: Path) -> None:
    candidate = _candidate(tmp_path)
    token = build_valid_preview_token("task", tmp_path, candidate)
    token["active_approval"] = True
    result = validate_controlled_solver_preview_token(token, "task", tmp_path, candidate)
    assert result["validation_status"] == "TOKEN_PREVIEW_BLOCKED_ACTIVE_APPROVAL_ATTEMPT"
