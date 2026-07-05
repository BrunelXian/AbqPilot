from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

from abqpilot.gui.human_approval_token import ACKNOWLEDGEMENT_FLAGS, SOLVER_APPROVAL_PHRASE, TOKEN_TYPE, TOKEN_VERSION, sha256_file


TOKEN_STATUSES = {
    "TOKEN_PREVIEW_VALID_FOR_FUTURE_STAGE",
    "TOKEN_PREVIEW_INVALID_MISSING_FIELDS",
    "TOKEN_PREVIEW_INVALID_TASK_MISMATCH",
    "TOKEN_PREVIEW_INVALID_CANDIDATE_HASH",
    "TOKEN_PREVIEW_INVALID_APPROVAL_PHRASE",
    "TOKEN_PREVIEW_INVALID_ACKNOWLEDGEMENTS",
    "TOKEN_PREVIEW_INVALID_EXPIRED",
    "TOKEN_PREVIEW_BLOCKED_ACTIVE_APPROVAL_ATTEMPT",
}


def validate_controlled_solver_preview_token(
    token: dict[str, Any],
    task_id: str,
    task_dir: str | Path,
    candidate_artifact_path: str | Path | None = None,
    now: datetime | None = None,
) -> dict[str, Any]:
    required = {
        "token_type",
        "token_version",
        "task_id",
        "task_dir",
        "candidate_artifact_hash",
        "candidate_artifact_path",
        "approval_phrase_required",
        "approval_phrase_supplied",
        "acknowledgement_flags",
        "one_time_use",
        "preview_only_in_stage_5_2b",
        "active_approval",
    }
    missing = sorted(key for key in required if key not in token)
    if missing:
        return _result("TOKEN_PREVIEW_INVALID_MISSING_FIELDS", missing_fields=missing)
    if token.get("active_approval") is True:
        return _result("TOKEN_PREVIEW_BLOCKED_ACTIVE_APPROVAL_ATTEMPT")
    if token.get("token_type") != TOKEN_TYPE or token.get("token_version") != TOKEN_VERSION:
        return _result("TOKEN_PREVIEW_INVALID_MISSING_FIELDS")
    if token.get("task_id") != task_id or str(Path(str(token.get("task_dir")))) != str(Path(task_dir)):
        return _result("TOKEN_PREVIEW_INVALID_TASK_MISMATCH")
    candidate = Path(candidate_artifact_path) if candidate_artifact_path else Path(str(token.get("candidate_artifact_path")))
    expected_hash = sha256_file(candidate)
    if expected_hash and token.get("candidate_artifact_hash") != expected_hash:
        return _result("TOKEN_PREVIEW_INVALID_CANDIDATE_HASH")
    if token.get("approval_phrase_required") != SOLVER_APPROVAL_PHRASE or token.get("approval_phrase_supplied") != SOLVER_APPROVAL_PHRASE:
        return _result("TOKEN_PREVIEW_INVALID_APPROVAL_PHRASE")
    acknowledgements = token.get("acknowledgement_flags") or {}
    if any(acknowledgements.get(flag) is not True for flag in ACKNOWLEDGEMENT_FLAGS):
        return _result("TOKEN_PREVIEW_INVALID_ACKNOWLEDGEMENTS")
    expires_at = token.get("expires_at_optional")
    if expires_at:
        try:
            expiry = datetime.fromisoformat(str(expires_at))
        except ValueError:
            return _result("TOKEN_PREVIEW_INVALID_EXPIRED")
        if expiry < (now or datetime.now()):
            return _result("TOKEN_PREVIEW_INVALID_EXPIRED")
    if token.get("one_time_use") is not True or token.get("preview_only_in_stage_5_2b") is not True:
        return _result("TOKEN_PREVIEW_INVALID_MISSING_FIELDS")
    return _result("TOKEN_PREVIEW_VALID_FOR_FUTURE_STAGE")


def _result(status: str, **extra: Any) -> dict[str, Any]:
    payload = {
        "schema_version": "0.1",
        "stage": "Stage 5.2B",
        "validation_status": status,
        "preview_only": True,
        "active_approval": False,
        "solver_approved": False,
        "solver_run": False,
        "real_gate_created": False,
        "solver_request_created": False,
    }
    payload.update(extra)
    return payload
