from __future__ import annotations

from pathlib import Path
from typing import Any


def build_controlled_solver_demo_smoke_card(project_root: str | Path | None = None) -> dict[str, Any]:
    root = Path(project_root) if project_root is not None else Path.cwd()
    task = root / "runs" / "tasks" / "stage5_3a_controlled_solver_demo_smoke"
    status_path = task / "artifacts" / "solver_status" / "CONTROLLED_SOLVER_DEMO_RUN_STATUS.json"
    request_path = task / "artifacts" / "solver_requests" / "solver_request.json"
    return {
        "title": "Controlled Solver Demo Smoke Run",
        "smoke_demo_only": True,
        "task_path": str(task),
        "solver_request_exists": request_path.exists(),
        "status_exists": status_path.exists(),
        "odb_not_opened": True,
        "metrics_not_extracted": True,
        "final_evidence_locked": True,
        "queue_entry_created": False,
        "arbitrary_task_execution_allowed": False,
        "backend_callback": None,
        "copy": [
            "Demo smoke only",
            "ODB not opened",
            "Metrics not extracted",
            "Final evidence remains locked",
            "No generic solver callback",
        ],
    }
