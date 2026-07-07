from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from abqpilot.gui.controlled_solver_candidate_hash import compute_candidate_artifact_hash
from abqpilot.gui.controlled_solver_dry_run_request_audit import audit_controlled_solver_dry_run_request_no_execution
from abqpilot.gui.controlled_solver_dry_run_request_report import render_dry_run_request_audit, render_dry_run_request_report
from abqpilot.gui.controlled_solver_dry_run_request_validator import (
    HASH_MISMATCH,
    HANDOFF_INVALID,
    MISSING_SOURCE,
    PREFLIGHT_INVALID,
    PREFLIGHT_NOT_PASS,
    READY,
    REQUEST_DRAFT_INVALID,
    SOURCE_GATE_INVALID,
    validate_controlled_solver_dry_run_request,
)
from abqpilot.gui.controlled_solver_execution_handoff_validator import READY as HANDOFF_READY
from abqpilot.gui.controlled_solver_execution_handoff_validator import validate_controlled_solver_execution_handoff_draft
from abqpilot.gui.controlled_solver_real_gate_creation import SMOKE_TASK_ID
from abqpilot.gui.controlled_solver_real_gate_validator import validate_controlled_solver_real_gate_smoke
from abqpilot.gui.controlled_solver_request_preflight_validator import PASS as PREFLIGHT_PASS
from abqpilot.gui.controlled_solver_request_preflight_validator import validate_controlled_solver_request_preflight_result
from abqpilot.gui.controlled_solver_request_validator import READY as REQUEST_READY
from abqpilot.gui.controlled_solver_request_validator import validate_controlled_solver_request_draft


STAGE5_2J_VERDICT = "PASS_ABQPILOT_V2_STAGE5_2J_CONTROLLED_SOLVER_EXECUTION_DRY_RUN_REQUEST_MATERIALIZATION_READY"
COMMAND_VERDICT = "CONTROLLED_SOLVER_DRY_RUN_REQUEST_MATERIALIZED_NO_EXECUTION"


