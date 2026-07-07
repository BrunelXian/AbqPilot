from __future__ import annotations

from pathlib import Path
from typing import Any

from abqpilot.gui.controlled_solver_real_gate_creation import SMOKE_TASK_ID


def build_controlled_solver_request_preflight_card(project_root: str | Path = r"D:\Projects\AbqPilot-v2") -> dict[str, Any]:
    task = Path(project_root) / "runs" / "tasks" / SMOKE_TASK_ID
    result_json = task / "artifacts" / "request_preflight" / "CONTROLLED_SOLVER_REQUEST_PREFLIGHT_RESULT.json"
    return {
        "title": "Controlled Solver Request Preflight [NO EXECUTION]",
        "task_id": SMOKE_TASK_ID,
        "result_json": str(result_json),
        "preflight_exists": result_json.exists(),
        "source_gate_validated": result_json.exists(),
        "source_handoff_draft_validated": result_json.exists(),
        "source_request_draft_validated": result_json.exists(),
        "candidate_hash_verified": result_json.exists(),
        "solver_command_label_validated": result_json.exists(),
        "output_dir_policy_validated": result_json.exists(),
        "resource_policy_validated": result_json.exists(),
        "preflight_only": True,
        "request_active": False,
        "executable_request": False,
        "solver_execution_allowed": False,
        "solver_request_created": False,
        "future_execution_stage_required": True,
        "final_evidence_locked": True,
        "action_allowed": False,
        "backend_callback": None,
        "required_copy": [
            "Controlled Solver Request Preflight [NO EXECUTION]",
            "Preflight only; no solver execution",
            "No solver_request.json is created",
            "No output directory for execution is created",
            "Future ExecutionAgent stage is required",
            "Final evidence remains locked",
        ],
    }
