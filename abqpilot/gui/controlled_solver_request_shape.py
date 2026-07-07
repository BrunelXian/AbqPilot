from __future__ import annotations

from pathlib import Path
from typing import Any


def build_expected_future_solver_request_shape(
    task_id: str,
    source_gate_id: str,
    source_handoff_id: str,
    candidate_inp_path: str | Path,
    candidate_inp_sha256: str,
) -> dict[str, Any]:
    return {
        "schema_version": "0.1",
        "request_type": "CONTROLLED_SOLVER_RUN",
        "request_id": "FUTURE_REQUEST_ID_ASSIGNED_BY_EXECUTION_STAGE",
        "task_id": task_id,
        "source_gate_id": source_gate_id,
        "source_handoff_id": source_handoff_id,
        "candidate_inp_path": str(candidate_inp_path),
        "candidate_inp_sha256": candidate_inp_sha256,
        "solver_command_label": "ABQ2024_FUTURE_CONTROLLED_SOLVER_STAGE",
        "solver_command_path": "FUTURE_STAGE_CONFIGURED_PATH_ONLY",
        "working_directory": "FUTURE_STAGE_WORKING_DIRECTORY",
        "output_directory": "FUTURE_STAGE_OUTPUT_DIRECTORY",
        "cpu_count": "FUTURE_STAGE_POLICY",
        "memory_policy": "FUTURE_STAGE_POLICY",
        "timeout_policy": "FUTURE_STAGE_POLICY",
        "log_capture_policy": "FUTURE_STAGE_POLICY",
        "no_queue_unless_separately_gated": True,
        "no_odb_acceptance": True,
        "no_metrics_acceptance": True,
        "no_final_evidence_approval": True,
        "stage5_2h_shape_only": True,
        "active_request_file_created": False,
        "solver_execution_allowed": False,
    }