def create_controlled_solver_dry_run_request_no_exec(project_root: str | Path) -> dict[str, Any]:
    root = Path(project_root)
    task_dir = root / "runs" / "tasks" / SMOKE_TASK_ID
    sources = _source_paths(task_dir)
    missing = [str(path) for path in sources.values() if not path.exists()]
    if missing:
        return _blocked(MISSING_SOURCE, task_dir, {"missing": missing})

    gate = _read_json(sources["gate_json"])
    token = _read_json(sources["token"])
    handoff = _read_json(sources["handoff_draft"])
    request_draft = _read_json(sources["request_draft"])
    request_validation = _read_json(sources["request_validation"])
    preflight = _read_json(sources["preflight_result"])
    preflight_validation = _read_json(sources["preflight_validation"])

    gate_validation = validate_controlled_solver_real_gate_smoke(task_dir, gate, token)
    if gate_validation.get("validation_status") != "CONTROLLED_SOLVER_REAL_GATE_VALID_NO_EXECUTION":
        return _blocked(SOURCE_GATE_INVALID, task_dir, {"source_gate_validation": gate_validation})

    handoff_validation = validate_controlled_solver_execution_handoff_draft(handoff)
    if handoff_validation.get("validation_status") != HANDOFF_READY:
        return _blocked(HANDOFF_INVALID, task_dir, {"handoff_validation": handoff_validation})

    draft_validation = validate_controlled_solver_request_draft(request_draft)
    if draft_validation.get("validation_status") != REQUEST_READY or request_validation.get("validation_status") != REQUEST_READY:
        return _blocked(REQUEST_DRAFT_INVALID, task_dir, {"request_validation": draft_validation, "source_validation": request_validation})

    preflight_check = validate_controlled_solver_request_preflight_result(preflight)
    if preflight_check.get("validation_status") != PREFLIGHT_PASS or preflight_validation.get("validation_status") != PREFLIGHT_PASS:
        return _blocked(PREFLIGHT_INVALID, task_dir, {"preflight_validation": preflight_check, "source_validation": preflight_validation})
    if preflight.get("preflight_status") != PREFLIGHT_PASS or preflight.get("preflight_passed") is not True:
        return _blocked(PREFLIGHT_NOT_PASS, task_dir, {"preflight_status": preflight.get("preflight_status")})

    candidate = sources["candidate"]
    hash_meta = compute_candidate_artifact_hash(candidate)
    candidate_hash = hash_meta.get("hash")
    expected_hashes = [
        gate.get("candidate_artifact_hash"),
        handoff.get("candidate_artifact_hash"),
        request_draft.get("candidate_artifact_hash"),
        preflight.get("candidate_artifact_hash"),
    ]
    if not candidate_hash or any(candidate_hash != expected for expected in expected_hashes):
        return _blocked(HASH_MISMATCH, task_dir, {"hash_metadata": hash_meta, "expected_hashes": expected_hashes})

    dry_run_request = build_controlled_solver_dry_run_request(
        task_dir=task_dir,
        gate=gate,
        handoff=handoff,
        request_draft=request_draft,
        preflight=preflight,
        candidate=candidate,
        candidate_hash=candidate_hash,
    )
    validation = validate_controlled_solver_dry_run_request(dry_run_request)
    audit = audit_controlled_solver_dry_run_request_no_execution(task_dir, dry_run_request)
    if validation.get("validation_status") != READY:
        return _blocked(validation.get("validation_status", "CONTROLLED_SOLVER_DRY_RUN_REQUEST_REVIEW_REQUIRED"), task_dir, {"validation": validation})

    task_out = task_dir / "artifacts" / "dry_run_requests"
    project_out = root / "gui_high_risk_gate_ux" / "controlled_solver_dry_run_request_materialization"
    task_out.mkdir(parents=True, exist_ok=True)
    project_out.mkdir(parents=True, exist_ok=True)

    task_request = task_out / "CONTROLLED_SOLVER_DRY_RUN_REQUEST.json"
    task_request_md = task_out / "CONTROLLED_SOLVER_DRY_RUN_REQUEST.md"
    task_validation = task_out / "CONTROLLED_SOLVER_DRY_RUN_REQUEST_VALIDATION.json"
    task_audit = task_out / "CONTROLLED_SOLVER_DRY_RUN_REQUEST_NO_EXECUTION_AUDIT.md"
    project_result = project_out / "CONTROLLED_SOLVER_DRY_RUN_REQUEST_RESULT.json"
    project_report = project_out / "CONTROLLED_SOLVER_DRY_RUN_REQUEST_REPORT.md"
    project_validation = project_out / "CONTROLLED_SOLVER_DRY_RUN_REQUEST_VALIDATION.json"
    project_audit = project_out / "CONTROLLED_SOLVER_DRY_RUN_REQUEST_NO_EXECUTION_AUDIT.md"
    project_audit_json = project_out / "CONTROLLED_SOLVER_DRY_RUN_REQUEST_NO_EXECUTION_AUDIT.json"
    result = {
        "schema_version": "0.1",
        "stage": "Stage 5.2J",
        "verdict": STAGE5_2J_VERDICT,
        "command_verdict": COMMAND_VERDICT,
        "materialization_status": READY,
        "success": True,
        "dry_run_request_materialized": True,
        "source_gate_validation_status": gate_validation.get("validation_status"),
        "source_handoff_validation_status": handoff_validation.get("validation_status"),
        "source_request_validation_status": draft_validation.get("validation_status"),
        "source_preflight_validation_status": preflight_check.get("validation_status"),
        "candidate_hash_verified": True,
        "dry_run_request": dry_run_request,
        "validation": validation,
        "no_execution_audit": audit,
        "dry_run_only": True,
        "active_request_created": False,
        "request_active": False,
        "executable_request": False,
        "solver_execution_allowed": False,
        "solver_request_created": False,
        "solver_run": False,
        "queue_runner_launched": False,
        "queue_entry_created": False,
        "output_dir_created": False,
        "odb_opened": False,
        "odb_metrics_approved": False,
        "final_evidence_approved": False,
        "final_verdict_frozen": False,
        "task_final_evidence_ledger_updated": False,
        "no_solver_request_files_found": audit["no_solver_request_files_found"],
        "no_active_handoff_files_found": audit["no_active_handoff_files_found"],
        "no_queue_files_found": audit["no_queue_files_found"],
        "no_odb_files_found": audit["no_odb_files_found"],
        "no_metrics_files_found": audit["no_metrics_files_found"],
        "no_output_execution_dir_found": audit["no_output_execution_dir_found"],
        "output_paths": {
            "task_request": str(task_request),
            "task_request_markdown": str(task_request_md),
            "task_validation": str(task_validation),
            "task_audit": str(task_audit),
            "project_result": str(project_result),
            "project_report": str(project_report),
            "project_validation": str(project_validation),
            "project_audit": str(project_audit),
            "project_audit_json": str(project_audit_json),
        },
    }
    report = render_dry_run_request_report(result)
    audit_md = render_dry_run_request_audit(audit)
    task_request.write_text(json.dumps(dry_run_request, indent=2, ensure_ascii=False), encoding="utf-8")
    task_request_md.write_text(report, encoding="utf-8")
    task_validation.write_text(json.dumps(validation, indent=2, ensure_ascii=False), encoding="utf-8")
    task_audit.write_text(audit_md, encoding="utf-8")
    project_result.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    project_report.write_text(report, encoding="utf-8")
    project_validation.write_text(json.dumps(validation, indent=2, ensure_ascii=False), encoding="utf-8")
    project_audit.write_text(audit_md, encoding="utf-8")
    project_audit_json.write_text(json.dumps(audit, indent=2, ensure_ascii=False), encoding="utf-8")
    return result


