from abqpilot.gui.controlled_solver_request_draft import build_controlled_solver_request_draft
from abqpilot.gui.controlled_solver_request_shape import build_expected_future_solver_request_shape
from abqpilot.gui.controlled_solver_request_validator import validate_controlled_solver_request_draft


def _draft() -> dict:
    future = build_expected_future_solver_request_shape("stage5_2f_controlled_solver_real_gate_smoke", "GATE_001", "CONTROLLED_SOLVER_EXECUTION_HANDOFF_DRAFT", "candidate.inp", "abc")
    return build_controlled_solver_request_draft(
        "runs/tasks/stage5_2f_controlled_solver_real_gate_smoke",
        {"gate_id": "GATE_001", "decision": "APPROVED_BY_HUMAN", "solver_approved": True},
        {"draft_type": "CONTROLLED_SOLVER_EXECUTION_HANDOFF_DRAFT"},
        "candidate.inp",
        "abc",
        future,
    )


def test_request_validator_accepts_safe_draft() -> None:
    assert validate_controlled_solver_request_draft(_draft())["validation_status"] == "CONTROLLED_SOLVER_REQUEST_DRAFT_SCHEMA_READY"


def test_request_validator_blocks_unsafe_flags() -> None:
    cases = {
        "request_active": "CONTROLLED_SOLVER_REQUEST_DRAFT_BLOCKED_ACTIVE_REQUEST",
        "executable_request": "CONTROLLED_SOLVER_REQUEST_DRAFT_BLOCKED_ACTIVE_REQUEST",
        "solver_execution_allowed": "CONTROLLED_SOLVER_REQUEST_DRAFT_BLOCKED_EXECUTION_ALLOWED",
        "solver_request_created": "CONTROLLED_SOLVER_REQUEST_DRAFT_BLOCKED_SOLVER_REQUEST_CREATED",
        "solver_run": "CONTROLLED_SOLVER_REQUEST_DRAFT_BLOCKED_EXECUTION_ALLOWED",
        "queue_runner_launched": "CONTROLLED_SOLVER_REQUEST_DRAFT_BLOCKED_QUEUE_OR_ODB",
        "odb_opened": "CONTROLLED_SOLVER_REQUEST_DRAFT_BLOCKED_QUEUE_OR_ODB",
        "odb_metrics_approved": "CONTROLLED_SOLVER_REQUEST_DRAFT_BLOCKED_QUEUE_OR_ODB",
        "final_evidence_approved": "CONTROLLED_SOLVER_REQUEST_DRAFT_BLOCKED_FINAL_EVIDENCE",
        "final_verdict_frozen": "CONTROLLED_SOLVER_REQUEST_DRAFT_BLOCKED_FINAL_EVIDENCE",
    }
    for field, status in cases.items():
        draft = _draft()
        draft[field] = True
        assert validate_controlled_solver_request_draft(draft)["validation_status"] == status
