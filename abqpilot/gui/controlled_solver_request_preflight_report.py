from __future__ import annotations

from typing import Any


def render_request_preflight_report(result: dict[str, Any]) -> str:
    validation = result.get("validation", {})
    audit = result.get("no_execution_audit", {})
    return f"""# Stage 5.2I Controlled Solver Request Preflight Report

## Purpose

Stage 5.2I validates the controlled solver request draft before a future execution stage. Preflight pass is not solver execution permission.

## Source Validation

- Stage 5.2F gate validated: `{result.get('source_gate_validated')}`
- Stage 5.2G handoff draft validated: `{result.get('source_handoff_draft_validated')}`
- Stage 5.2H request draft validated: `{result.get('source_request_draft_validated')}`
- Candidate hash verified: `{result.get('candidate_hash_verified')}`

## Policy Validation

- Solver command label validated: `{result.get('solver_command_label_validated')}`
- Solver command path not invoked: `{result.get('solver_command_path_not_invoked')}`
- Output directory policy validated: `{result.get('output_dir_policy_validated')}`
- Output directory created: `{result.get('output_dir_created')}`
- CPU policy validated: `{result.get('cpu_policy_validated')}`
- Memory policy validated: `{result.get('memory_policy_validated')}`
- Timeout policy validated: `{result.get('timeout_policy_validated')}`
- Log capture policy validated: `{result.get('log_capture_policy_validated')}`

## Preflight Result

- Preflight status: `{result.get('preflight_status')}`
- Preflight passed: `{result.get('preflight_passed')}`
- Validator status: `{validation.get('validation_status')}`
- No-execution audit: `{audit.get('audit_status')}`

## Safety Boundary

- Preflight only: `{result.get('preflight_only')}`
- Active request created: `{result.get('active_request_created')}`
- Request active: `{result.get('request_active')}`
- Executable request: `{result.get('executable_request')}`
- Solver request created: `{result.get('solver_request_created')}`
- Solver execution allowed: `{result.get('solver_execution_allowed')}`
- Solver run: `{result.get('solver_run')}`
- Queue launched: `{result.get('queue_runner_launched')}`
- ODB opened: `{result.get('odb_opened')}`
- Metrics approved: `{result.get('odb_metrics_approved')}`
- Final evidence approved: `{result.get('final_evidence_approved')}`
- Final verdict frozen: `{result.get('final_verdict_frozen')}`

## Required Notices

- Preflight only; no solver execution.
- No Abaqus solver command is executed.
- No solver_request.json is created.
- No output directory for execution is created.
- Future ExecutionAgent stage is required.
- Final evidence remains locked.
"""


def render_request_preflight_audit(audit: dict[str, Any]) -> str:
    lines = [
        "# Controlled Solver Request Preflight No-Execution Audit",
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
            "No active solver request, job request, Abaqus job file, solver launcher, active handoff, queue file, ODB file, metrics file, or final evidence ledger is created by Stage 5.2I.",
            "",
        ]
    )
    return "\n".join(lines)