def build_controlled_solver_dry_run_request(
    task_dir: str | Path,
    gate: dict[str, Any],
    handoff: dict[str, Any],
    request_draft: dict[str, Any],
    preflight: dict[str, Any],
    candidate: str | Path,
    candidate_hash: str,
) -> dict[str, Any]:
    task = Path(task_dir)
    return {
        "schema_version": "0.1",
        "request_type": "CONTROLLED_SOLVER_DRY_RUN_REQUEST",
        "stage_id": "STAGE5_2J",
        "source_stage_id": "STAGE5_2I",
        "source_task_id": SMOKE_TASK_ID,
        "source_gate_id": gate.get("gate_id", "GATE_001"),
        "source_gate_validated": True,
        "source_handoff_draft_validated": handoff.get("draft_type") == "CONTROLLED_SOLVER_EXECUTION_HANDOFF_DRAFT",
        "source_request_draft_validated": request_draft.get("draft_type") == "CONTROLLED_SOLVER_REQUEST_DRAFT",
        "source_preflight_validated": preflight.get("result_type") == "CONTROLLED_SOLVER_REQUEST_PREFLIGHT",
        "source_preflight_status": preflight.get("preflight_status"),
        "candidate_artifact_path": str(candidate),
        "candidate_artifact_hash": candidate_hash,
        "candidate_artifact_hash_algorithm": "SHA256",
        "candidate_hash_verified": True,
        "target_agent": "ExecutionAgent",
        "target_future_stage": "FUTURE_CONTROLLED_SOLVER_EXECUTION_STAGE",
        "dry_run_only": True,
        "materialized_request_artifact": True,
        "materialized_request_filename": "CONTROLLED_SOLVER_DRY_RUN_REQUEST.json",
        "active_request_created": False,
        "request_active": False,
        "executable_request": False,
        "future_execution_stage_required": True,
        "solver_command_label": request_draft.get("solver_command_label"),
        "solver_command_label_validated": preflight.get("solver_command_label_validated") is True,
        "solver_command_path_included": False,
        "solver_command_not_invoked": True,
        "allowed_output_dir_preview": request_draft.get("allowed_output_dir_preview"),
        "output_dir_policy_validated": preflight.get("output_dir_policy_validated") is True,
        "output_dir_created": False,
        "cpu_count_preview": request_draft.get("cpu_count_preview", "FUTURE_STAGE_POLICY"),
        "cpu_policy_validated": preflight.get("cpu_policy_validated") is True,
        "memory_policy_preview": request_draft.get("memory_policy_preview", "FUTURE_STAGE_POLICY"),
        "memory_policy_validated": preflight.get("memory_policy_validated") is True,
        "timeout_policy_preview": request_draft.get("timeout_policy_preview", "FUTURE_STAGE_POLICY"),
        "timeout_policy_validated": preflight.get("timeout_policy_validated") is True,
        "log_capture_policy_preview": request_draft.get("log_capture_policy_preview", "FUTURE_STAGE_POLICY"),
        "log_capture_policy_validated": preflight.get("log_capture_policy_validated") is True,
        "solver_approved_by_source_gate": gate.get("solver_approved") is True,
        "solver_execution_allowed": False,
        "solver_request_created": False,
        "solver_run": False,
        "queue_runner_launched": False,
        "queue_entry_created": False,
        "odb_opened": False,
        "odb_metrics_approved": False,
        "final_evidence_approved": False,
        "final_verdict_frozen": False,
        "task_final_evidence_ledger_updated": False,
        "downstream_execution_auto_start": False,
        "no_solver_execution_notice": "Dry-run request artifact only; no Abaqus solver command is executed.",
        "no_solver_request_notice": "No active solver request is created and no solver_request.json is written.",
        "no_queue_notice": "No queue entry is created.",
        "no_odb_notice": "No ODB is opened or accepted.",
        "no_metrics_notice": "No metrics are extracted or approved.",
        "final_evidence_locked_notice": "Final evidence remains locked.",
        "expected_future_active_request_shape": request_draft.get("expected_future_solver_request_shape", {}),
        "forbidden_stage5_2j_outputs": [
            "solver_request.json",
            "job_request.json",
            "abaqus_job.json",
            ".bat or .cmd solver launcher",
            "active HANDOFF_*.md execution handoff",
            "queue files",
            "ODB files",
            "metrics files",
            "execution output directory",
            "TASK_FINAL_EVIDENCE_LEDGER.md",
        ],
        "safety_boundary": "This is not solver_request.json, an active job request, queue entry creation, Abaqus command, ODB acceptance, metrics approval, final evidence approval, or final verdict freeze.",
        "materialized_request_path": str(task / "artifacts" / "dry_run_requests" / "CONTROLLED_SOLVER_DRY_RUN_REQUEST.json"),
        "created_at": datetime.now().isoformat(timespec="seconds"),
    }


