from __future__ import annotations

import hashlib
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any


SOLVER_APPROVAL_PHRASE = "I_APPROVE_ABQPILOT_CONTROLLED_SOLVER_RUN_FUTURE_STAGE"
TOKEN_TYPE = "CONTROLLED_SOLVER_RUN_APPROVAL"
TOKEN_VERSION = "0.1"

ACKNOWLEDGEMENT_FLAGS = (
    "understands_solver_will_run",
    "understands_cpu_time_risk",
    "understands_files_will_be_created",
    "understands_no_final_evidence_approval",
    "understands_no_odb_metrics_acceptance",
    "understands_no_queue_mutation_unless_separately_gated",
)


def sha256_file(path: str | Path) -> str | None:
    candidate = Path(path)
    if not candidate.exists() or not candidate.is_file():
        return None
    digest = hashlib.sha256()
    with candidate.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def build_controlled_solver_approval_token_schema(
    task_id: str,
    task_dir: str | Path,
    candidate_artifact_path: str | Path | None = None,
    approval_phrase_supplied: str = "",
) -> dict[str, Any]:
    candidate = Path(candidate_artifact_path) if candidate_artifact_path else None
    return {
        "token_type": TOKEN_TYPE,
        "token_version": TOKEN_VERSION,
        "task_id": task_id,
        "task_dir": str(Path(task_dir)),
        "candidate_artifact_hash": sha256_file(candidate) if candidate else None,
        "candidate_artifact_path": str(candidate) if candidate else None,
        "intended_solver_command_label": "configured-controlled-abaqus-command",
        "allowed_output_dir": str(Path(task_dir) / "future_controlled_solver_run"),
        "approver_type": "HUMAN",
        "approval_phrase_required": SOLVER_APPROVAL_PHRASE,
        "approval_phrase_supplied": approval_phrase_supplied,
        "acknowledgement_flags": {flag: False for flag in ACKNOWLEDGEMENT_FLAGS},
        "expires_at_optional": (datetime.now() + timedelta(hours=24)).isoformat(timespec="seconds"),
        "one_time_use": True,
        "preview_only_in_stage_5_2b": True,
        "active_approval": False,
    }


def build_valid_preview_token(
    task_id: str,
    task_dir: str | Path,
    candidate_artifact_path: str | Path | None = None,
) -> dict[str, Any]:
    token = build_controlled_solver_approval_token_schema(
        task_id=task_id,
        task_dir=task_dir,
        candidate_artifact_path=candidate_artifact_path,
        approval_phrase_supplied=SOLVER_APPROVAL_PHRASE,
    )
    token["acknowledgement_flags"] = {flag: True for flag in ACKNOWLEDGEMENT_FLAGS}
    return token
