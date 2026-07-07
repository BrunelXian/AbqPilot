from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from abqpilot.gui.controlled_solver_active_gate_schema import build_controlled_solver_active_gate_schema
from abqpilot.gui.controlled_solver_active_gate_validator import validate_controlled_solver_active_gate_schema
from abqpilot.gui.controlled_solver_active_gate_writer_policy import evaluate_active_gate_writer_target


BLOCKING_FLAG_STATUS = {
    "solver_request_created": "ACTIVE_GATE_WRITER_BLOCKED_SOLVER_REQUEST",
    "solver_execution_allowed": "ACTIVE_GATE_WRITER_BLOCKED_EXECUTION_HANDOFF",
    "downstream_execution_auto_start": "ACTIVE_GATE_WRITER_BLOCKED_EXECUTION_HANDOFF",
    "final_evidence_approved": "ACTIVE_GATE_WRITER_BLOCKED_FINAL_EVIDENCE",
    "final_verdict_frozen": "ACTIVE_GATE_WRITER_BLOCKED_FINAL_EVIDENCE",
    "task_final_evidence_ledger_updated": "ACTIVE_GATE_WRITER_BLOCKED_FINAL_EVIDENCE",
}


def write_controlled_solver_active_gate_fixture(
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
    policy = evaluate_active_gate_writer_target(target_dir, fixture_mode=fixture_mode)
    if policy["policy_status"] != "ACTIVE_GATE_WRITER_TARGET_ALLOWED":
        return _blocked(policy["policy_status"], policy=policy)
    if request_solver_request:
        return _blocked("ACTIVE_GATE_WRITER_BLOCKED_SOLVER_REQUEST", policy=policy)
    if request_execution_handoff:
        return _blocked("ACTIVE_GATE_WRITER_BLOCKED_EXECUTION_HANDOFF", policy=policy)
    if request_final_evidence:
        return _blocked("ACTIVE_GATE_WRITER_BLOCKED_FINAL_EVIDENCE", policy=policy)

    record = dict(gate_record or build_controlled_solver_active_gate_schema(task_id, task_dir or target_dir, candidate_artifact_path))
    for flag, status in BLOCKING_FLAG_STATUS.items():
        if record.get(flag) is True:
            return _blocked(status, policy=policy)
    record.update(
        {
            "stage": "Stage 5.2E",
            "design_stage_id": "STAGE5_2E",
            "fixture_only": True,
            "real_project_gate_written": False,
            "active_record_created_in_stage_5_2e": True,
            "active_record_created_under_fixture": True,
            "real_task_gate_path": False,
            "execution_status": "NOT_EXECUTED",
            "solver_execution_allowed": False,
            "solver_request_created": False,
            "solver_run": False,
            "queue_runner_launched": False,
            "odb_opened": False,
            "odb_metrics_approved": False,
            "final_evidence_approved": False,
            "final_verdict_frozen": False,
            "task_final_evidence_ledger_updated": False,
            "downstream_execution_stage_required": True,
            "downstream_execution_auto_start": False,
            "no_solver_execution_notice": "Fixture active gate record only; no solver execution is enabled.",
            "no_final_evidence_notice": "Fixture active gate record is not final evidence approval.",
        }
    )
    validation = validate_controlled_solver_active_gate_schema(record)
    if not str(validation["validation_status"]).startswith("ACTIVE_SOLVER_GATE_SCHEMA_VALID"):
        return _blocked(validation["validation_status"], policy=policy, validation=validation)

    target = Path(policy["target_dir"])
    gate_dir = target / "gates"
    gate_dir.mkdir(parents=True, exist_ok=True)
    gate_path = gate_dir / "GATE_FIXTURE_CONTROLLED_SOLVER_ACTIVE.json"
    record["written_at"] = datetime.now().isoformat(timespec="seconds")
    gate_path.write_text(json.dumps(record, indent=2, ensure_ascii=False), encoding="utf-8")
    return {
        "schema_version": "0.1",
        "stage": "Stage 5.2E",
        "writer_status": "ACTIVE_GATE_WRITER_FIXTURE_WRITE_OK",
        "success": True,
        "fixture_mode": True,
        "fixture_only": True,
        "fixture_write_supported": True,
        "real_task_write_enabled": False,
        "real_project_gate_written": False,
        "active_task_gate_record_written": False,
        "active_execution_handoff_written": False,
        "solver_request_created": False,
        "solver_run": False,
        "queue_runner_launched": False,
        "odb_opened": False,
        "odb_metrics_approved": False,
        "final_evidence_approved": False,
        "final_verdict_frozen": False,
        "task_final_evidence_ledger_updated": False,
        "output_paths": {"fixture_gate_record": str(gate_path)},
        "record": record,
        "validation": validation,
        "policy": policy,
        "warnings": ["Fixture active gate record is not a real solver approval."],
        "errors": [],
    }


def _blocked(status: str, **extra: Any) -> dict[str, Any]:
    payload = {
        "schema_version": "0.1",
        "stage": "Stage 5.2E",
        "writer_status": status,
        "success": False,
        "fixture_write_supported": True,
        "real_task_write_enabled": False,
        "real_project_gate_written": False,
        "active_task_gate_record_written": False,
        "active_execution_handoff_written": False,
        "solver_request_created": False,
        "solver_run": False,
        "queue_runner_launched": False,
        "odb_opened": False,
        "odb_metrics_approved": False,
        "final_evidence_approved": False,
        "final_verdict_frozen": False,
        "task_final_evidence_ledger_updated": False,
        "warnings": [],
        "errors": [status],
    }
    payload.update(extra)
    return payload