def _source_paths(task_dir: Path) -> dict[str, Path]:
    return {
        "gate_json": task_dir / "gates" / "GATE_001_CONTROLLED_SOLVER_HUMAN_APPROVAL.json",
        "candidate": task_dir / "artifacts" / "candidates" / "candidate_controlled_solver_smoke.inp",
        "token": task_dir / "artifacts" / "approvals" / "HUMAN_APPROVAL_TOKEN_PREVIEW.json",
        "handoff_draft": task_dir / "artifacts" / "handoff_drafts" / "CONTROLLED_SOLVER_EXECUTION_HANDOFF_DRAFT.json",
        "request_draft": task_dir / "artifacts" / "request_drafts" / "CONTROLLED_SOLVER_REQUEST_DRAFT_SCHEMA.json",
        "request_example": task_dir / "artifacts" / "request_drafts" / "CONTROLLED_SOLVER_REQUEST_DRAFT_EXAMPLE.json",
        "request_validation": task_dir / "artifacts" / "request_drafts" / "CONTROLLED_SOLVER_REQUEST_DRAFT_VALIDATION.json",
        "preflight_result": task_dir / "artifacts" / "request_preflight" / "CONTROLLED_SOLVER_REQUEST_PREFLIGHT_RESULT.json",
        "preflight_validation": task_dir / "artifacts" / "request_preflight" / "CONTROLLED_SOLVER_REQUEST_PREFLIGHT_VALIDATION.json",
    }


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _blocked(status: str, task_dir: Path, details: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": "0.1",
        "stage": "Stage 5.2J",
        "success": False,
        "verdict": status,
        "command_verdict": status,
        "materialization_status": status,
        "task_dir": str(task_dir),
        "details": details,
        "dry_run_only": True,
        "dry_run_request_materialized": False,
        "active_request_created": False,
        "request_active": False,
        "executable_request": False,
        "solver_execution_allowed": False,
        "solver_request_created": False,
        "solver_run": False,
        "queue_entry_created": False,
        "final_evidence_approved": False,
        "final_verdict_frozen": False,
    }
