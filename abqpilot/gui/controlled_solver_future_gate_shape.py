from __future__ import annotations

from typing import Any


def build_expected_future_active_gate_shape(task_id: str, gate_id: str = "GATE_FUTURE_CONTROLLED_SOLVER_APPROVAL") -> dict[str, Any]:
    return {
        "doc_type": "gate_decision",
        "gate_id": gate_id,
        "gate_type": "CONTROLLED_SOLVER_RUN",
        "task_id": task_id,
        "transition": "GUARD_VALIDATION_TO_CONTROLLED_SOLVER_EXECUTION",
        "decision": "APPROVED_BY_HUMAN",
        "human_approval_required": True,
        "human_approval_token_valid": True,
        "solver_approved": True,
        "solver_request_allowed": True,
        "solver_execution_allowed": False,
        "odb_open_allowed": False,
        "metrics_approval_allowed": False,
        "final_evidence_approval_allowed": False,
        "stage_5_2c_expected_shape_only": True,
        "active_gate_record_created": False,
    }
