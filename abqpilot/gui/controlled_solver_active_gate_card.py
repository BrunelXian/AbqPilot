from __future__ import annotations

from pathlib import Path
from typing import Any

from abqpilot.gui.controlled_solver_active_gate_schema import (
    build_controlled_solver_active_gate_schema,
    build_future_execution_handoff_shape,
)
from abqpilot.gui.controlled_solver_active_gate_validator import validate_controlled_solver_active_gate_schema
from abqpilot.gui.controlled_solver_token_consumption import build_controlled_solver_token_consumption_design


def build_controlled_solver_active_gate_card(
    task_dir: str | Path | None = None,
    candidate_artifact_path: str | Path | None = None,
) -> dict[str, Any]:
    task = Path(task_dir) if task_dir else None
    gate = build_controlled_solver_active_gate_schema(
        task_id=task.name if task else "UNSELECTED_TASK",
        task_dir=task,
        candidate_artifact_path=candidate_artifact_path,
    )
    validation = validate_controlled_solver_active_gate_schema(gate)
    return {
        "title": "Controlled Solver Active Human Gate Record [DESIGN ONLY]",
        "fixture_writer_title": "Active Gate Writer [TEST FIXTURE ONLY]",
        "status_badge": "TEST_FIXTURE_ONLY",
        "gate_type": "CONTROLLED_SOLVER_RUN",
        "validation_status": validation["validation_status"],
        "active_record_schema_preview": gate,
        "token_consumption_rules": build_controlled_solver_token_consumption_design(),
        "future_execution_handoff_shape": build_future_execution_handoff_shape(gate),
        "writer_status": "REAL_TASK_WRITE_DISABLED",
        "fixture_write_policy": "TEST_FIXTURE_ONLY",
        "real_task_writes_disabled": True,
        "action_allowed": False,
        "backend_callback": None,
        "read_only_actions": [
            "Preview Active Gate Schema",
            "Inspect Token Rules",
            "Inspect Future Handoff Shape",
        ],
        "no_execution_notice": "Human approval does not execute solver. No Abaqus solver command is executed.",
        "no_solver_request_notice": "No solver request file is created in Stage 5.2D.",
        "fixture_no_execution_notice": "Fixture writer does not execute solver and does not create solver request files.",
        "no_final_evidence_notice": "Fixture active gate records are not final evidence approval.",
        "final_evidence_locked_notice": "Final evidence remains locked.",
        "required_copy": [
            "Active gate record design only",
            "Active Gate Writer [TEST FIXTURE ONLY]",
            "real task writes disabled",
            "No real project gate is written in Stage 5.2D",
            "Human approval does not execute solver",
            "Future solver execution must consume the active gate in a later explicit stage",
            "No Abaqus solver command is executed",
            "No solver request file is created",
            "Final evidence remains locked",
            "ODB and metrics remain disabled",
            "Queue mutation remains disabled",
        ],
    }
