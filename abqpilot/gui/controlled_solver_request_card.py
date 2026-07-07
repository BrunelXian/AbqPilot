from __future__ import annotations

from pathlib import Path
from typing import Any

from abqpilot.gui.controlled_solver_real_gate_creation import SMOKE_TASK_ID


def build_controlled_solver_request_card(project_root: str | Path = r"D:\Projects\AbqPilot-v2") -> dict[str, Any]:
    task = Path(project_root) / "runs" / "tasks" / SMOKE_TASK_ID
    draft_json = task / "artifacts" / "request_drafts" / "CONTROLLED_SOLVER_REQUEST_DRAFT_SCHEMA.json"
    return {
        "title": "Controlled Solver Request Draft Schema [DRAFT ONLY]",
        "task_id": SMOKE_TASK_ID,
        "draft_json": str(draft_json),
        "draft_exists": draft_json.exists(),
        "source_gate_validated": draft_json.exists(),
        "source_handoff_draft_validated": draft_json.exists(),
        "candidate_hash_verified": draft_json.exists(),
        "target_agent": "ExecutionAgent",
        "request_active": False,
        "executable_request": False,
        "solver_execution_allowed": False,
        "solver_request_created": False,
        "future_execution_stage_required": True,
        "final_evidence_locked": True,
        "action_allowed": False,
        "backend_callback": None,
        "required_copy": [
            "Controlled Solver Request Draft Schema [DRAFT ONLY]",
            "Draft schema only; not an active solver request",
            "No solver_request.json is created",
            "No solver execution",
            "Future ExecutionAgent stage is required",
            "Final evidence remains locked",
        ],
    }
