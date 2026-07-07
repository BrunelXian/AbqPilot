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
from abqpilot.gui.controlled_solver_request_report import (
    render_request_draft_report,
    render_request_draft_schema_markdown,
    render_request_no_execution_audit,
)
from abqpilot.gui.controlled_solver_request_shape import build_expected_future_solver_request_shape
from abqpilot.gui.controlled_solver_request_validator import (
    HASH_MISMATCH,
    HANDOFF_INVALID,
    MISSING_SOURCE,
    READY,
    SOURCE_GATE_INVALID,
    validate_controlled_solver_request_draft,
)


STAGE5_2H_VERDICT = "PASS_ABQPILOT_V2_STAGE5_2H_CONTROLLED_SOLVER_REQUEST_DRAFT_SCHEMA_WITHOUT_EXECUTION_READY"
COMMAND_VERDICT = "CONTROLLED_SOLVER_REQUEST_DRAFT_SCHEMA_CREATED_NO_EXECUTION"


def create_controlled_solver_request_draft_no_exec(project_root: str | Path) -> dict[str, Any]:
    root = Path(project_root)
    task_dir = root / "runs" / "tasks" / SMOKE_TASK_ID
    sources = _source_paths(task_dir)
    missing = [str(path) for path in sources.values() if not path.exists()]
    if missing:
        return _blocked(MISSING_SOURCE, task_dir, {"missing": missing})

    gate = json.loads(sources["gate_json"].read_text(encoding="utf-8"))
    token = json.loads(sources["token"].read_text(encoding="utf-8"))
    handoff = json.loads(sources["handoff_draft"].read_text(encoding="utf-8"))
    source_gate_validation = validate_controlled_solver_real_gate_smoke(task_dir, gate, token)
    if source_gate_validation.get("validation_status") != "CONTROLLED_SOLVER_REAL_GATE_VALID_NO_EXECUTION":
        return _blocked(SOURCE_GATE_INVALID, task_dir, {"source_gate_validation": source_gate_validation})

    handoff_validation = validate_controlled_solver_execution_handoff_draft(handoff)
    if handoff_validation.get("validation_status") != HANDOFF_READY:
        return _blocked(HANDOFF_INVALID, task_dir, {"handoff_validation": handoff_validation})

    candidate = sources["candidate"]
    hash_meta = compute_candidate_artifact_hash(candidate)
    candidate_hash = hash_meta.get("hash")
    if not candidate_hash or candidate_hash != gate.get("candidate_artifact_hash") or candidate_hash != handoff.get("candidate_artifact_hash"):
        return _blocked(HASH_MISMATCH, task_dir, {"hash_metadata": hash_meta})

    future_shape = build_expected_future_solver_request_shape(
        task_id=SMOKE_TASK_ID,
        source_gate_id=str(gate.get("gate_id", "GATE_001")),
        source_handoff_id="CONTROLLED_SOLVER_EXECUTION_HANDOFF_DRAFT",
        candidate_inp_path=candidate,
        candidate_inp_sha256=candidate_hash,
    )
    draft = build_controlled_solver_request_draft(task_dir, gate, handoff, candidate, candidate_hash, future_shape)
    validation = validate_controlled_solver_request_draft(draft)
    audit = audit_controlled_solver_request_draft_no_execution(task_dir, draft)
    if validation.get("validation_status") != READY:
        return _blocked(validation.get("validation_status", "CONTROLLED_SOLVER_REQUEST_DRAFT_REVIEW_REQUIRED"), task_dir, {"validation": validation})

    draft_dir = task_dir / "artifacts" / "request_drafts"
    out_dir = root / "gui_high_risk_gate_ux" / "controlled_solver_request_draft_schema"
    draft_dir.mkdir(parents=True, exist_ok=True)
    out_dir.mkdir(parents=True, exist_ok=True)

    schema_json = draft_dir / "CONTROLLED_SOLVER_REQUEST_DRAFT_SCHEMA.json"
    example_json = draft_dir / "CONTROLLED_SOLVER_REQUEST_DRAFT_EXAMPLE.json"
    validation_json = draft_dir / "CONTROLLED_SOLVER_REQUEST_DRAFT_VALIDATION.json"
    result_json = out_dir / "CONTROLLED_SOLVER_REQUEST_DRAFT_SCHEMA_RESULT.json"
    report_md = out_dir / "CONTROLLED_SOLVER_REQUEST_DRAFT_SCHEMA_REPORT.md"
    out_validation_json = out_dir / "CONTROLLED_SOLVER_REQUEST_DRAFT_VALIDATION.json"
    audit_md = out_dir / "CONTROLLED_SOLVER_REQUEST_DRAFT_NO_EXECUTION_AUDIT.md"
    audit_json = out_dir / "CONTROLLED_SOLVER_REQUEST_DRAFT_NO_EXECUTION_AUDIT.json"
    future_shape_json = out_dir / "CONTROLLED_SOLVER_FUTURE_REQUEST_SHAPE.json"
    card_json = out_dir / "CONTROLLED_SOLVER_REQUEST_DRAFT_CARD.json"

    result = {
        "schema_version": "0.1",
        "stage": "Stage 5.2H",
        "verdict": STAGE5_2H_VERDICT,
        "command_verdict": COMMAND_VERDICT,
        "success": True,
        "draft_created": True,
        "task_id": SMOKE_TASK_ID,
        "task_dir": str(task_dir),
        "source_gate_validation_status": source_gate_validation.get("validation_status"),
        "source_handoff_validation_status": handoff_validation.get("validation_status"),
        "candidate_hash_verified": True,
        "draft": draft,
        "expected_future_solver_request_shape": future_shape,
        "validation": validation,
        "no_execution_audit": audit,
        "draft_only": True,
        "request_active": False,
        "executable_request": False,
        "solver_execution_allowed": False,
        "solver_request_created": False,
        "solver_run": False,
        "queue_runner_launched": False,
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
        "output_paths": {
            "schema_json": str(schema_json),
            "example_json": str(example_json),
            "validation_json": str(validation_json),
            "result_json": str(result_json),
            "report_markdown": str(report_md),
            "out_validation_json": str(out_validation_json),
            "audit_markdown": str(audit_md),
            "audit_json": str(audit_json),
            "future_shape_json": str(future_shape_json),
            "card_json": str(card_json),
        },
    }
    schema_json.write_text(json.dumps(draft, indent=2, ensure_ascii=False), encoding="utf-8")
    example_json.write_text(json.dumps({"draft": draft, "expected_future_solver_request_shape": future_shape}, indent=2, ensure_ascii=False), encoding="utf-8")
    validation_json.write_text(json.dumps(validation, indent=2, ensure_ascii=False), encoding="utf-8")
    result_json.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    report_md.write_text(render_request_draft_report(result), encoding="utf-8")
    out_validation_json.write_text(json.dumps(validation, indent=2, ensure_ascii=False), encoding="utf-8")
    audit_md.write_text(render_request_no_execution_audit(audit), encoding="utf-8")
    audit_json.write_text(json.dumps(audit, indent=2, ensure_ascii=False), encoding="utf-8")
    future_shape_json.write_text(json.dumps(future_shape, indent=2, ensure_ascii=False), encoding="utf-8")
    card_json.write_text(json.dumps(_card_payload(result), indent=2, ensure_ascii=False), encoding="utf-8")
    return result


