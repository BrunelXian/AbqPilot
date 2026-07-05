from abqpilot.gui.controlled_solver_inactive_gate_draft import build_controlled_solver_inactive_gate_draft
from abqpilot.gui.controlled_solver_inactive_gate_validator import validate_controlled_solver_inactive_gate_draft


def test_inactive_gate_validator_accepts_safe_draft_with_warnings(tmp_path) -> None:
    draft = build_controlled_solver_inactive_gate_draft(tmp_path)
    result = validate_controlled_solver_inactive_gate_draft(draft)
    assert result["validation_status"] in {"INACTIVE_GATE_DRAFT_VALID", "INACTIVE_GATE_DRAFT_VALID_WITH_WARNINGS"}


def test_inactive_gate_validator_blocks_active_approval(tmp_path) -> None:
    draft = build_controlled_solver_inactive_gate_draft(tmp_path)
    draft["human_approval_token_preview"]["active_approval"] = True
    assert validate_controlled_solver_inactive_gate_draft(draft)["validation_status"] == "INACTIVE_GATE_DRAFT_BLOCKED_ACTIVE_APPROVAL"


def test_inactive_gate_validator_blocks_execution_request(tmp_path) -> None:
    draft = build_controlled_solver_inactive_gate_draft(tmp_path)
    draft["active_solver_request_path"] = "solver_request.json"
    assert validate_controlled_solver_inactive_gate_draft(draft)["validation_status"] == "INACTIVE_GATE_DRAFT_BLOCKED_EXECUTION_REQUEST"


def test_inactive_gate_validator_blocks_active_gate_record(tmp_path) -> None:
    draft = build_controlled_solver_inactive_gate_draft(tmp_path)
    draft["active_task_gate_output_path"] = "gates/GATE_999.md"
    assert validate_controlled_solver_inactive_gate_draft(draft)["validation_status"] == "INACTIVE_GATE_DRAFT_BLOCKED_ACTIVE_GATE_RECORD"


def test_inactive_gate_validator_blocks_final_evidence(tmp_path) -> None:
    draft = build_controlled_solver_inactive_gate_draft(tmp_path)
    draft["final_evidence_approved"] = True
    assert validate_controlled_solver_inactive_gate_draft(draft)["validation_status"] == "INACTIVE_GATE_DRAFT_BLOCKED_FINAL_EVIDENCE"
