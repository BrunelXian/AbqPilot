from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from abqpilot.gui.controlled_solver_readiness import build_solver_readiness_checklist
from abqpilot.gui.human_approval_token import build_controlled_solver_approval_token_schema
from abqpilot.gui.human_approval_token_validator import validate_controlled_solver_preview_token


STAGE5_2B_VERDICT = "PASS_ABQPILOT_V2_STAGE5_2B_CONTROLLED_SOLVER_HUMAN_GATE_PREVIEW_READY"


def build_controlled_solver_gate_preview(
    task_dir: str | Path | None = None,
    candidate_inp: str | Path | None = None,
) -> dict[str, Any]:
    task = Path(task_dir) if task_dir else None
    task_id = task.name if task else "UNSELECTED_TASK"
    readiness = build_solver_readiness_checklist(task, candidate_inp)
    candidate = readiness.get("candidate_inp")
    token = build_controlled_solver_approval_token_schema(task_id, task or Path("."), candidate)
    token_validation = validate_controlled_solver_preview_token(token, task_id, task or Path("."), candidate)
    missing = list(readiness["missing_prerequisites"])
    blocked = list(readiness["blocked_items"])
    return {
        "schema_version": "0.1",
        "stage": "Stage 5.2B",
        "stage_id": "STAGE5_2B",
        "gate_type": "CONTROLLED_SOLVER_RUN",
        "preview_only": True,
        "approval_status": "NOT_APPROVED",
        "execution_status": "NOT_EXECUTABLE",
        "future_stage_required": True,
        "human_gate_required": True,
        "real_gate_created": False,
        "solver_approved": False,
        "solver_run": False,
        "solver_request_created": False,
        "queue_runner_launched": False,
        "odb_opened": False,
        "final_evidence_approved": False,
        "final_verdict_frozen": False,
        "task_final_evidence_ledger_updated": False,
        "task_dir": str(task) if task else None,
        "candidate_artifact_paths": [candidate] if candidate else [],
        "prerequisite_checklist": readiness["checklist"],
        "missing_prerequisites": missing,
        "readiness_status": readiness["readiness_status"],
        "warning_items": _warnings(readiness),
        "blocked_items": blocked,
        "required_human_confirmation_text": "Preview only; not a solver approval. Future controlled solver approval must use an explicit human gate.",
        "approval_token_preview": token,
        "token_validation_rules": _token_validation_rules(),
        "approval_token_validation_preview": token_validation,
        "expected_future_gate_record_shape": _future_gate_shape(task_id),
        "expected_future_solver_request_shape": _future_solver_request_shape(task_id),
        "safety_boundary": (
            "Stage 5.2B designs controlled solver gate preview and approval token schema only. "
            "It does not approve solver, run solver, create solver request files, open ODB, extract metrics, "
            "mutate queue/runtime files, update final evidence, or freeze verdict."
        ),
        "no_execution_notice": "No Abaqus solver command is executed. No solver request file is created.",
        "required_copy": [
            "Preview only; not a solver approval",
            "Human approval token is designed but not accepted as active approval in Stage 5.2B",
            "No Abaqus solver command is executed",
            "No solver request file is created",
            "Final evidence remains locked",
        ],
        "approval_execution_separation": {
            "stage_5_2b": "preview token + preview gate only",
            "future_stage_5_2c_or_later": "real human approval gate record may be created, still no solver execution",
            "future_stage_5_2d_or_later": "controlled solver execution may consume approved gate, still no ODB/metrics approval",
            "queue_execution": "separately gated",
            "odb_metrics": "separately gated after solver completion",
        },
    }


