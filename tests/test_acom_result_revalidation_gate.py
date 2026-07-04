from __future__ import annotations

from abqpilot.acom.result_revalidation_gate import gate_decision_for_status


def test_accepted_result_creates_pending_revalidation_gate() -> None:
    decision, required = gate_decision_for_status("ACOM_RESULT_ACCEPTED_PENDING_REVALIDATION")
    assert decision == "PENDING_REVALIDATION"
    assert required is True


def test_rejected_result_creates_blocked_gate() -> None:
    decision, required = gate_decision_for_status("ACOM_RESULT_REJECTED_SAFETY_FLAGS")
    assert decision == "BLOCKED"
    assert required is False


def test_review_required_result_is_not_approved() -> None:
    decision, required = gate_decision_for_status("ACOM_RESULT_REVIEW_REQUIRED")
    assert decision == "PENDING_REVIEW"
    assert decision != "APPROVED"
    assert required is False
