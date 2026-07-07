from abqpilot.gui.controlled_solver_dry_run_request_validator import (
    READY,
    validate_controlled_solver_dry_run_request,
)


def _request() -> dict:
    return {
        "request_type": "CONTROLLED_SOLVER_DRY_RUN_REQUEST",
        "stage_id": "STAGE5_2J",
        "source_stage_id": "STAGE5_2I",
        "source_gate_validated": True,
        "source_handoff_draft_validated": True,
        "source_request_draft_validated": True,
        "source_preflight_validated": True,
        "source_preflight_status": "CONTROLLED_SOLVER_REQUEST_PREFLIGHT_PASS_NO_EXECUTION",
        "candidate_hash_verified": True,
        "target_agent": "ExecutionAgent",
        "target_future_stage": "FUTURE_CONTROLLED_SOLVER_EXECUTION_STAGE",
        "dry_run_only": True,
        "materialized_request_artifact": True,
        "materialized_request_filename": "CONTROLLED_SOLVER_DRY_RUN_REQUEST.json",
        "active_request_created": False,
        "request_active": False,
        "executable_request": False,
        "future_execution_stage_required": True,
        "solver_command_label_validated": True,
        "solver_command_path_included": False,
        "solver_command_not_invoked": True,
        "output_dir_policy_validated": True,
        "output_dir_created": False,
        "cpu_policy_validated": True,
        "memory_policy_validated": True,
        "timeout_policy_validated": True,
        "log_capture_policy_validated": True,
        "solver_approved_by_source_gate": True,
        "solver_execution_allowed": False,
        "solver_request_created": False,
        "solver_run": False,
        "queue_runner_launched": False,
        "queue_entry_created": False,
        "odb_opened": False,
        "odb_metrics_approved": False,
        "final_evidence_approved": False,
        "final_verdict_frozen": False,
        "task_final_evidence_ledger_updated": False,
        "downstream_execution_auto_start": False,
    }


def test_dry_run_validator_accepts_safe_request() -> None:
    assert validate_controlled_solver_dry_run_request(_request())["validation_status"] == READY


def test_dry_run_validator_blocks_unsafe_flags() -> None:
    cases = {
        "source_gate_validated": "CONTROLLED_SOLVER_DRY_RUN_REQUEST_BLOCKED_SOURCE_GATE_INVALID",
        "source_handoff_draft_validated": "CONTROLLED_SOLVER_DRY_RUN_REQUEST_BLOCKED_HANDOFF_INVALID",
        "source_request_draft_validated": "CONTROLLED_SOLVER_DRY_RUN_REQUEST_BLOCKED_REQUEST_DRAFT_INVALID",
        "source_preflight_validated": "CONTROLLED_SOLVER_DRY_RUN_REQUEST_BLOCKED_PREFLIGHT_INVALID",
        "candidate_hash_verified": "CONTROLLED_SOLVER_DRY_RUN_REQUEST_BLOCKED_CANDIDATE_HASH_MISMATCH",
        "request_active": "CONTROLLED_SOLVER_DRY_RUN_REQUEST_BLOCKED_ACTIVE_REQUEST",
        "executable_request": "CONTROLLED_SOLVER_DRY_RUN_REQUEST_BLOCKED_EXECUTABLE_REQUEST",
        "solver_execution_allowed": "CONTROLLED_SOLVER_DRY_RUN_REQUEST_BLOCKED_EXECUTION_ALLOWED",
        "solver_request_created": "CONTROLLED_SOLVER_DRY_RUN_REQUEST_BLOCKED_SOLVER_REQUEST_CREATED",
        "solver_run": "CONTROLLED_SOLVER_DRY_RUN_REQUEST_BLOCKED_EXECUTION_ALLOWED",
        "queue_runner_launched": "CONTROLLED_SOLVER_DRY_RUN_REQUEST_BLOCKED_QUEUE_OR_ODB",
        "queue_entry_created": "CONTROLLED_SOLVER_DRY_RUN_REQUEST_BLOCKED_QUEUE_OR_ODB",
        "output_dir_created": "CONTROLLED_SOLVER_DRY_RUN_REQUEST_BLOCKED_QUEUE_OR_ODB",
        "odb_opened": "CONTROLLED_SOLVER_DRY_RUN_REQUEST_BLOCKED_QUEUE_OR_ODB",
        "odb_metrics_approved": "CONTROLLED_SOLVER_DRY_RUN_REQUEST_BLOCKED_QUEUE_OR_ODB",
        "final_evidence_approved": "CONTROLLED_SOLVER_DRY_RUN_REQUEST_BLOCKED_FINAL_EVIDENCE",
        "final_verdict_frozen": "CONTROLLED_SOLVER_DRY_RUN_REQUEST_BLOCKED_FINAL_EVIDENCE",
    }
    for field, expected in cases.items():
        request = _request()
        request[field] = False if field in {"source_gate_validated", "source_handoff_draft_validated", "source_request_draft_validated", "source_preflight_validated", "candidate_hash_verified"} else True
        assert validate_controlled_solver_dry_run_request(request)["validation_status"] == expected


def test_dry_run_validator_blocks_preflight_not_pass() -> None:
    request = _request()
    request["source_preflight_status"] = "CONTROLLED_SOLVER_REQUEST_PREFLIGHT_REVIEW_REQUIRED"
    assert validate_controlled_solver_dry_run_request(request)["validation_status"] == "CONTROLLED_SOLVER_DRY_RUN_REQUEST_BLOCKED_PREFLIGHT_NOT_PASS"
