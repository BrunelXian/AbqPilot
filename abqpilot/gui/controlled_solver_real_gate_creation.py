from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from abqpilot.gui.controlled_solver_candidate_hash import compute_candidate_artifact_hash
from abqpilot.gui.controlled_solver_real_gate_validator import validate_controlled_solver_real_gate_smoke
from abqpilot.gui.controlled_solver_real_gate_report import (
    render_no_execution_audit,
    render_real_gate_creation_report,
    render_real_gate_validation_report,
)


STAGE5_2F_VERDICT = "PASS_ABQPILOT_V2_STAGE5_2F_CONTROLLED_SOLVER_REAL_HUMAN_GATE_WITHOUT_EXECUTION_READY"
SMOKE_TASK_ID = "stage5_2f_controlled_solver_real_gate_smoke"
APPROVAL_PHRASE = "I_APPROVE_ABQPILOT_CONTROLLED_SOLVER_REAL_GATE_SMOKE_NO_EXECUTION"
ACK_FLAGS = (
    "understands_solver_will_run_in_future_stage_only",
    "understands_no_solver_execution_in_stage_5_2f",
    "understands_no_solver_request_created",
    "understands_no_queue_mutation",
    "understands_no_odb_open",
    "understands_no_metrics_approval",
    "understands_no_final_evidence_approval",
    "understands_no_final_verdict_freeze",
)


