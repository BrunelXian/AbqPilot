from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from abqpilot.gui.controlled_solver_candidate_hash import compute_candidate_artifact_hash
from abqpilot.gui.controlled_solver_execution_handoff_audit import audit_controlled_solver_execution_handoff_no_execution
from abqpilot.gui.controlled_solver_execution_handoff_report import (
    render_execution_handoff_draft_markdown,
    render_execution_handoff_report,
    render_no_execution_audit,
)
from abqpilot.gui.controlled_solver_execution_handoff_validator import (
    MISSING_SOURCE,
    READY,
    HASH_MISMATCH,
    SOURCE_INVALID,
    validate_controlled_solver_execution_handoff_draft,
)
from abqpilot.gui.controlled_solver_real_gate_creation import SMOKE_TASK_ID
from abqpilot.gui.controlled_solver_real_gate_validator import validate_controlled_solver_real_gate_smoke


STAGE5_2G_VERDICT = "PASS_ABQPILOT_V2_STAGE5_2G_CONTROLLED_SOLVER_EXECUTION_HANDOFF_DRAFT_WITHOUT_EXECUTION_READY"
COMMAND_VERDICT = "CONTROLLED_SOLVER_EXECUTION_HANDOFF_DRAFT_CREATED_NO_EXECUTION"


def create_controlled_solver_execution_handoff_draft_no_exec(project_root: str | Path) -> dict[str, Any]:
    root = Path(project_root)
    task_dir = root / "runs" / "tasks" / SMOKE_TASK_ID
    source_paths = _source_paths(task_dir)
    missing = [str(path) for path in source_paths.values() if not path.exists()]
    if missing:
        return _blocked(MISSING_SOURCE, task_dir, {"missing": missing})

    gate = json.loads(source_paths["gate_json"].read_text(encoding="utf-8"))
    token = json.loads(source_paths["token"].read_text(encoding="utf-8"))
    source_validation = validate_controlled_solver_real_gate_smoke(task_dir, gate, token)
    if source_validation.get("validation_status") != "CONTROLLED_SOLVER_REAL_GATE_VALID_NO_EXECUTION":
        return _blocked(SOURCE_INVALID, task_dir, {"source_validation": source_validation})

    candidate = source_paths["candidate"]
    hash_meta = compute_candidate_artifact_hash(candidate)
    candidate_hash = hash_meta.get("hash")
    if not candidate_hash or candidate_hash != gate.get("candidate_artifact_hash") or candidate_hash != token.get("candidate_artifact_hash"):
        return _blocked(HASH_MISMATCH, task_dir, {"hash_metadata": hash_meta})

    draft = build_controlled_solver_execution_handoff_draft(task_dir, gate, candidate, candidate_hash)
    validation = validate_controlled_solver_execution_handoff_draft(draft)
    audit = audit_controlled_solver_execution_handoff_no_execution(task_dir, draft)
    if validation.get("validation_status") != READY:
        return _blocked(validation.get("validation_status", "CONTROLLED_SOLVER_EXECUTION_HANDOFF_DRAFT_REVIEW_REQUIRED"), task_dir, {"validation": validation})

    draft_dir = task_dir / "artifacts" / "handoff_drafts"
    out_dir = root / "gui_high_risk_gate_ux" / "controlled_solver_execution_handoff_draft"
    draft_dir.mkdir(parents=True, exist_ok=True)
    out_dir.mkdir(parents=True, exist_ok=True)

    draft_json = draft_dir / "CONTROLLED_SOLVER_EXECUTION_HANDOFF_DRAFT.json"
    draft_md = draft_dir / "CONTROLLED_SOLVER_EXECUTION_HANDOFF_DRAFT.md"
    result_json = out_dir / "CONTROLLED_SOLVER_EXECUTION_HANDOFF_DRAFT_RESULT.json"
    report_md = out_dir / "CONTROLLED_SOLVER_EXECUTION_HANDOFF_DRAFT_REPORT.md"
    validation_json = out_dir / "CONTROLLED_SOLVER_EXECUTION_HANDOFF_DRAFT_VALIDATION.json"
    audit_md = out_dir / "CONTROLLED_SOLVER_EXECUTION_HANDOFF_DRAFT_NO_EXECUTION_AUDIT.md"
    audit_json = out_dir / "CONTROLLED_SOLVER_EXECUTION_HANDOFF_DRAFT_NO_EXECUTION_AUDIT.json"
    card_json = out_dir / "CONTROLLED_SOLVER_EXECUTION_HANDOFF_DRAFT_CARD.json"

    result = {
        "schema_version": "0.1",
        "stage": "Stage 5.2G",
        "verdict": STAGE5_2G_VERDICT,
        "command_verdict": COMMAND_VERDICT,
        "success": True,
        "draft_created": True,
        "task_id": SMOKE_TASK_ID,
        "task_dir": str(task_dir),
        "source_gate_validation_status": source_validation.get("validation_status"),
        "candidate_hash_verified": True,
        "draft": draft,
        "validation": validation,
        "no_execution_audit": audit,
        "draft_only": True,
        "active_execution_handoff": False,
        "handoff_active_for_execution": False,
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
            "draft_json": str(draft_json),
            "draft_markdown": str(draft_md),
            "result_json": str(result_json),
            "report_markdown": str(report_md),
            "validation_json": str(validation_json),
            "audit_markdown": str(audit_md),
            "audit_json": str(audit_json),
            "card_json": str(card_json),
        },
    }
    draft_json.write_text(json.dumps(draft, indent=2, ensure_ascii=False), encoding="utf-8")
    draft_md.write_text(render_execution_handoff_draft_markdown(draft, validation), encoding="utf-8")
    result_json.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    report_md.write_text(render_execution_handoff_report(result), encoding="utf-8")
    validation_json.write_text(json.dumps(validation, indent=2, ensure_ascii=False), encoding="utf-8")
    audit_md.write_text(render_no_execution_audit(audit), encoding="utf-8")
    audit_json.write_text(json.dumps(audit, indent=2, ensure_ascii=False), encoding="utf-8")
    card_json.write_text(json.dumps(_card_payload(result), indent=2, ensure_ascii=False), encoding="utf-8")
    return result


