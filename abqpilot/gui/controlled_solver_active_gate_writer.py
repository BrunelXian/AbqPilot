from __future__ import annotations

from pathlib import Path
from typing import Any

from abqpilot.gui.controlled_solver_active_gate_fixture_writer import write_controlled_solver_active_gate_fixture


def write_controlled_solver_active_gate_record_disabled(
    task_dir: str | Path | None = None,
    gate_record: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "schema_version": "0.1",
        "stage": "Stage 5.2D",
        "writer_status": "ACTIVE_GATE_WRITER_DISABLED_IN_STAGE_5_2D",
        "writer_enabled": False,
        "task_dir": str(Path(task_dir)) if task_dir else None,
        "gate_record_supplied": gate_record is not None,
        "real_project_gate_written": False,
        "active_task_gate_record_written": False,
        "active_execution_handoff_written": False,
        "solver_request_created": False,
        "solver_run": False,
        "queue_runner_launched": False,
        "odb_opened": False,
        "final_evidence_approved": False,
        "final_verdict_frozen": False,
        "task_final_evidence_ledger_updated": False,
        "errors": ["Active gate writing is disabled in Stage 5.2D."],
        "warnings": ["Future explicit stage must enable and revalidate active human gate writing."],
    }


def write_controlled_solver_active_gate_record_fixture_only(
    target_dir: str | Path,
    *,
    fixture_mode: bool,
    task_id: str = "fixture_task",
    task_dir: str | Path | None = None,
    candidate_artifact_path: str | Path | None = None,
    gate_record: dict[str, Any] | None = None,
    request_solver_request: bool = False,
    request_execution_handoff: bool = False,
    request_final_evidence: bool = False,
) -> dict[str, Any]:
    return write_controlled_solver_active_gate_fixture(
        target_dir,
        fixture_mode=fixture_mode,
        task_id=task_id,
        task_dir=task_dir,
        candidate_artifact_path=candidate_artifact_path,
        gate_record=gate_record,
        request_solver_request=request_solver_request,
        request_execution_handoff=request_execution_handoff,
        request_final_evidence=request_final_evidence,
    )
