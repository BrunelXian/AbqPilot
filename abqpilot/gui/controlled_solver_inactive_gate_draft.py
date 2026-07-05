from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from abqpilot.gui.controlled_solver_future_gate_shape import build_expected_future_active_gate_shape
from abqpilot.gui.controlled_solver_future_handoff_shape import build_expected_future_solver_execution_handoff_shape
from abqpilot.gui.controlled_solver_gate_preview import build_controlled_solver_gate_preview
from abqpilot.gui.human_approval_token import sha256_file


STAGE5_2C_VERDICT = "PASS_ABQPILOT_V2_STAGE5_2C_CONTROLLED_SOLVER_INACTIVE_HUMAN_GATE_DRAFT_READY"


def build_controlled_solver_inactive_gate_draft(
    task_dir: str | Path | None = None,
    candidate_inp: str | Path | None = None,
) -> dict[str, Any]:
    preview = build_controlled_solver_gate_preview(task_dir=task_dir, candidate_inp=candidate_inp)
    task = Path(task_dir) if task_dir else None
    task_id = task.name if task else "UNSELECTED_TASK"
    candidate_path = _candidate_path(preview, candidate_inp)
    token = dict(preview["approval_token_preview"])
    token["preview_only_in_stage_5_2c"] = True
    return {
        "schema_version": "0.1",
        "stage": "Stage 5.2C",
        "stage_id": "STAGE5_2C",
        "draft_type": "CONTROLLED_SOLVER_RUN_HUMAN_GATE_DRAFT",
        "gate_type": "CONTROLLED_SOLVER_RUN",
        "preview_only": True,
        "inactive_draft": True,
        "draft_status": _draft_status(preview),
        "approval_status": "NOT_APPROVED",
        "gate_decision": "PREVIEW_ONLY_NOT_APPROVED",
        "execution_status": "NOT_EXECUTABLE",
        "future_stage_required": True,
        "human_gate_required": True,
        "real_gate_created": False,
        "active_gate_record_created": False,
        "task_gate_record_created": False,
        "solver_approved": False,
        "solver_run": False,
        "solver_request_created": False,
        "queue_runner_launched": False,
        "odb_opened": False,
        "odb_metrics_approved": False,
        "final_evidence_approved": False,
        "final_verdict_frozen": False,
        "task_final_evidence_ledger_updated": False,
        "task_dir": str(task) if task else None,
        "task_id": task_id,
        "candidate_artifact_path": str(candidate_path) if candidate_path else None,
        "candidate_artifact_hash": sha256_file(candidate_path) if candidate_path else None,
        "readiness_status": preview["readiness_status"],
        "readiness_checklist": preview["prerequisite_checklist"],
        "missing_prerequisites": preview["missing_prerequisites"],
        "warning_items": preview["warning_items"],
        "blocked_items": preview["blocked_items"],
        "human_approval_token_preview": token,
        "token_validation_preview": preview["approval_token_validation_preview"],
        "expected_future_active_gate_shape": build_expected_future_active_gate_shape(task_id),
        "expected_future_solver_execution_handoff_shape": build_expected_future_solver_execution_handoff_shape(
            task_id,
            str(candidate_path) if candidate_path else None,
        ),
        "safety_boundary": (
            "Stage 5.2C creates an inactive controlled solver human gate draft only. It does not approve solver, "
            "run Abaqus, create solver request files, write active task gates, open ODB, approve metrics, update "
            "final evidence, or freeze verdict."
        ),
        "no_execution_notice": "No Abaqus solver command is executed. No solver request file is created.",
        "no_approval_notice": "Inactive draft only; not an approval. No active gate record is created in Stage 5.2C.",
        "next_future_stage_recommendation": "A future explicit stage must create an active human approval gate before any later solver execution stage.",
        "required_copy": [
            "Inactive draft only; not an approval",
            "No active gate record is created in Stage 5.2C",
            "No Abaqus solver command is executed",
            "No solver request file is created",
            "Final evidence remains locked",
            "A future explicit stage is required to create an active human approval gate",
        ],
        "active_approval": False,
        "active_solver_request_path": None,
        "active_task_gate_output_path": None,
        "queue_mutation_output_path": None,
        "odb_metrics_output_path": None,
    }