def write_controlled_solver_gate_preview(
    project_root: str | Path,
    task_dir: str | Path | None = None,
    candidate_inp: str | Path | None = None,
    output_dir: str | Path | None = None,
) -> dict[str, Any]:
    root = Path(project_root)
    out = Path(output_dir) if output_dir else root / "gui_high_risk_gate_ux" / "controlled_solver_gate_preview"
    out.mkdir(parents=True, exist_ok=True)
    preview = build_controlled_solver_gate_preview(task_dir=task_dir, candidate_inp=candidate_inp)
    preview["generated_at"] = datetime.now().isoformat(timespec="seconds")
    preview["verdict"] = STAGE5_2B_VERDICT

    from abqpilot.gui.controlled_solver_gate_report import (
        render_controlled_solver_approval_token_rules,
        render_controlled_solver_gate_preview_report,
        render_controlled_solver_readiness_checklist,
    )

    preview_path = out / "CONTROLLED_SOLVER_GATE_PREVIEW.json"
    report_path = out / "CONTROLLED_SOLVER_GATE_PREVIEW_REPORT.md"
    checklist_path = out / "CONTROLLED_SOLVER_READINESS_CHECKLIST.md"
    token_schema_path = out / "CONTROLLED_SOLVER_APPROVAL_TOKEN_SCHEMA.json"
    token_rules_path = out / "CONTROLLED_SOLVER_APPROVAL_TOKEN_RULES.md"

    preview_path.write_text(json.dumps(preview, indent=2, ensure_ascii=False), encoding="utf-8")
    report_path.write_text(render_controlled_solver_gate_preview_report(preview), encoding="utf-8")
    checklist_path.write_text(render_controlled_solver_readiness_checklist(preview["prerequisite_checklist"]), encoding="utf-8")
    token_schema_path.write_text(json.dumps(preview["approval_token_preview"], indent=2, ensure_ascii=False), encoding="utf-8")
    token_rules_path.write_text(render_controlled_solver_approval_token_rules(preview["token_validation_rules"]), encoding="utf-8")
    return {
        "command": "report-controlled-solver-gate-preview",
        "verdict": "CONTROLLED_SOLVER_GATE_PREVIEW_REPORT_READY",
        "success": True,
        "output_paths": {
            "preview_json": str(preview_path),
            "preview_report": str(report_path),
            "readiness_checklist": str(checklist_path),
            "approval_token_schema": str(token_schema_path),
            "approval_token_rules": str(token_rules_path),
        },
        "details": preview,
        "warnings": [],
        "errors": [],
    }


def _warnings(readiness: dict[str, Any]) -> list[str]:
    if readiness["readiness_status"] == "SOLVER_GATE_PREVIEW_READY":
        return ["Readiness preview appears complete, but Stage 5.2B still cannot approve or execute solver."]
    return ["Missing or blocked prerequisites are advisory in Stage 5.2B; no solver action is enabled."]


def _token_validation_rules() -> list[str]:
    return [
        "token_type must be CONTROLLED_SOLVER_RUN_APPROVAL",
        "token_version must be supported",
        "task_id and task_dir must match",
        "candidate_artifact_hash must match the candidate artifact if it exists",
        "approval phrase must exactly match the required phrase",
        "all acknowledgement flags must be true",
        "token must not be expired if expires_at_optional is present",
        "one_time_use must be true",
        "preview_only_in_stage_5_2b must be true",
        "active_approval must be false in Stage 5.2B",
    ]


def _future_gate_shape(task_id: str) -> dict[str, Any]:
    return {
        "doc_type": "gate_decision",
        "task_id": task_id,
        "transition": "CONTROLLED_SOLVER_GATE_PREVIEW_TO_FUTURE_HUMAN_APPROVAL",
        "decision": "FUTURE_STAGE_REQUIRED",
        "approver_type": "HUMAN",
        "stage_5_2b_real_gate_created": False,
    }


def _future_solver_request_shape(task_id: str) -> dict[str, Any]:
    return {
        "task_id": task_id,
        "request_type": "CONTROLLED_SOLVER_RUN",
        "stage_5_2b_solver_request_created": False,
        "requires_future_approved_gate": True,
        "queue_runner_allowed": False,
        "odb_metrics_allowed": False,
    }
