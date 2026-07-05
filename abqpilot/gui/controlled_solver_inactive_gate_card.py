from __future__ import annotations

from pathlib import Path
from typing import Any

from abqpilot.gui.controlled_solver_inactive_gate_draft import build_controlled_solver_inactive_gate_draft
from abqpilot.gui.controlled_solver_inactive_gate_validator import validate_controlled_solver_inactive_gate_draft


def build_controlled_solver_inactive_gate_card(
    task_dir: str | Path | None = None,
    candidate_inp: str | Path | None = None,
) -> dict[str, Any]:
    draft = build_controlled_solver_inactive_gate_draft(task_dir=task_dir, candidate_inp=candidate_inp)
    validation = validate_controlled_solver_inactive_gate_draft(draft)
    return {
        "title": "Controlled Solver Run [LOCKED]",
        "subtitle": "Inactive Human Gate Draft [PREVIEW ONLY]",
        "status_badge": "INACTIVE_DRAFT",
        "draft_status": draft["draft_status"],
        "validation_status": validation["validation_status"],
        "approval_status": draft["approval_status"],
        "gate_decision": draft["gate_decision"],
        "execution_status": draft["execution_status"],
        "preview_only": True,
        "inactive_draft": True,
        "action_allowed": False,
        "backend_callback": None,
        "copy": [
            "Inactive draft only; not an approval",
            "No active gate record is created in Stage 5.2C",
            "No Abaqus solver command is executed",
            "No solver request file is created",
            "Future active human approval gate creation must be a separate explicit stage",
            "Future solver execution must be a later separate explicit stage",
            "Final evidence remains locked",
            "ODB and metrics remain disabled",
            "Queue mutation remains disabled",
        ],
        "real_gate_created": False,
        "active_gate_record_created": False,
        "task_gate_record_created": False,
        "solver_request_created": False,
        "solver_approved": False,
        "solver_run": False,
        "odb_opened": False,
        "odb_metrics_approved": False,
        "final_evidence_approved": False,
        "final_verdict_frozen": False,
        "task_final_evidence_ledger_updated": False,
    }