def write_controlled_solver_inactive_gate_draft(
    project_root: str | Path,
    task_dir: str | Path | None = None,
    candidate_inp: str | Path | None = None,
    output_dir: str | Path | None = None,
) -> dict[str, Any]:
    root = Path(project_root)
    out = Path(output_dir) if output_dir else root / "gui_high_risk_gate_ux" / "controlled_solver_inactive_gate_draft"
    out.mkdir(parents=True, exist_ok=True)
    draft = build_controlled_solver_inactive_gate_draft(task_dir=task_dir, candidate_inp=candidate_inp)
    draft["generated_at"] = datetime.now().isoformat(timespec="seconds")
    draft["verdict"] = STAGE5_2C_VERDICT

    from abqpilot.gui.controlled_solver_inactive_gate_report import render_controlled_solver_inactive_gate_report
    from abqpilot.gui.controlled_solver_inactive_gate_validator import validate_controlled_solver_inactive_gate_draft

    validation = validate_controlled_solver_inactive_gate_draft(draft)
    draft_path = out / "CONTROLLED_SOLVER_INACTIVE_GATE_DRAFT.json"
    report_path = out / "CONTROLLED_SOLVER_INACTIVE_GATE_DRAFT_REPORT.md"
    validation_path = out / "CONTROLLED_SOLVER_INACTIVE_GATE_DRAFT_VALIDATION.json"
    future_gate_path = out / "CONTROLLED_SOLVER_FUTURE_ACTIVE_GATE_SHAPE.json"
    future_handoff_path = out / "CONTROLLED_SOLVER_FUTURE_EXECUTION_HANDOFF_SHAPE.json"

    draft_path.write_text(json.dumps(draft, indent=2, ensure_ascii=False), encoding="utf-8")
    report_path.write_text(render_controlled_solver_inactive_gate_report(draft, validation), encoding="utf-8")
    validation_path.write_text(json.dumps(validation, indent=2, ensure_ascii=False), encoding="utf-8")
    future_gate_path.write_text(json.dumps(draft["expected_future_active_gate_shape"], indent=2, ensure_ascii=False), encoding="utf-8")
    future_handoff_path.write_text(json.dumps(draft["expected_future_solver_execution_handoff_shape"], indent=2, ensure_ascii=False), encoding="utf-8")
    return {
        "command": "report-controlled-solver-inactive-gate-draft",
        "verdict": "CONTROLLED_SOLVER_INACTIVE_GATE_DRAFT_REPORT_READY",
        "success": True,
        "output_paths": {
            "inactive_gate_draft": str(draft_path),
            "inactive_gate_report": str(report_path),
            "inactive_gate_validation": str(validation_path),
            "future_active_gate_shape": str(future_gate_path),
            "future_execution_handoff_shape": str(future_handoff_path),
        },
        "details": draft,
        "validation": validation,
        "warnings": [],
        "errors": [],
    }


def _candidate_path(preview: dict[str, Any], candidate_inp: str | Path | None) -> Path | None:
    if candidate_inp:
        return Path(candidate_inp)
    paths = preview.get("candidate_artifact_paths") or []
    return Path(paths[0]) if paths else None


def _draft_status(preview: dict[str, Any]) -> str:
    readiness = str(preview.get("readiness_status"))
    if readiness == "SOLVER_GATE_PREVIEW_BLOCKED_EXECUTION_REQUEST_PRESENT":
        return "CONTROLLED_SOLVER_GATE_DRAFT_BLOCKED_EXECUTION_REQUEST_PRESENT"
    if readiness == "SOLVER_GATE_PREVIEW_BLOCKED_SOURCE_MUTATION_RISK":
        return "CONTROLLED_SOLVER_GATE_DRAFT_BLOCKED_SOURCE_MUTATION_RISK"
    if "no_final_evidence_update_requested" in preview.get("missing_prerequisites", []):
        return "CONTROLLED_SOLVER_GATE_DRAFT_BLOCKED_FINAL_EVIDENCE_REQUEST"
    if readiness == "SOLVER_GATE_PREVIEW_READY":
        return "CONTROLLED_SOLVER_GATE_DRAFT_READY"
    if readiness == "SOLVER_GATE_PREVIEW_READY_WITH_MISSING_PREREQUISITES":
        return "CONTROLLED_SOLVER_GATE_DRAFT_READY_WITH_MISSING_PREREQUISITES"
    return "CONTROLLED_SOLVER_GATE_DRAFT_REVIEW_REQUIRED"
