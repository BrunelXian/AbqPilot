from __future__ import annotations

from typing import Any


def render_execution_handoff_draft_markdown(draft: dict[str, Any], validation: dict[str, Any]) -> str:
    return f"""# Controlled Solver Execution Handoff Draft

## Purpose

Draft only; not an active execution handoff.

## Source Gate

- Source task: `{draft.get('source_task_id')}`
- Source gate: `{draft.get('source_gate_id')}`
- Source decision: `{draft.get('source_gate_decision')}`
- Source gate validated: `{draft.get('source_gate_validated')}`

## Candidate Hash

- Candidate: `{draft.get('candidate_artifact_path')}`
- SHA256: `{draft.get('candidate_artifact_hash')}`
- Candidate hash verified: `{draft.get('candidate_hash_verified')}`

## Future Handoff Shape

- From agent: `{draft.get('from_agent')}`
- To agent: `{draft.get('to_agent')}`
- Future stage: `{draft.get('target_future_stage')}`
- Future ExecutionAgent stage is required.

## Safety Boundary

- Draft only: `{draft.get('draft_only')}`
- Active execution handoff: `{draft.get('active_execution_handoff')}`
- Handoff active for execution: `{draft.get('handoff_active_for_execution')}`
- Execution status: `{draft.get('execution_status')}`
- Solver execution allowed: `{draft.get('solver_execution_allowed')}`
- Solver request created: `{draft.get('solver_request_created')}`
- Solver run: `{draft.get('solver_run')}`
- Queue runner launched: `{draft.get('queue_runner_launched')}`
- ODB opened: `{draft.get('odb_opened')}`
- ODB metrics approved: `{draft.get('odb_metrics_approved')}`
- Final evidence approved: `{draft.get('final_evidence_approved')}`
- Final verdict frozen: `{draft.get('final_verdict_frozen')}`

## Validation

Validation status: `{validation.get('validation_status')}`

## Claim Boundary

This is not a solver request, job manifest, execution command, ODB acceptance, metrics approval, final evidence approval, or final verdict freeze.

## Notices

- No Abaqus solver command is executed.
- No solver request file is created.
- Final evidence remains locked.
"""


def render_execution_handoff_report(result: dict[str, Any]) -> str:
    draft = result.get("draft", {})
    validation = result.get("validation", {})
    audit = result.get("no_execution_audit", {})
    return f"""# Stage 5.2G Controlled Solver Execution Handoff Draft Report

## Purpose

Stage 5.2G creates a draft-only future ExecutionAgent handoff from the Stage 5.2F smoke gate. It does not create an active execution handoff.

## Source Stage 5.2F Gate

- Source gate validation: `{result.get('source_gate_validation_status')}`
- Source gate decision: `{draft.get('source_gate_decision')}`
- Candidate hash verified: `{draft.get('candidate_hash_verified')}`

## Handoff Draft

- Draft created: `{result.get('draft_created')}`
- Draft only: `{draft.get('draft_only')}`
- Active execution handoff: `{draft.get('active_execution_handoff')}`
- Handoff active for execution: `{draft.get('handoff_active_for_execution')}`
- To agent: `{draft.get('to_agent')}`
- Execution status: `{draft.get('execution_status')}`

## Validation

- Draft validation: `{validation.get('validation_status')}`
- No-execution audit: `{audit.get('audit_status')}`

## Safety Boundary

- Solver execution allowed: `{draft.get('solver_execution_allowed')}`
- Solver request created: `{draft.get('solver_request_created')}`
- Solver run: `{draft.get('solver_run')}`
- Queue runner launched: `{draft.get('queue_runner_launched')}`
- ODB opened: `{draft.get('odb_opened')}`
- Metrics approved: `{draft.get('odb_metrics_approved')}`
- Final evidence approved: `{draft.get('final_evidence_approved')}`
- Final verdict frozen: `{draft.get('final_verdict_frozen')}`

## Claim Boundary

This draft is not a solver request, job manifest, execution command, ODB acceptance, metrics approval, final evidence approval, or final verdict freeze.

## Next Required Action

A future explicit controlled solver execution stage is required before any solver request or Abaqus command can exist.
"""


def render_no_execution_audit(audit: dict[str, Any]) -> str:
    lines = [
        "# Controlled Solver Execution Handoff Draft No-Execution Audit",
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
            "No solver request, job request, Abaqus job file, active execution handoff, queue file, ODB file, metrics file, or final evidence ledger is created by Stage 5.2G.",
            "",
        ]
    )
    return "\n".join(lines)
