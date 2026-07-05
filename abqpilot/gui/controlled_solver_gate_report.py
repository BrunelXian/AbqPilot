from __future__ import annotations

from typing import Any


def render_controlled_solver_gate_preview_report(preview: dict[str, Any]) -> str:
    lines = [
        "# Controlled Solver Human Gate Preview",
        "",
        "Controlled Solver Run is locked.",
        "Preview only; not a solver approval.",
        "Human approval token is not active in Stage 5.2B.",
        "No Abaqus solver command is executed.",
        "No solver request file is created.",
        "Future solver approval and future solver execution must be separate stages.",
        "Final evidence remains locked.",
        "ODB and metrics remain disabled.",
        "Queue mutation remains disabled.",
        "",
        "## Preview Status",
        "",
        f"- gate_type: `{preview['gate_type']}`",
        f"- readiness_status: `{preview['readiness_status']}`",
        f"- approval_status: `{preview['approval_status']}`",
        f"- execution_status: `{preview['execution_status']}`",
        f"- real_gate_created: `{preview['real_gate_created']}`",
        f"- solver_approved: `{preview['solver_approved']}`",
        f"- solver_run: `{preview['solver_run']}`",
        f"- solver_request_created: `{preview['solver_request_created']}`",
        f"- queue_runner_launched: `{preview['queue_runner_launched']}`",
        f"- odb_opened: `{preview['odb_opened']}`",
        f"- final_evidence_approved: `{preview['final_evidence_approved']}`",
        f"- final_verdict_frozen: `{preview['final_verdict_frozen']}`",
        f"- task_final_evidence_ledger_updated: `{preview['task_final_evidence_ledger_updated']}`",
        "",
        "## Readiness Checklist",
        "",
    ]
    for item in preview["prerequisite_checklist"]:
        lines.append(f"- `{item['item_id']}`: `{item['status']}` - {item['description']}")
    lines.extend(
        [
            "",
            "## Approval / Execution Separation",
            "",
        ]
    )
    for key, value in preview["approval_execution_separation"].items():
        lines.append(f"- `{key}`: {value}")
    lines.extend(
        [
            "",
            "## Safety Boundary",
            "",
            preview["safety_boundary"],
            "",
            "## Claim Boundary",
            "",
            "This is a non-final preview/specification report. It is not solver approval, solver execution, ODB acceptance, metrics acceptance, final evidence approval, or final verdict freeze.",
            "",
            f"Verdict: `{preview.get('verdict', 'CONTROLLED_SOLVER_GATE_PREVIEW_REPORT_READY')}`",
        ]
    )
    return "\n".join(lines) + "\n"


def render_controlled_solver_readiness_checklist(checklist: list[dict[str, Any]]) -> str:
    lines = [
        "# Controlled Solver Readiness Checklist",
        "",
        "This checklist is preview-only. Passing items do not approve or execute a solver run.",
        "",
        "| Item | Status | Description |",
        "| --- | --- | --- |",
    ]
    for item in checklist:
        lines.append(f"| `{item['item_id']}` | `{item['status']}` | {item['description']} |")
    return "\n".join(lines) + "\n"


def render_controlled_solver_approval_token_rules(rules: list[str]) -> str:
    lines = [
        "# Controlled Solver Approval Token Rules",
        "",
        "The token schema is preview-only in Stage 5.2B. A token that validates here is valid for future-stage design review only and is not active approval.",
        "",
    ]
    lines.extend(f"- {rule}" for rule in rules)
    lines.extend(
        [
            "",
            "If `active_approval=true`, validation must return `TOKEN_PREVIEW_BLOCKED_ACTIVE_APPROVAL_ATTEMPT`.",
            "Future approval and future solver execution must remain separate stages.",
        ]
    )
    return "\n".join(lines) + "\n"