def create_controlled_solver_real_gate_smoke(project_root: str | Path) -> dict[str, Any]:
    root = Path(project_root)
    task_dir = root / "runs" / "tasks" / SMOKE_TASK_ID
    paths = _paths(task_dir)
    for path in (paths["trace_dir"], paths["handoffs_dir"], paths["gates_dir"], paths["candidates_dir"], paths["approvals_dir"], paths["reports_dir"]):
        path.mkdir(parents=True, exist_ok=True)

    candidate_text = "\n".join(
        [
            "** ABQPILOT_STAGE5_2F_SMOKE_CANDIDATE_ONLY **",
            "** NOT FOR SOLVER EXECUTION IN STAGE 5.2F **",
            "*Heading",
            "Stage 5.2F controlled solver gate smoke candidate only.",
            "",
        ]
    )
    paths["candidate"].write_text(candidate_text, encoding="utf-8")
    hash_meta = compute_candidate_artifact_hash(paths["candidate"])
    token = build_stage5_2f_human_approval_token(task_dir, paths["candidate"], hash_meta["hash"])
    token_validation = validate_stage5_2f_human_approval_token(token, task_dir, paths["candidate"])
    if token_validation["validation_status"] != "STAGE5_2F_TOKEN_VALID":
        return _blocked("CONTROLLED_SOLVER_REAL_GATE_TOKEN_INVALID", task_dir, token_validation)

    gate = build_stage5_2f_real_gate_record(task_dir, paths["candidate"], hash_meta["hash"], token)
    validation = validate_controlled_solver_real_gate_smoke(task_dir, gate, token)
    if validation["validation_status"] != "CONTROLLED_SOLVER_REAL_GATE_VALID_NO_EXECUTION":
        return _blocked("CONTROLLED_SOLVER_REAL_GATE_VALIDATION_FAILED", task_dir, validation)

    paths["task_plan"].write_text(_task_plan(), encoding="utf-8")
    paths["trace_index"].write_text(_trace_index(), encoding="utf-8")
    paths["run_precheck"].write_text(_run_record("RUN_001", "CONTROLLED_SOLVER_GATE_PRECHECK", "CONTROLLED_SOLVER_GATE_PRECHECK_COMPLETE"), encoding="utf-8")
    paths["run_creation"].write_text(_run_record("RUN_002", "CONTROLLED_SOLVER_ACTIVE_GATE_CREATION", "CONTROLLED_SOLVER_REAL_GATE_CREATED_NO_EXECUTION"), encoding="utf-8")
    paths["handoff"].write_text(_future_design_handoff(), encoding="utf-8")
    paths["gate_md"].write_text(_gate_markdown(gate), encoding="utf-8")
    paths["gate_json"].write_text(json.dumps(gate, indent=2, ensure_ascii=False), encoding="utf-8")
    paths["token"].write_text(json.dumps(token, indent=2, ensure_ascii=False), encoding="utf-8")
    paths["task_report"].write_text(render_real_gate_creation_report(gate, validation), encoding="utf-8")

    out = root / "gui_high_risk_gate_ux" / "controlled_solver_real_gate_without_execution"
    out.mkdir(parents=True, exist_ok=True)
    output_paths = {
        "creation_result": out / "CONTROLLED_SOLVER_REAL_GATE_CREATION_RESULT.json",
        "creation_report": out / "CONTROLLED_SOLVER_REAL_GATE_CREATION_REPORT.md",
        "validation_report": out / "CONTROLLED_SOLVER_REAL_GATE_VALIDATION_REPORT.md",
        "no_execution_audit": out / "CONTROLLED_SOLVER_REAL_GATE_NO_EXECUTION_AUDIT.md",
    }
    result = {
        "schema_version": "0.1",
        "stage": "Stage 5.2F",
        "verdict": STAGE5_2F_VERDICT,
        "command_verdict": "CONTROLLED_SOLVER_REAL_GATE_SMOKE_CREATED_NO_EXECUTION",
        "success": True,
        "task_id": SMOKE_TASK_ID,
        "task_dir": str(task_dir),
        "real_gate_created": True,
        "real_gate_created_only_in_stage5_2f_smoke_task": True,
        "arbitrary_real_task_gate_write_enabled": False,
        "solver_execution_allowed": False,
        "solver_request_created": False,
        "solver_run": False,
        "queue_runner_launched": False,
        "odb_opened": False,
        "odb_metrics_approved": False,
        "final_evidence_approved": False,
        "final_verdict_frozen": False,
        "task_final_evidence_ledger_updated": False,
        "no_solver_request_files_found": validation["no_solver_request_files_found"],
        "no_execution_handoff_found": validation["no_execution_handoff_found"],
        "no_queue_files_found": validation["no_queue_files_found"],
        "no_odb_files_found": validation["no_odb_files_found"],
        "gate_json": str(paths["gate_json"]),
        "gate_markdown": str(paths["gate_md"]),
        "candidate": str(paths["candidate"]),
        "token": str(paths["token"]),
        "validation": validation,
    }
    output_paths["creation_result"].write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    output_paths["creation_report"].write_text(render_real_gate_creation_report(gate, validation), encoding="utf-8")
    output_paths["validation_report"].write_text(render_real_gate_validation_report(validation), encoding="utf-8")
    output_paths["no_execution_audit"].write_text(render_no_execution_audit(result), encoding="utf-8")
    result["output_paths"] = {key: str(path) for key, path in output_paths.items()}
    return result


def build_stage5_2f_human_approval_token(task_dir: Path, candidate: Path, candidate_hash: str | None) -> dict[str, Any]:
    return {
        "token_type": "CONTROLLED_SOLVER_RUN_APPROVAL",
        "token_version": "0.2",
        "task_id": SMOKE_TASK_ID,
        "task_dir": str(task_dir),
        "candidate_artifact_hash": candidate_hash,
        "candidate_artifact_path": str(candidate),
        "approver_type": "HUMAN",
        "approval_phrase_required": APPROVAL_PHRASE,
        "approval_phrase_supplied": APPROVAL_PHRASE,
        "acknowledgement_flags": {flag: True for flag in ACK_FLAGS},
        "one_time_use": True,
        "active_approval": True,
        "active_approval_allowed_stage": "STAGE5_2F",
        "solver_execution_allowed": False,
        "final_evidence_approved": False,
        "final_verdict_frozen": False,
        "consumed": True,
        "consumed_once": True,
    }


