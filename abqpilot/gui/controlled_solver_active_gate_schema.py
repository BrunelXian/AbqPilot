from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from abqpilot.gui.controlled_solver_candidate_hash import compute_candidate_artifact_hash


STAGE5_2D_VERDICT = "PASS_ABQPILOT_V2_STAGE5_2D_CONTROLLED_SOLVER_ACTIVE_HUMAN_GATE_RECORD_DESIGN_READY"


def build_controlled_solver_active_gate_schema(
    task_id: str = "UNSELECTED_TASK",
    task_dir: str | Path | None = None,
    candidate_artifact_path: str | Path | None = None,
) -> dict[str, Any]:
    task_path = Path(task_dir) if task_dir else None
    candidate_hash = compute_candidate_artifact_hash(candidate_artifact_path)
    candidate_path = str(candidate_artifact_path) if candidate_artifact_path else None
    return {
        "schema_version": "0.1",
        "doc_type": "gate_decision",
        "gate_type": "CONTROLLED_SOLVER_RUN",
        "stage_id": "FUTURE_CONTROLLED_SOLVER_HUMAN_APPROVAL_STAGE",
        "design_stage_id": "STAGE5_2D",
        "active_gate_record_schema": True,
        "active_record_created_in_stage_5_2d": False,
        "real_project_gate_written": False,
        "decision": "APPROVED_BY_HUMAN",
        "approval_status": "APPROVED_BY_HUMAN",
        "execution_status": "NOT_EXECUTED",
        "solver_approved": True,
        "solver_execution_allowed": False,
        "solver_request_created": False,
        "solver_run": False,
        "queue_runner_launched": False,
        "odb_opened": False,
        "odb_metrics_approved": False,
        "final_evidence_approved": False,
        "final_verdict_frozen": False,
        "task_final_evidence_ledger_updated": False,
        "human_approval_required": True,
        "human_approval_token_valid": True,
        "human_approval_token_consumed": True,
        "one_time_use_token": True,
        "token_reuse_allowed": False,
        "task_id": task_id,
        "task_dir": str(task_path) if task_path else None,
        "candidate_artifact_path": candidate_path,
        "candidate_artifact_hash": candidate_hash.get("hash"),
        "candidate_artifact_hash_algorithm": "SHA256",
        "candidate_artifact_hash_binding": candidate_hash,
        "approval_timestamp": "FUTURE_APPROVAL_TIMESTAMP",
        "approver_type": "HUMAN",
        "approval_phrase_verified": True,
        "acknowledgement_flags_verified": True,
        "solver_command_label": "configured-controlled-abaqus-command",
        "allowed_output_dir": str((task_path or Path(".")) / "future_controlled_solver_run"),
        "downstream_execution_stage_required": True,
        "downstream_execution_handoff_allowed": True,
        "downstream_execution_auto_start": False,
        "odb_open_allowed": False,
        "metrics_extraction_allowed": False,
        "final_evidence_approval_allowed": False,
        "safety_boundary": (
            "Stage 5.2D defines active controlled solver human gate record design only. "
            "No real project gate is written, no solver request file is created, no Abaqus solver command is executed, "
            "and final evidence remains locked."
        ),
        "approval_scope": "Human approval would allow a later explicit execution stage to consume this gate; it does not execute solver.",
        "expiry_policy": "Future active gates should expire according to the bound approval token policy.",
        "audit_notes": [
            "Human approval and solver execution remain separate.",
            "ODB opening, metrics acceptance, final evidence approval, and final verdict freeze remain separately gated.",
            "Stage 5.2D does not write active gates under real task directories.",
        ],
        "writer_enabled": False,
    }


