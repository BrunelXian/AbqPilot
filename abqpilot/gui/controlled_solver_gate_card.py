from __future__ import annotations

from pathlib import Path
from typing import Any

from abqpilot.gui.controlled_solver_gate_preview import build_controlled_solver_gate_preview


def build_controlled_solver_gate_card(task_dir: str | Path | None = None, candidate_inp: str | Path | None = None) -> dict[str, Any]:
    preview = build_controlled_solver_gate_preview(task_dir=task_dir, candidate_inp=candidate_inp)
    return {
        "title": "Controlled Solver Run [LOCKED]",
        "status_badge": "PREVIEW_ONLY",
        "gate_type": preview["gate_type"],
        "readiness_status": preview["readiness_status"],
        "approval_status": preview["approval_status"],
        "execution_status": preview["execution_status"],
        "preview_only": True,
        "action_allowed": False,
        "backend_callback": None,
        "copy": [
            "Preview only; not a solver approval",
            "Human approval token is not active in Stage 5.2B",
            "No Abaqus solver command is executed",
            "No solver request file is created",
            "Future solver approval and future solver execution must be separate stages",
            "Final evidence remains locked",
            "ODB and metrics remain disabled",
            "Queue mutation remains disabled",
        ],
        "missing_prerequisites": preview["missing_prerequisites"],
        "blocked_items": preview["blocked_items"],
        "token_validation_status": preview["approval_token_validation_preview"]["validation_status"],
        "real_gate_created": False,
        "solver_request_created": False,
        "solver_approved": False,
        "solver_run": False,
        "odb_opened": False,
        "queue_runner_launched": False,
        "final_evidence_approved": False,
        "final_verdict_frozen": False,
        "task_final_evidence_ledger_updated": False,
    }
