from __future__ import annotations

from typing import Any


def render_dry_run_request_report(result: dict[str, Any]) -> str:
    request = result.get("dry_run_request", result)
    return "\n".join(
        [
            "# Controlled Solver Dry-Run Request Materialization",
            "",
            f"Verdict: `{result.get('verdict', result.get('materialization_status'))}`",
            "",
            "Dry-run request artifact only; not an active solver_request.json.",
            "No Abaqus solver command is executed.",
            "No active solver request is created.",
            "No queue entry is created.",
            "No output execution directory is created.",
            "Future ExecutionAgent stage is required.",
            "Final evidence remains locked.",
            "",
            "## Source Chain",
            "",
            f"- Source gate validated: `{request.get('source_gate_validated')}`",
            f"- Source handoff draft validated: `{request.get('source_handoff_draft_validated')}`",
            f"- Source request draft validated: `{request.get('source_request_draft_validated')}`",
            f"- Source preflight validated: `{request.get('source_preflight_validated')}`",
            f"- Source preflight status: `{request.get('source_preflight_status')}`",
            f"- Candidate hash verified: `{request.get('candidate_hash_verified')}`",
            "",
            "## Dry-Run Request",
            "",
            f"- Request type: `{request.get('request_type')}`",
            f"- Dry-run only: `{request.get('dry_run_only')}`",
            f"- Materialized request artifact: `{request.get('materialized_request_artifact')}`",
            f"- Active request created: `{request.get('active_request_created')}`",
            f"- Request active: `{request.get('request_active')}`",
            f"- Executable request: `{request.get('executable_request')}`",
            f"- Solver execution allowed: `{request.get('solver_execution_allowed')}`",
            f"- Solver request created: `{request.get('solver_request_created')}`",
            f"- Output dir created: `{request.get('output_dir_created')}`",
            "",
            "## Safety Boundary",
            "",
            str(request.get("safety_boundary")),
        ]
    )


def render_dry_run_request_audit(audit: dict[str, Any]) -> str:
    checks = audit.get("checks", {})
    lines = [
        "# Controlled Solver Dry-Run Request No-Execution Audit",
        "",
        f"Audit status: `{audit.get('audit_status')}`",
        "",
    ]
    for key in sorted(checks):
        lines.append(f"- {key}: `{checks[key]}`")
    return "\n".join(lines)