def build_controlled_solver_execution_handoff_draft(
    task_dir: str | Path,
    source_gate: dict[str, Any],
    candidate: str | Path,
    candidate_hash: str,
) -> dict[str, Any]:
    task = Path(task_dir)
    candidate_path = Path(candidate)
    return {
        "schema_version": "0.1",
        "draft_type": "CONTROLLED_SOLVER_EXECUTION_HANDOFF_DRAFT",
        "stage_id": "STAGE5_2G",
        "source_stage_id": "STAGE5_2F",
        "source_task_id": SMOKE_TASK_ID,
        "source_gate_id": source_gate.get("gate_id", "GATE_001"),
        "source_gate_type": "CONTROLLED_SOLVER_RUN",
        "source_gate_decision": source_gate.get("decision"),
        "source_gate_validated": True,
        "candidate_artifact_path": str(candidate_path),
        "candidate_artifact_hash": candidate_hash,
        "candidate_artifact_hash_algorithm": "SHA256",
        "candidate_hash_verified": True,
        "from_agent": "PipelineSupervisor",
        "to_agent": "ExecutionAgent",
        "target_future_stage": "FUTURE_CONTROLLED_SOLVER_EXECUTION_STAGE",
        "draft_only": True,
        "active_execution_handoff": False,
        "handoff_active_for_execution": False,
        "execution_status": "NOT_EXECUTABLE",
        "future_stage_required": True,
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
        "no_solver_execution_notice": "Draft only; no Abaqus solver command is executed.",
        "no_solver_request_notice": "No solver request file is created in Stage 5.2G.",
        "no_queue_notice": "No queue runner launch or queue mutation is allowed.",
        "no_odb_notice": "No ODB is opened or accepted.",
        "no_metrics_notice": "No metrics are extracted or approved.",
        "final_evidence_locked_notice": "Final evidence remains locked.",
        "required_future_execution_inputs": [
            "Stage 5.2F source gate JSON and Markdown",
            "candidate INP artifact",
            "verified candidate SHA256 hash",
            "future explicit controlled solver execution stage",
        ],
        "expected_future_execution_outputs": [
            "future solver request only in a later explicit execution stage",
            "future execution RUN/HANDOFF/GATE records only after that stage is authorized",
        ],
        "forbidden_stage5_2g_outputs": [
            "HANDOFF_*.md active execution handoff under task handoffs",
            "solver_request.json",
            "job_request.json",
            "abaqus_job.json",
            ".bat or .cmd solver launcher",
            "queue files",
            "ODB files",
            "metrics files",
            "TASK_FINAL_EVIDENCE_LEDGER.md",
        ],
        "safety_boundary": "This is not a solver request, job manifest, execution command, ODB acceptance, metrics approval, final evidence approval, or final verdict freeze.",
        "draft_path": str(task / "artifacts" / "handoff_drafts" / "CONTROLLED_SOLVER_EXECUTION_HANDOFF_DRAFT.json"),
        "created_at": datetime.now().isoformat(timespec="seconds"),
    }


def _source_paths(task_dir: Path) -> dict[str, Path]:
    return {
        "gate_json": task_dir / "gates" / "GATE_001_CONTROLLED_SOLVER_HUMAN_APPROVAL.json",
        "gate_markdown": task_dir / "gates" / "GATE_001_CONTROLLED_SOLVER_HUMAN_APPROVAL.md",
        "candidate": task_dir / "artifacts" / "candidates" / "candidate_controlled_solver_smoke.inp",
        "token": task_dir / "artifacts" / "approvals" / "HUMAN_APPROVAL_TOKEN_PREVIEW.json",
    }


def _card_payload(result: dict[str, Any]) -> dict[str, Any]:
    draft = result.get("draft", {})
    return {
        "title": "Controlled Solver Execution Handoff Draft [DRAFT ONLY]",
        "draft_exists": True,
        "source_gate_validated": result.get("source_gate_validation_status") == "CONTROLLED_SOLVER_REAL_GATE_VALID_NO_EXECUTION",
        "candidate_hash_verified": result.get("candidate_hash_verified") is True,
        "to_agent": draft.get("to_agent"),
        "active_execution_handoff": False,
        "handoff_active_for_execution": False,
        "solver_execution_allowed": False,
        "solver_request_created": False,
        "future_execution_stage_required": True,
        "final_evidence_locked": True,
        "backend_callback": None,
    }


def _blocked(status: str, task_dir: Path, details: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": "0.1",
        "stage": "Stage 5.2G",
        "success": False,
        "verdict": status,
        "command_verdict": status,
        "task_dir": str(task_dir),
        "details": details,
        "draft_created": False,
        "draft_only": True,
        "active_execution_handoff": False,
        "handoff_active_for_execution": False,
        "solver_execution_allowed": False,
        "solver_request_created": False,
        "solver_run": False,
        "final_evidence_approved": False,
        "final_verdict_frozen": False,
    }
