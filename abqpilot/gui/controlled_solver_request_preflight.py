from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from abqpilot.gui.controlled_solver_candidate_hash import compute_candidate_artifact_hash
from abqpilot.gui.controlled_solver_execution_handoff_validator import READY as HANDOFF_READY
from abqpilot.gui.controlled_solver_execution_handoff_validator import validate_controlled_solver_execution_handoff_draft
from abqpilot.gui.controlled_solver_real_gate_creation import SMOKE_TASK_ID
from abqpilot.gui.controlled_solver_real_gate_validator import validate_controlled_solver_real_gate_smoke
from abqpilot.gui.controlled_solver_request_audit import audit_controlled_solver_request_draft_no_execution
from abqpilot.gui.controlled_solver_request_policy import (
    RESOURCE_POLICY_DEFAULTS,
    validate_output_dir_policy,
    validate_resource_policy_shape,
    validate_solver_command_label_policy,
)
from abqpilot.gui.controlled_solver_request_preflight_audit import audit_controlled_solver_request_preflight_no_execution
from abqpilot.gui.controlled_solver_request_preflight_report import render_request_preflight_audit, render_request_preflight_report
from abqpilot.gui.controlled_solver_request_preflight_validator import (
    COMMAND_POLICY,
    DRAFT_INVALID,
    GATE_INVALID,
    HANDOFF_INVALID,
    HASH_MISMATCH,
    MISSING,
    OUTPUT_POLICY,
    PASS,
    RESOURCE_POLICY,
    validate_controlled_solver_request_preflight_result,
)
from abqpilot.gui.controlled_solver_request_validator import READY as REQUEST_READY
from abqpilot.gui.controlled_solver_request_validator import validate_controlled_solver_request_draft


STAGE5_2I_VERDICT = "PASS_ABQPILOT_V2_STAGE5_2I_CONTROLLED_SOLVER_REQUEST_PREFLIGHT_VALIDATOR_WITHOUT_EXECUTION_READY"
COMMAND_VERDICT = "CONTROLLED_SOLVER_REQUEST_PREFLIGHT_REPORT_READY_NO_EXECUTION"


