from abqpilot.gui.controlled_solver_execution_handoff_draft import build_controlled_solver_execution_handoff_draft
from abqpilot.gui.controlled_solver_execution_handoff_validator import validate_controlled_solver_execution_handoff_draft


def _draft() -> dict:
    return build_controlled_solver_execution_handoff_draft(
        "runs/tasks/stage5_2f_controlled_solver_real_gate_smoke",
        {"gate_id": "GATE_001", "decision": "APPROVED_BY_HUMAN", "solver_approved": True},
        "candidate.inp",
        "abc123",
    )


def test_execution_handoff_validator_accepts_safe_draft() -> None:
    result = validate_controlled_solver_execution_handoff_draft(_draft())
    assert result["validation_status"] == "CONTROLLED_SOLVER_EXECUTION_HANDOFF_DRAFT_READY"


def test_execution_handoff_validator_blocks_unsafe_flags() -> None:
    cases = {
        "solver_execution_allowed": "CONTROLLED_SOLVER_EXECUTION_HANDOFF_DRAFT_BLOCKED_EXECUTION_ALLOWED",
        "solver_request_created": "CONTROLLED_SOLVER_EXECUTION_HANDOFF_DRAFT_BLOCKED_SOLVER_REQUEST",
        "solver_run": "CONTROLLED_SOLVER_EXECUTION_HANDOFF_DRAFT_BLOCKED_EXECUTION_ALLOWED",
        "queue_runner_launched": "CONTROLLED_SOLVER_EXECUTION_HANDOFF_DRAFT_BLOCKED_QUEUE_OR_ODB",
        "odb_opened": "CONTROLLED_SOLVER_EXECUTION_HANDOFF_DRAFT_BLOCKED_QUEUE_OR_ODB",
        "odb_metrics_approved": "CONTROLLED_SOLVER_EXECUTION_HANDOFF_DRAFT_BLOCKED_QUEUE_OR_ODB",
        "final_evidence_approved": "CONTROLLED_SOLVER_EXECUTION_HANDOFF_DRAFT_BLOCKED_FINAL_EVIDENCE",
        "final_verdict_frozen": "CONTROLLED_SOLVER_EXECUTION_HANDOFF_DRAFT_BLOCKED_FINAL_EVIDENCE",
    }
    for field, status in cases.items():
        draft = _draft()
        draft[field] = True
        assert validate_controlled_solver_execution_handoff_draft(draft)["validation_status"] == status