def build_controlled_solver_request_draft(
    task_dir: str | Path,
    source_gate: dict[str, Any],
    handoff_draft: dict[str, Any],
    candidate: str | Path,
    candidate_hash: str,
    future_shape: dict[str, Any],
) -> dict[str, Any]:
    task = Path(task_dir)
    candidate_path = Path(candidate)
    return {
        "schema_version": "0.1",
        "draft_type": "CONTROLLED_SOLVER_REQUEST_DRAFT",
        "stage_id": "STAGE5_2H",
        "source_stage_id": "STAGE5_2G",
        "source_task_id": SMOKE_TASK_ID,
        "source_gate_id": source_gate.get("gate_id", "GATE_001"),
        "source_gate_type": "CONTROLLED_SOLVER_RUN",
        "source_gate_decision": source_gate.get("decision"),
        "source_gate_validated": True,
        "source_handoff_draft_validated": True,
        "source_handoff_draft_type": handoff_draft.get("draft_type"),
        "candidate_artifact_path": str(candidate_path),
        "candidate_artifact_hash": candidate_hash,
        "candidate_artifact_hash_algorithm": "SHA256",
        "candidate_hash_verified": True,
        "target_agent": "ExecutionAgent",
        "target_future_stage": "FUTURE_CONTROLLED_SOLVER_EXECUTION_STAGE",
        "draft_only": True,
        "request_active": False,
        "executable_request": False,
        "future_stage_required": True,
        "solver_command_label": future_shape["solver_command_label"],
        "solver_command_path_included": False,
        "solver_command_not_invoked": True,
        "allowed_output_dir_preview": str(task / "future_controlled_solver_outputs"),
        "output_dir_created": False,
        "solver_approved_by_source_gate": source_gate.get("solver_approved") is True,
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
        "no_solver_execution_notice": "Draft schema only; no Abaqus solver command is executed.",
        "no_solver_request_notice": "No solver_request.json is created in Stage 5.2H.",
        "no_queue_notice": "No queue runner launch or queue mutation is allowed.",
        "no_odb_notice": "No ODB is opened or accepted.",
        "no_metrics_notice": "No metrics are extracted or approved.",
        "final_evidence_locked_notice": "Final evidence remains locked.",
        "required_future_execution_inputs": [
            "Stage 5.2F source gate JSON",
            "Stage 5.2G execution handoff draft",
            "candidate INP artifact",
            "verified candidate SHA256 hash",
            "future explicit controlled solver execution stage",
        ],
        "expected_future_execution_outputs": [
            "future active solver request only in a later explicit execution stage",
            "future solver output directory only after that stage is authorized",
        ],
        "forbidden_stage5_2h_outputs": [
            "solver_request.json",
            "job_request.json",
            "abaqus_job.json",
            ".bat or .cmd solver launcher",
            "active HANDOFF_*.md execution handoff",
            "queue files",
            "ODB files",
            "metrics files",
            "TASK_FINAL_EVIDENCE_LEDGER.md",
        ],
        "expected_future_solver_request_shape": future_shape,
        "safety_boundary": "This is not a real solver_request.json, job request, queue submission, Abaqus command, ODB acceptance, metrics approval, final evidence approval, or final verdict freeze.",
        "draft_path": str(task / "artifacts" / "request_drafts" / "CONTROLLED_SOLVER_REQUEST_DRAFT_SCHEMA.json"),
        "created_at": datetime.now().isoformat(timespec="seconds"),
    }


