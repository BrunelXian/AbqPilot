from __future__ import annotations

from pathlib import Path
from typing import Any

from abqpilot.repair.solver_failure_context import build_solver_failure_context
from abqpilot.repair.solver_failure_repair_artifacts import write_repair_artifacts
from abqpilot.repair.solver_failure_repair_report import render_solver_failure_repair_summary
from abqpilot.repair.solver_failure_repair_schema import (
    ALLOWED_PATCH_SCOPE,
    FORBIDDEN_PATCH_SCOPE,
    SCHEMA_VERSION,
    STAGE,
    validate_repair_proposal,
)


def propose_solver_failure_repair(
    solver_run_dir: str | Path,
    diagnosis_path: str | Path | None = None,
    output_dir: str | Path | None = None,
) -> dict[str, Any]:
    run_dir = Path(solver_run_dir)
    out_dir = Path(output_dir) if output_dir else run_dir / "solver_failure_repair_proposal"
    context = build_solver_failure_context(run_dir, diagnosis_path)
    proposal = _proposal_from_context(context)
    validation = validate_repair_proposal(proposal)
    if not validation["valid"]:
        proposal["repair_proposal_status"] = "REPAIR_PROPOSAL_REJECTED_BY_SCHEMA"
    summary = render_solver_failure_repair_summary(proposal, validation)
    paths = write_repair_artifacts(out_dir, context, proposal, validation, summary)
    return {
        "command": "propose-solver-repair",
        "verdict": proposal["repair_proposal_status"],
        "success": proposal["repair_proposal_status"]
        in {"REPAIR_PROPOSAL_READY", "REPAIR_PROPOSAL_MANUAL_REVIEW_ONLY"},
        "details": proposal,
        "output_paths": {"artifact_dir": str(out_dir), **paths},
        "errors": [] if validation["valid"] else validation["errors"],
        "warnings": [],
    }


def _proposal_from_context(context: dict[str, Any]) -> dict[str, Any]:
    if not context.get("diagnosis_exists"):
        return _base_proposal(context, "REPAIR_PROPOSAL_BLOCKED_NO_DIAGNOSIS", "manual_review_required", [], "low")
    status = context.get("diagnosis_status")
    evidence = context.get("evidence", {})
    if status == "JOB_SOLVER_CONVERGENCE_FAILED" and evidence.get("too_many_attempts") is True:
        proposal = _base_proposal(
            context,
            "REPAIR_PROPOSAL_READY",
            "step_increment_relaxation",
            ["minimum_increment_reduction", "maximum_increment_attempts_increase", "load_ramp_smoothing"],
            "medium",
        )
        proposal["next_allowed_action"] = "Create a guarded solver-control patch preview in a later stage."
        return proposal
    if status == "JOB_INPUT_PROCESSOR_FAILED":
        proposal = _base_proposal(
            context,
            "REPAIR_PROPOSAL_MANUAL_REVIEW_ONLY",
            "manual_review_required",
            [],
            "medium",
        )
        proposal["next_allowed_action"] = "Inspect keyword/reference errors; do not propose solver-control repair blindly."
        return proposal
    if status in {"JOB_STATUS_UNKNOWN", "JOB_ODB_EXISTS_BUT_COMPLETION_NOT_PROVEN"}:
        return _base_proposal(context, "REPAIR_PROPOSAL_BLOCKED_UNKNOWN_FAILURE", "manual_review_required", [], "low")
    return _base_proposal(context, "REPAIR_PROPOSAL_MANUAL_REVIEW_ONLY", "manual_review_required", [], "low")


def _base_proposal(
    context: dict[str, Any],
    proposal_status: str,
    recommended_type: str,
    secondary_types: list[str],
    confidence: str,
) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "stage": STAGE,
        "source_diagnosis_path": context.get("diagnosis_path"),
        "solver_run_dir": context.get("solver_run_dir"),
        "job_name": context.get("job_name"),
        "diagnosis_status": context.get("diagnosis_status"),
        "failure_category": context.get("failure_category"),
        "repair_proposal_status": proposal_status,
        "recommended_repair_type": recommended_type,
        "secondary_repair_types": secondary_types,
        "allowed_patch_scope": list(ALLOWED_PATCH_SCOPE),
        "forbidden_patch_scope": list(FORBIDDEN_PATCH_SCOPE),
        "evidence_summary": dict(context.get("evidence", {})),
        "important_lines": dict(context.get("important_lines", {})),
        "candidate_traceability_required": True,
        "candidate_inp_path": context.get("candidate_inp_path"),
        "candidate_inp_sha256": context.get("candidate_inp_sha256"),
        "candidate_traceability": context.get("candidate_traceability"),
        "guard_statuses": context.get("guard_statuses", {}),
        "solver_command_preview_sha256": context.get("solver_command_preview_sha256"),
        "requires_human_review": True,
        "apply_repair_now": False,
        "run_solver_now": False,
        "confidence": confidence,
        "next_allowed_action": "Human review required before any later guarded patch preview.",
        "safety_flags": {
            "mutated_inp": False,
            "opened_odb": False,
            "submitted_solver": False,
            "queue_runner_launched": False,
            "llm_used": False,
        },
    }