def create_controlled_solver_request_preflight_no_exec(project_root: str | Path) -> dict[str, Any]:
    root = Path(project_root)
    task_dir = root / "runs" / "tasks" / SMOKE_TASK_ID
    sources = _source_paths(task_dir)
    missing = [str(path) for path in sources.values() if not path.exists()]
    if missing:
        return _blocked(MISSING, task_dir, {"missing": missing})

    gate = json.loads(sources["gate_json"].read_text(encoding="utf-8"))
    token = json.loads(sources["token"].read_text(encoding="utf-8"))
    handoff = json.loads(sources["handoff_draft"].read_text(encoding="utf-8"))
    request_draft = json.loads(sources["request_draft"].read_text(encoding="utf-8"))
    request_validation = json.loads(sources["request_validation"].read_text(encoding="utf-8"))

    gate_validation = validate_controlled_solver_real_gate_smoke(task_dir, gate, token)
    if gate_validation.get("validation_status") != "CONTROLLED_SOLVER_REAL_GATE_VALID_NO_EXECUTION":
        return _blocked(GATE_INVALID, task_dir, {"source_gate_validation": gate_validation})
    handoff_validation = validate_controlled_solver_execution_handoff_draft(handoff)
    if handoff_validation.get("validation_status") != HANDOFF_READY:
        return _blocked(HANDOFF_INVALID, task_dir, {"handoff_validation": handoff_validation})
    draft_validation = validate_controlled_solver_request_draft(request_draft)
    if draft_validation.get("validation_status") != REQUEST_READY or request_validation.get("validation_status") != REQUEST_READY:
        return _blocked(DRAFT_INVALID, task_dir, {"request_validation": draft_validation, "source_validation": request_validation})

    candidate = sources["candidate"]
    hash_meta = compute_candidate_artifact_hash(candidate)
    candidate_hash = hash_meta.get("hash")
    if not candidate_hash or candidate_hash != gate.get("candidate_artifact_hash") or candidate_hash != handoff.get("candidate_artifact_hash") or candidate_hash != request_draft.get("candidate_artifact_hash"):
        return _blocked(HASH_MISMATCH, task_dir, {"hash_metadata": hash_meta})

    command_policy = validate_solver_command_label_policy(
        request_draft.get("solver_command_label"),
        request_draft.get("solver_command_path_included") is True,
        request_draft.get("solver_command_not_invoked") is True,
    )
    if command_policy["policy_status"] != "SOLVER_COMMAND_LABEL_POLICY_VALID":
        return _blocked(COMMAND_POLICY, task_dir, {"command_policy": command_policy})
    output_policy = validate_output_dir_policy(
        request_draft.get("allowed_output_dir_preview"),
        task_dir,
        request_draft.get("output_dir_created") is True,
    )
    if output_policy["policy_status"] != "OUTPUT_DIR_POLICY_VALID":
        return _blocked(OUTPUT_POLICY, task_dir, {"output_policy": output_policy})
    resource_policy = validate_resource_policy_shape(request_draft)
    if resource_policy["policy_status"] != "RESOURCE_POLICY_SHAPE_VALID":
        return _blocked(RESOURCE_POLICY, task_dir, {"resource_policy": resource_policy})

    draft_audit = audit_controlled_solver_request_draft_no_execution(task_dir, request_draft)
    result = build_controlled_solver_request_preflight_result(
        task_dir=task_dir,
        gate=gate,
        handoff=handoff,
        request_draft=request_draft,
        candidate=candidate,
        candidate_hash=candidate_hash,
        command_policy=command_policy,
        output_policy=output_policy,
        resource_policy=resource_policy,
    )
    validation = validate_controlled_solver_request_preflight_result(result)
    audit = audit_controlled_solver_request_preflight_no_execution(task_dir, result)
    result["success"] = validation["validation_status"] == PASS
    result["verdict"] = STAGE5_2I_VERDICT if validation["validation_status"] == PASS else validation["validation_status"]
    result["command_verdict"] = COMMAND_VERDICT if validation["validation_status"] == PASS else validation["validation_status"]
    result["preflight_status"] = validation["validation_status"]
    result["preflight_passed"] = validation["validation_status"] == PASS
    result["validation"] = validation
    result["request_draft_audit"] = draft_audit
    result["no_execution_audit"] = audit
    if validation["validation_status"] != PASS:
        return _blocked(validation["validation_status"], task_dir, {"validation": validation})

    task_out = task_dir / "artifacts" / "request_preflight"
    project_out = root / "gui_high_risk_gate_ux" / "controlled_solver_request_preflight_validator"
    task_out.mkdir(parents=True, exist_ok=True)
    project_out.mkdir(parents=True, exist_ok=True)
    task_result = task_out / "CONTROLLED_SOLVER_REQUEST_PREFLIGHT_RESULT.json"
    task_report = task_out / "CONTROLLED_SOLVER_REQUEST_PREFLIGHT_REPORT.md"
    task_validation = task_out / "CONTROLLED_SOLVER_REQUEST_PREFLIGHT_VALIDATION.json"
    task_audit = task_out / "CONTROLLED_SOLVER_REQUEST_PREFLIGHT_NO_EXECUTION_AUDIT.md"
    project_result = project_out / "CONTROLLED_SOLVER_REQUEST_PREFLIGHT_RESULT.json"
    project_report = project_out / "CONTROLLED_SOLVER_REQUEST_PREFLIGHT_REPORT.md"
    project_validation = project_out / "CONTROLLED_SOLVER_REQUEST_PREFLIGHT_VALIDATION.json"
    project_audit_md = project_out / "CONTROLLED_SOLVER_REQUEST_PREFLIGHT_NO_EXECUTION_AUDIT.md"
    project_audit_json = project_out / "CONTROLLED_SOLVER_REQUEST_PREFLIGHT_NO_EXECUTION_AUDIT.json"
    card_json = project_out / "CONTROLLED_SOLVER_REQUEST_PREFLIGHT_CARD.json"
    result["output_paths"] = {
        "task_result": str(task_result),
        "task_report": str(task_report),
        "task_validation": str(task_validation),
        "task_audit": str(task_audit),
        "project_result": str(project_result),
        "project_report": str(project_report),
        "project_validation": str(project_validation),
        "project_audit_md": str(project_audit_md),
        "project_audit_json": str(project_audit_json),
        "card_json": str(card_json),
    }
    report = render_request_preflight_report(result)
    audit_md = render_request_preflight_audit(audit)
    for path in (task_result, project_result):
        path.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    for path in (task_report, project_report):
        path.write_text(report, encoding="utf-8")
    for path in (task_validation, project_validation):
        path.write_text(json.dumps(validation, indent=2, ensure_ascii=False), encoding="utf-8")
    for path in (task_audit, project_audit_md):
        path.write_text(audit_md, encoding="utf-8")
    project_audit_json.write_text(json.dumps(audit, indent=2, ensure_ascii=False), encoding="utf-8")
    card_json.write_text(json.dumps(_card_payload(result), indent=2, ensure_ascii=False), encoding="utf-8")
    return result


