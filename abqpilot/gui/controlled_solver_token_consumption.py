from __future__ import annotations

from typing import Any


def build_controlled_solver_token_consumption_design() -> dict[str, Any]:
    return {
        "schema_version": "0.1",
        "stage": "Stage 5.2D",
        "design_only": True,
        "token_consumption_realized_in_stage_5_2d": False,
        "token_must_be_valid_before_consumption": True,
        "one_time_use_required": True,
        "binds_task_id": True,
        "binds_candidate_artifact_hash": True,
        "requires_exact_approval_phrase": True,
        "requires_all_acknowledgement_flags": True,
        "active_approval_allowed_only_in_future_explicit_stage": True,
        "consumed_token_reuse_allowed": False,
        "token_consumption_executes_solver": False,
        "token_consumption_approves_odb": False,
        "token_consumption_approves_metrics": False,
        "token_consumption_approves_final_evidence": False,
        "token_consumption_freezes_final_verdict": False,
        "rules": [
            "Token must be valid before consumption.",
            "Token must be one-time use.",
            "Token must bind to task_id.",
            "Token must bind to candidate artifact hash.",
            "Token must verify the exact approval phrase.",
            "All acknowledgement flags must be true.",
            "active_approval=true is only allowed in a future explicit active approval stage.",
            "Consumed token must not be reused.",
            "Token consumption creates approval audit data but does not execute solver.",
            "Token consumption does not approve ODB, metrics, final evidence, or final verdict.",
        ],
    }