def validate_stage5_2f_human_approval_token(token: dict[str, Any], task_dir: Path, candidate: Path) -> dict[str, Any]:
    if token.get("task_id") != SMOKE_TASK_ID or Path(str(token.get("task_dir"))) != task_dir:
        return _token_result("STAGE5_2F_TOKEN_BLOCKED_TASK_MISMATCH")
    expected_hash = compute_candidate_artifact_hash(candidate)["hash"]
    if not expected_hash or token.get("candidate_artifact_hash") != expected_hash:
        return _token_result("STAGE5_2F_TOKEN_BLOCKED_CANDIDATE_HASH")
    if token.get("approval_phrase_required") != APPROVAL_PHRASE or token.get("approval_phrase_supplied") != APPROVAL_PHRASE:
        return _token_result("STAGE5_2F_TOKEN_BLOCKED_APPROVAL_PHRASE")
    flags = token.get("acknowledgement_flags") or {}
    if any(flags.get(flag) is not True for flag in ACK_FLAGS):
        return _token_result("STAGE5_2F_TOKEN_BLOCKED_ACKNOWLEDGEMENT_FLAGS")
    if token.get("active_approval") is not True or token.get("active_approval_allowed_stage") != "STAGE5_2F":
        return _token_result("STAGE5_2F_TOKEN_BLOCKED_ACTIVE_APPROVAL_STAGE")
    if token.get("solver_execution_allowed") is True:
        return _token_result("STAGE5_2F_TOKEN_BLOCKED_EXECUTION_ALLOWED")
    if token.get("final_evidence_approved") is True or token.get("final_verdict_frozen") is True:
        return _token_result("STAGE5_2F_TOKEN_BLOCKED_FINAL_EVIDENCE")
    return _token_result("STAGE5_2F_TOKEN_VALID")


def build_stage5_2f_real_gate_record(task_dir: Path, candidate: Path, candidate_hash: str | None, token: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": "0.1",
        "doc_type": "gate_decision",
        "gate_id": "GATE_001",
        "gate_type": "CONTROLLED_SOLVER_RUN",
        "stage_id": "STAGE5_2F",
        "task_id": SMOKE_TASK_ID,
        "task_dir": str(task_dir),
        "real_project_gate_written": True,
        "smoke_task_only": True,
        "restricted_to_stage5_2f_smoke_task": True,
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
        "token_consumed_once": token.get("consumed_once") is True,
        "candidate_artifact_path": str(candidate),
        "candidate_artifact_hash": candidate_hash,
        "candidate_artifact_hash_algorithm": "SHA256",
        "approver_type": "HUMAN",
        "approval_phrase_verified": True,
        "acknowledgement_flags_verified": True,
        "downstream_execution_stage_required": True,
        "downstream_execution_auto_start": False,
        "downstream_execution_handoff_created": False,
        "odb_open_allowed": False,
        "metrics_extraction_allowed": False,
        "final_evidence_approval_allowed": False,
        "no_solver_execution_notice": "Human gate created; solver execution remains disabled in Stage 5.2F.",
        "no_solver_request_notice": "No solver request file is created in Stage 5.2F.",
        "final_evidence_locked_notice": "Final evidence remains locked.",
        "created_at": datetime.now().isoformat(timespec="seconds"),
    }


def _paths(task_dir: Path) -> dict[str, Path]:
    return {
        "task_plan": task_dir / "TASK_PLAN.md",
        "trace_index": task_dir / "TRACE_INDEX.md",
        "trace_dir": task_dir / "trace",
        "handoffs_dir": task_dir / "handoffs",
        "gates_dir": task_dir / "gates",
        "candidates_dir": task_dir / "artifacts" / "candidates",
        "approvals_dir": task_dir / "artifacts" / "approvals",
        "reports_dir": task_dir / "reports",
        "run_precheck": task_dir / "trace" / "RUN_001_CONTROLLED_SOLVER_GATE_PRECHECK.md",
        "run_creation": task_dir / "trace" / "RUN_002_CONTROLLED_SOLVER_ACTIVE_GATE_CREATION.md",
        "handoff": task_dir / "handoffs" / "HANDOFF_001_CONTROLLED_SOLVER_GATE_TO_FUTURE_EXECUTION_DESIGN.md",
        "gate_md": task_dir / "gates" / "GATE_001_CONTROLLED_SOLVER_HUMAN_APPROVAL.md",
        "gate_json": task_dir / "gates" / "GATE_001_CONTROLLED_SOLVER_HUMAN_APPROVAL.json",
        "candidate": task_dir / "artifacts" / "candidates" / "candidate_controlled_solver_smoke.inp",
        "token": task_dir / "artifacts" / "approvals" / "HUMAN_APPROVAL_TOKEN_PREVIEW.json",
        "task_report": task_dir / "reports" / "CONTROLLED_SOLVER_GATE_CREATION_REPORT.md",
    }


