from __future__ import annotations

from typing import Any


def build_expected_future_solver_execution_handoff_shape(
    task_id: str,
    candidate_inp_path: str | None = None,
    input_gate_id: str = "GATE_FUTURE_CONTROLLED_SOLVER_APPROVAL",
) -> dict[str, Any]:
    return {
        "doc_type": "handoff",
        "task_id": task_id,
        "from_agent": "PipelineSupervisor",
        "to_agent": "ExecutionAgent",
        "target_stage": "future controlled solver execution",
        "input_gate_id": input_gate_id,
        "candidate_inp_path": candidate_inp_path,
        "solver_command_label": "configured-controlled-abaqus-command",
        "output_directory": "future_controlled_solver_run",
        "execution_risk_acknowledgement": True,
        "no_odb_metrics_approval": True,
        "no_final_evidence_approval": True,
        "stage_5_2c_expected_shape_only": True,
        "active_execution_handoff_created": False,
    }