def build_controlled_solver_request_preflight_result(
    task_dir: str | Path,
    gate: dict[str, Any],
    handoff: dict[str, Any],
    request_draft: dict[str, Any],
    candidate: str | Path,
    candidate_hash: str,
    command_policy: dict[str, Any],
    output_policy: dict[str, Any],
    resource_policy: dict[str, Any],
) -> dict[str, Any]:
    return {
        "schema_version": "0.1",
        "result_type": "CONTROLLED_SOLVER_REQUEST_PREFLIGHT",
        "stage_id": "STAGE5_2I",
        "source_stage_id": "STAGE5_2H",
        "source_task_id": SMOKE_TASK_ID,
        "source_gate_id": gate.get("gate_id", "GATE_001"),
        "source_gate_validated": True,
        "source_handoff_draft_validated": handoff.get("draft_type") == "CONTROLLED_SOLVER_EXECUTION_HANDOFF_DRAFT",
        "source_request_draft_validated": request_draft.get("draft_type") == "CONTROLLED_SOLVER_REQUEST_DRAFT",
        "candidate_artifact_path": str(candidate),
        "candidate_artifact_hash": candidate_hash,
        "candidate_artifact_hash_algorithm": "SHA256",
        "candidate_hash_verified": True,
        "solver_command_label_validated": command_policy["solver_command_label_validated"],
        "solver_command_path_not_invoked": command_policy["solver_command_path_not_invoked"],
        "output_dir_policy_validated": output_policy["output_dir_policy_validated"],
        "output_dir_created": False,
        "cpu_policy_validated": resource_policy["cpu_policy_validated"],
        "memory_policy_validated": resource_policy["memory_policy_validated"],
        "timeout_policy_validated": resource_policy["timeout_policy_validated"],
        "log_capture_policy_validated": resource_policy["log_capture_policy_validated"],
        "preflight_only": True,
        "preflight_status": "CONTROLLED_SOLVER_REQUEST_PREFLIGHT_REVIEW_REQUIRED",
        "preflight_passed": False,
        "active_request_created": False,
        "request_active": False,
        "executable_request": False,
        "future_execution_stage_required": True,
        "target_agent": "ExecutionAgent",
        "solver_execution_allowed": False,
        "solver_request_created": False,
        "solver_run": False,
        "queue_runner_launched": False,
        "odb_opened": False,
        "odb_metrics_approved": False,
        "final_evidence_approved": False,
        "final_verdict_frozen": False,
        "task_final_evidence_ledger_updated": False,
        "downstream_execution_auto_start": False,
        "forbidden_artifacts_found": [],
        "missing_inputs": [],
        "warning_items": [],
        "blocked_items": [],
        "solver_command_policy": command_policy,
        "output_dir_policy": output_policy,
        "resource_policy": {**RESOURCE_POLICY_DEFAULTS, **resource_policy},
        "no_solver_execution_notice": "Preflight only; no solver execution.",
        "no_solver_request_notice": "No solver_request.json is created.",
        "no_queue_notice": "No queue mutation is created.",
        "no_odb_notice": "No ODB is opened or accepted.",
        "no_metrics_notice": "No metrics are extracted or approved.",
        "final_evidence_locked_notice": "Final evidence remains locked.",
        "safety_boundary": "This is not a solver request, job request, queue submission, Abaqus command, ODB acceptance, metrics approval, final evidence approval, or final verdict freeze.",
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
    }


def _card_payload(result: dict[str, Any]) -> dict[str, Any]:
    return {
        "title": "Controlled Solver Request Preflight [NO EXECUTION]",
        "preflight_exists": True,
        "source_gate_validated": result.get("source_gate_validated") is True,
        "source_handoff_draft_validated": result.get("source_handoff_draft_validated") is True,
        "source_request_draft_validated": result.get("source_request_draft_validated") is True,
        "candidate_hash_verified": result.get("candidate_hash_verified") is True,
        "solver_command_label_validated": result.get("solver_command_label_validated") is True,
        "output_dir_policy_validated": result.get("output_dir_policy_validated") is True,
        "resource_policy_validated": result.get("cpu_policy_validated") is True,
        "request_active": False,
        "executable_request": False,
        "solver_execution_allowed": False,
        "solver_request_created": False,
        "future_execution_stage_required": True,
        "final_evidence_locked": True,
        "backend_callback": None,
    }


def _blocked(status: str, task_dir: Path, details: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": "0.1",
        "stage": "Stage 5.2I",
        "success": False,
        "verdict": status,
        "command_verdict": status,
        "task_dir": str(task_dir),
        "details": details,
        "preflight_only": True,
        "preflight_passed": False,
        "active_request_created": False,
        "request_active": False,
        "executable_request": False,
        "solver_execution_allowed": False,
        "solver_request_created": False,
        "solver_run": False,
        "final_evidence_approved": False,
        "final_verdict_frozen": False,
    }
