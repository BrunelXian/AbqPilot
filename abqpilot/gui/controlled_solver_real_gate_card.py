from __future__ import annotations

from pathlib import Path
from typing import Any

from abqpilot.gui.controlled_solver_real_gate_creation import SMOKE_TASK_ID


def build_controlled_solver_real_gate_card(project_root: str | Path = r"D:\Projects\AbqPilot-v2") -> dict[str, Any]:
    task = Path(project_root) / "runs" / "tasks" / SMOKE_TASK_ID
    gate_json = task / "gates" / "GATE_001_CONTROLLED_SOLVER_HUMAN_APPROVAL.json"
    return {
        "title": "Controlled Solver Human Gate [SMOKE TASK CREATED]",
        "task_id": SMOKE_TASK_ID,
        "gate_json": str(gate_json),
        "gate_exists": gate_json.exists(),
        "smoke_task_only": True,
        "arbitrary_task_gate_write_enabled": False,
        "solver_execution_allowed": False,
        "solver_request_created": False,
        "future_execution_stage_required": True,
        "final_evidence_locked": True,
        "action_allowed": False,
        "backend_callback": None,
        "required_copy": [
            "Controlled Solver Human Gate [SMOKE TASK CREATED]",
            "active gate exists only in Stage 5.2F smoke task",
            "solver execution remains disabled",
            "solver request not created",
            "future execution stage required",
            "final evidence remains locked",
        ],
    }
