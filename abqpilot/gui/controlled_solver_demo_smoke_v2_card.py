from __future__ import annotations

import json
from pathlib import Path
from typing import Any

TASK_ID = "stage5_3a_v2_controlled_solver_demo_smoke"


def build_controlled_solver_demo_smoke_v2_card(project_root: str | Path | None = None) -> dict[str, Any]:
    root = Path(project_root) if project_root is not None else Path.cwd()
    task = root / "runs" / "tasks" / TASK_ID
    status_path = task / "artifacts" / "solver_status" / "CONTROLLED_SOLVER_DEMO_RUN_STATUS.json"
    request_path = task / "artifacts" / "solver_requests" / "solver_request.json"
    status: dict[str, Any] = {}
    if status_path.exists():
        try:
            status = json.loads(status_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            status = {"parse_error": True}
    return {
        "title": "Controlled Solver Demo Smoke Run [Stage 5.3A-v2]", "smoke_demo_only": True, "task_path": str(task),
        "solver_request_exists": request_path.exists(), "status_exists": status_path.exists(), "selected_demo_inp": status.get("candidate_inp_path", ""),
        "solver_status": status.get("solver_status", "NOT_RUN"), "solver_return_code": status.get("solver_return_code"),
        "expected_artifacts_present": status.get("expected_artifacts_present", {}), "odb_produced": status.get("odb_produced", False),
        "odb_not_opened": True, "metrics_not_extracted": True, "final_evidence_locked": True, "queue_entry_created": False,
        "arbitrary_task_execution_allowed": False, "backend_callback": None,
        "copy": ["Demo smoke only", "Stage 5.3A-v2 dedicated task only", "ODB not opened", "Metrics not extracted", "Final evidence remains locked", "No generic solver callback"],
    }