def build_future_execution_handoff_shape(
    gate: dict[str, Any] | None = None,
    candidate_artifact_path: str | Path | None = None,
) -> dict[str, Any]:
    gate = gate or build_controlled_solver_active_gate_schema(candidate_artifact_path=candidate_artifact_path)
    return {
        "doc_type": "handoff",
        "handoff_type": "CONTROLLED_SOLVER_APPROVAL_TO_EXECUTION",
        "design_stage_id": "STAGE5_2D",
        "expected_future_execution_handoff_shape": True,
        "active_execution_handoff_written_in_stage_5_2d": False,
        "from_agent": "PipelineSupervisor",
        "to_agent": "ExecutionAgent",
        "source_gate_type": "CONTROLLED_SOLVER_RUN",
        "source_gate_decision": "APPROVED_BY_HUMAN",
        "solver_execution_stage_required": True,
        "solver_auto_start": False,
        "candidate_artifact_path": gate.get("candidate_artifact_path"),
        "candidate_artifact_hash": gate.get("candidate_artifact_hash"),
        "solver_command_label": gate.get("solver_command_label"),
        "allowed_output_dir": gate.get("allowed_output_dir"),
        "no_odb_open": True,
        "no_metrics_approval": True,
        "no_final_evidence_approval": True,
        "queue_runner_launched": False,
    }


def write_controlled_solver_active_gate_design(
    project_root: str | Path,
    task_id: str = "UNSELECTED_TASK",
    task_dir: str | Path | None = None,
    candidate_artifact_path: str | Path | None = None,
    output_dir: str | Path | None = None,
) -> dict[str, Any]:
    root = Path(project_root)
    out = Path(output_dir) if output_dir else root / "gui_high_risk_gate_ux" / "controlled_solver_active_gate_design"
    out.mkdir(parents=True, exist_ok=True)
    gate = build_controlled_solver_active_gate_schema(task_id, task_dir, candidate_artifact_path)
    gate["generated_at"] = datetime.now().isoformat(timespec="seconds")
    gate["verdict"] = STAGE5_2D_VERDICT

    from abqpilot.gui.controlled_solver_active_gate_report import (
        render_active_gate_design_report,
        render_active_gate_validation_rules,
        render_candidate_hash_binding,
        render_token_consumption_rules,
        render_writer_policy,
    )
    from abqpilot.gui.controlled_solver_active_gate_validator import validate_controlled_solver_active_gate_schema

    validation = validate_controlled_solver_active_gate_schema(gate)
    handoff = build_future_execution_handoff_shape(gate)
    paths = {
        "schema": out / "CONTROLLED_SOLVER_ACTIVE_GATE_SCHEMA.json",
        "report": out / "CONTROLLED_SOLVER_ACTIVE_GATE_SCHEMA_REPORT.md",
        "validation_rules": out / "CONTROLLED_SOLVER_ACTIVE_GATE_VALIDATION_RULES.md",
        "token_rules": out / "CONTROLLED_SOLVER_TOKEN_CONSUMPTION_RULES.md",
        "candidate_hash": out / "CONTROLLED_SOLVER_CANDIDATE_HASH_BINDING.md",
        "future_handoff": out / "CONTROLLED_SOLVER_FUTURE_EXECUTION_HANDOFF_SHAPE.json",
        "writer_policy": out / "CONTROLLED_SOLVER_ACTIVE_GATE_WRITER_POLICY.md",
    }
    paths["schema"].write_text(json.dumps(gate, indent=2, ensure_ascii=False), encoding="utf-8")
    paths["report"].write_text(render_active_gate_design_report(gate, validation, handoff), encoding="utf-8")
    paths["validation_rules"].write_text(render_active_gate_validation_rules(), encoding="utf-8")
    paths["token_rules"].write_text(render_token_consumption_rules(), encoding="utf-8")
    paths["candidate_hash"].write_text(render_candidate_hash_binding(), encoding="utf-8")
    paths["future_handoff"].write_text(json.dumps(handoff, indent=2, ensure_ascii=False), encoding="utf-8")
    paths["writer_policy"].write_text(render_writer_policy(), encoding="utf-8")
    return {
        "command": "report-controlled-solver-active-gate-design",
        "verdict": "CONTROLLED_SOLVER_ACTIVE_GATE_DESIGN_REPORT_READY",
        "success": True,
        "output_paths": {key: str(path) for key, path in paths.items()},
        "details": gate,
        "validation": validation,
        "future_execution_handoff_shape": handoff,
        "warnings": [],
        "errors": [],
    }
