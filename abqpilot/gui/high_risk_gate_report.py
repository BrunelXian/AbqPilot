from __future__ import annotations

from typing import Any


def render_high_risk_gate_ux_report(spec: dict[str, Any]) -> str:
    lines = [
        "# GUI High-Risk Gate UX Specification",
        "",
        "Stage 5.2A specifies high-risk gate UX only.",
        "",
        "High-risk action locked.",
        "Preview only; not an approval.",
        "Human gate required in a future explicit stage.",
        "This GUI does not execute solver, ODB, queue, Codex, or final freeze.",
        "Final evidence remains locked.",
        "Prerequisites shown here are advisory/specification only.",
        "No real gate is created in Stage 5.2A.",
        "No TASK_FINAL_EVIDENCE_LEDGER.md mutation.",
        "",
        "## Safety Flags",
        "",
        f"- preview_only: `{spec['preview_only']}`",
        f"- specification_only: `{spec['specification_only']}`",
        f"- final_evidence_approved: `{spec['final_evidence_approved']}`",
        f"- final_verdict_frozen: `{spec['final_verdict_frozen']}`",
        f"- solver_approved: `{spec['solver_approved']}`",
        f"- odb_metrics_approved: `{spec['odb_metrics_approved']}`",
        f"- queue_runner_launched: `{spec['queue_runner_launched']}`",
        f"- codex_cli_called: `{spec['codex_cli_called']}`",
        f"- auto_execute_allowed: `{spec['auto_execute_allowed']}`",
        f"- real_gate_created: `{spec['real_gate_created']}`",
        f"- task_final_evidence_ledger_updated: `{spec['task_final_evidence_ledger_updated']}`",
        "",
        "## High-Risk Actions",
        "",
    ]
    for action in spec["high_risk_actions"]:
        lines.extend(
            [
                f"### {action['display_name']}",
                "",
                f"- action_id: `{action['action_id']}`",
                f"- risk_level: `{action['risk_level']}`",
                f"- default_allowed: `{action['default_allowed']}`",
                f"- executable_in_stage_5_2a: `{action['executable_in_stage_5_2a']}`",
                f"- preview_only: `{action['preview_only']}`",
                f"- requires_human_gate: `{action['requires_human_gate']}`",
                f"- disabled_reason: {action['disabled_reason']}",
                f"- final_evidence_effect: `{action['final_evidence_effect']}`",
                "",
            ]
        )
    lines.extend(
        [
            "## Claim Boundary",
            "",
            "This is a preview/specification record only. It is not solver readiness, ODB readiness, metrics readiness, queue readiness, Codex automation readiness, final evidence readiness, or final verdict freeze readiness.",
            "",
            f"Verdict: `{spec['verdict']}`",
        ]
    )
    return "\n".join(lines) + "\n"


def render_high_risk_action_catalog_markdown(actions: list[dict[str, Any]]) -> str:
    lines = [
        "# High-Risk Action Catalog",
        "",
        "Every action in this catalog is disabled, preview-only, and requires a future explicit human gate.",
        "",
        "| Action | Risk | Allowed | Executable in 5.2A | Preview Only | Final Evidence Effect |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for action in actions:
        lines.append(
            f"| `{action['action_id']}` | `{action['risk_level']}` | `{action['default_allowed']}` | "
            f"`{action['executable_in_stage_5_2a']}` | `{action['preview_only']}` | `{action['final_evidence_effect']}` |"
        )
    return "\n".join(lines) + "\n"


def render_high_risk_gate_checklists_markdown(previews: list[dict[str, Any]]) -> str:
    lines = [
        "# High-Risk Gate Checklist Preview",
        "",
        "Prerequisites shown here are advisory/specification only. No real gate is created in Stage 5.2A.",
        "",
    ]
    for preview in previews:
        lines.extend(
            [
                f"## {preview['display_name']}",
                "",
                f"- approval_status: `{preview['approval_status']}`",
                f"- execution_status: `{preview['execution_status']}`",
                f"- preview_only: `{preview['preview_only']}`",
                "",
                "Prerequisites:",
            ]
        )
        for item in preview["prerequisite_checklist"]:
            lines.append(f"- `{item['prerequisite_id']}`: {item['description']}")
        lines.append("")
    return "\n".join(lines) + "\n"
