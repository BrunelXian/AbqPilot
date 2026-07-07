from __future__ import annotations

from typing import Any


def render_request_draft_report(result: dict[str, Any]) -> str:
    draft = result.get("draft", {})
    validation = result.get("validation", {})
    audit = result.get("no_execution_audit", {})
    return f"""# Stage 5.2H Controlled Solver Request Draft Schema Report

## Purpose

Stage 5.2H defines a draft schema for a future controlled solver request. It does not create an active solver request.

## Source Records

- Stage 5.2F gate validation: `{result.get('source_gate_validation_status')}`
- Stage 5.2G handoff draft validation: `{result.get('source_handoff_validation_status')}`
- Candidate hash verified: `{result.get('candidate_hash_verified')}`

## Request Draft

- Draft created: `{result.get('draft_created')}`
- Draft only: `{draft.get('draft_only')}`
- Request active: `{draft.get('request_active')}`
- Executable request: `{draft.get('executable_request')}`
- Target agent: `{draft.get('target_agent')}`
- Solver command path included: `{draft.get('solver_command_path_included')}`
- Solver command invoked: `{not draft.get('solver_command_not_invoked')}`
- Output directory created: `{draft.get('output_dir_created')}`

## Validation

- Request draft validation: `{validation.get('validation_status')}`
- No-execution audit: `{audit.get('audit_status')}`

## Safety Boundary

- Solver execution allowed: `{draft.get('solver_execution_allowed')}`
- Solver request created: `{draft.get('solver_request_created')}`
- Solver run: `{draft.get('solver_run')}`
- Queue launched: `{draft.get('queue_runner_launched')}`
- ODB opened: `{draft.get('odb_opened')}`
- Metrics approved: `{draft.get('odb_metrics_approved')}`
- Final evidence approved: `{draft.get('final_evidence_approved')}`
- Final verdict frozen: `{draft.get('final_verdict_frozen')}`

## Claim Boundary

This is not a real `solver_request.json`, job request, queue submission, Abaqus command, ODB acceptance, metrics approval, final evidence approval, or final verdict freeze.

## Next Required Action

A future explicit controlled solver execution stage is required before any active request file or Abaqus command can exist.
"""


def render_request_draft_schema_markdown(draft: dict[str, Any], validation: dict[str, Any]) -> str:
    return f"""# Controlled Solver Request Draft Schema

## Purpose

Draft schema only; not an active solver request.

## Source Inputs

- Source gate: `{draft.get('source_gate_id')}`
- Source gate decision: `{draft.get('source_gate_decision')}`
- Source handoff draft validated: `{draft.get('source_handoff_draft_validated')}`
- Candidate hash verified: `{draft.get('candidate_hash_verified')}`

## Future Request Shape

- Target agent: `{draft.get('target_agent')}`
- Future stage: `{draft.get('target_future_stage')}`
- Solver command label: `{draft.get('solver_command_label')}`
- Allowed output directory preview: `{draft.get('allowed_output_dir_preview')}`

## Safety Boundary

- Request active: `{draft.get('request_active')}`
- Executable request: `{draft.get('executable_request')}`
- Solver command path included: `{draft.get('solver_command_path_included')}`
- Solver command not invoked: `{draft.get('solver_command_not_invoked')}`
- Output directory created: `{draft.get('output_dir_created')}`
- Solver request created: `{draft.get('solver_request_created')}`
- Solver run: `{draft.get('solver_run')}`
- Final evidence approved: `{draft.get('final_evidence_approved')}`

## Validation

Validation status: `{validation.get('validation_status')}`

## Required Notices

- No Abaqus solver command is executed.
- No solver_request.json is created.
- No job request is created.
- Future ExecutionAgent stage is required.
- Final evidence remains locked.
"""


def render_request_no_execution_audit(audit: dict[str, Any]) -> str:
    lines = [
        "# Controlled Solver Request Draft No-Execution Audit",
        "",
        f"Audit status: `{audit.get('audit_status')}`",
        "",
        "## Checks",
        "",
    ]
    for key, value in (audit.get("checks") or {}).items():
        lines.append(f"- {key}: `{value}`")
    lines.extend(
        [
            "",
            "No active solver request, job request, Abaqus job file, solver launcher, active handoff, queue file, ODB file, metrics file, or final evidence ledger is created by Stage 5.2H.",
            "",
        ]
    )
    return "\n".join(lines)
