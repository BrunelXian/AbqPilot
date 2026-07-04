from __future__ import annotations


def gate_decision_for_status(status: str) -> tuple[str, bool]:
    if status == "ACOM_RESULT_ACCEPTED_PENDING_REVALIDATION":
        return "PENDING_REVALIDATION", True
    if status == "ACOM_RESULT_REVIEW_REQUIRED":
        return "PENDING_REVIEW", False
    return "BLOCKED", False