def _source_paths(task_dir: Path) -> dict[str, Path]:
    return {
        "gate_json": task_dir / "gates" / "GATE_001_CONTROLLED_SOLVER_HUMAN_APPROVAL.json",
        "candidate": task_dir / "artifacts" / "candidates" / "candidate_controlled_solver_smoke.inp",
        "token": task_dir / "artifacts" / "approvals" / "HUMAN_APPROVAL_TOKEN_PREVIEW.json",
        "handoff_draft": task_dir / "artifacts" / "handoff_drafts" / "CONTROLLED_SOLVER_EXECUTION_HANDOFF_DRAFT.json",
    }


def _card_payload(result: dict[str, Any]) -> dict[str, Any]:
    return {
        "title": "Controlled Solver Request Draft Schema [DRAFT ONLY]",
        "draft_exists": True,
        "source_gate_validated": result.get("source_gate_validation_status") == "CONTROLLED_SOLVER_REAL_GATE_VALID_NO_EXECUTION",
        "source_handoff_draft_validated": result.get("source_handoff_validation_status") == "CONTROLLED_SOLVER_EXECUTION_HANDOFF_DRAFT_READY",
        "candidate_hash_verified": result.get("candidate_hash_verified") is True,
        "target_agent": "ExecutionAgent",
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
        "stage": "Stage 5.2H",
        "success": False,
        "verdict": status,
        "command_verdict": status,
        "task_dir": str(task_dir),
        "details": details,
        "draft_created": False,
        "draft_only": True,
        "request_active": False,
        "executable_request": False,
        "solver_execution_allowed": False,
        "solver_request_created": False,
        "solver_run": False,
        "final_evidence_approved": False,
        "final_verdict_frozen": False,
    }
