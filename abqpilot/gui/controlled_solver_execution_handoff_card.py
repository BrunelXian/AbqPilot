from __future__ import annotations

from pathlib import Path
from typing import Any

from abqpilot.gui.controlled_solver_real_gate_creation import SMOKE_TASK_ID


def build_controlled_solver_execution_handoff_card(project_root: str | Path = r"D:\Projects\AbqPilot-v2") -> dict[str, Any]:
    task = Path(project_root) / "runs" / "tasks" / SMOKE_TASK_ID
    draft_json = task / "artifacts" / "handoff_drafts" / "CONTROLLED_SOLVER_EXECUTION_HANDOFF_DRAFT.json"
    return {
        "title": "Controlled Solver Execution Handoff Draft [DRAFT ONLY]",
        "task_id": SMOKE_TASK_ID,
        "draft_json": str(draft_json),
        "draft_exists": draft_json.exists(),
        "source_gate_validated": draft_json.exists(),
        "candidate_hash_verified": draft_json.exists(),
        "to_agent": "ExecutionAgent",
        "active_execution_handoff": False,
        "handoff_active_for_execution": False,
        "solver_execution_allowed": False,
        "solver_request_created": False,
        "future_execution_stage_required": True,
        "final_evidence_locked": True,
        "action_allowed": False,
        "backend_callback": None,
        "required_copy": [
            "Controlled Solver Execution Handoff Draft [DRAFT ONLY]",
            "Draft only; not an active execution handoff",
            "No solver execution",
            "No solver request file is created",
            "Future ExecutionAgent stage is required",
            "Final evidence remains locked",
        ],
    }