def _task_plan() -> str:
    return "# Stage 5.2F Controlled Solver Real Gate Smoke\n\nHuman gate creation only. No solver execution.\n"


def _trace_index() -> str:
    return "\n".join(
        [
            "# TRACE_INDEX",
            "",
            "- trace/RUN_001_CONTROLLED_SOLVER_GATE_PRECHECK.md",
            "- trace/RUN_002_CONTROLLED_SOLVER_ACTIVE_GATE_CREATION.md",
            "- gates/GATE_001_CONTROLLED_SOLVER_HUMAN_APPROVAL.md",
            "- handoffs/HANDOFF_001_CONTROLLED_SOLVER_GATE_TO_FUTURE_EXECUTION_DESIGN.md",
            "",
        ]
    )


def _run_record(run_id: str, run_name: str, status: str) -> str:
    return f"""---
doc_type: run_report
task_id: {SMOKE_TASK_ID}
run_id: {run_id}
run_name: {run_name}
agent: PipelineSupervisor
status: {status}
risk_level: HIGH
solver_execution_allowed: false
solver_request_created: false
solver_run: false
final_evidence_approved: false
final_verdict_frozen: false
---

# {run_name}

Stage 5.2F human approval gate creation without execution.
"""


def _future_design_handoff() -> str:
    return f"""---
doc_type: handoff
task_id: {SMOKE_TASK_ID}
handoff_id: HANDOFF_001
handoff_type: CONTROLLED_SOLVER_GATE_TO_FUTURE_EXECUTION_DESIGN
from_agent: PipelineSupervisor
to_agent: ExecutionAgent
handoff_active_for_execution: false
future_stage_required: true
solver_auto_start: false
solver_request_created: false
final_evidence_approved: false
final_verdict_frozen: false
---

# Future Execution Design Handoff

This handoff is design-only and future-stage only. It is not an active execution handoff.
"""


def _gate_markdown(gate: dict[str, Any]) -> str:
    return f"""---
doc_type: gate_decision
gate_id: GATE_001
gate_type: CONTROLLED_SOLVER_RUN
stage_id: STAGE5_2F
task_id: {SMOKE_TASK_ID}
decision: APPROVED_BY_HUMAN
approval_status: APPROVED_BY_HUMAN
execution_status: NOT_EXECUTED
solver_approved: true
solver_execution_allowed: false
solver_request_created: false
solver_run: false
queue_runner_launched: false
odb_opened: false
odb_metrics_approved: false
final_evidence_approved: false
final_verdict_frozen: false
task_final_evidence_ledger_updated: false
downstream_execution_stage_required: true
downstream_execution_auto_start: false
---

# Controlled Solver Human Approval Gate

Human approval gate record created for the Stage 5.2F smoke task only.

Solver execution is not allowed in Stage 5.2F. No solver request file is created. Final evidence remains locked.

Candidate hash: `{gate.get('candidate_artifact_hash')}`
"""


def _blocked(status: str, task_dir: Path, details: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": "0.1",
        "stage": "Stage 5.2F",
        "success": False,
        "verdict": status,
        "task_dir": str(task_dir),
        "details": details,
        "solver_request_created": False,
        "solver_run": False,
        "final_evidence_approved": False,
        "final_verdict_frozen": False,
    }


def _token_result(status: str) -> dict[str, Any]:
    return {
        "schema_version": "0.1",
        "stage": "Stage 5.2F",
        "validation_status": status,
        "solver_execution_allowed": False,
        "final_evidence_approved": False,
        "final_verdict_frozen": False,
    }
