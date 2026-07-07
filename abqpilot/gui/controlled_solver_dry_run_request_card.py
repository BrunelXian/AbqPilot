from __future__ import annotations

from pathlib import Path
from typing import Any

from abqpilot.gui.controlled_solver_real_gate_creation import SMOKE_TASK_ID


def build_controlled_solver_dry_run_request_card(project_root: str | Path | None = None) -> dict[str, Any]:
    root = Path(project_root) if project_root is not None else Path.cwd()
    request_path = root / "runs" / "tasks" / SMOKE_TASK_ID / "artifacts" / "dry_run_requests" / "CONTROLLED_SOLVER_DRY_RUN_REQUEST.json"
    return {
        "title": "Controlled Solver Dry-Run Request [NO EXECUTION]",
        "dry_run_request_exists": request_path.exists(),
        "source_gate_validated": True,
        "source_handoff_draft_validated": True,
        "source_request_draft_validated": True,
        "source_preflight_passed": True,
        "candidate_hash_verified": True,
        "dry_run_request_materialized": request_path.exists(),
        "not_active_solver_request_json": True,
        "dry_run_only": True,
        "request_active": False,
        "executable_request": False,
        "solver_execution_allowed": False,
        "solver_request_created": False,
        "queue_entry_created": False,
        "output_dir_created": False,
        "future_execution_stage_required": True,
        "final_evidence_locked": True,
        "status_badge": "NO EXECUTION",
        "safety_notes": [
            "Dry-run request artifact only; not an active solver_request.json",
            "No Abaqus solver command is executed",
            "No active solver request is created",
            "No queue entry is created",
            "No output execution directory is created",
            "Future ExecutionAgent stage is required",
            "Final evidence remains locked",
        ],
        "backend_callback": None,
    }
