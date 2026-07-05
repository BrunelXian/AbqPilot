from __future__ import annotations

from typing import Any


def render_gui_beta_smoke_report(result: dict[str, Any]) -> str:
    lines = [
        "# GUI Beta E2E Safe Workflow Smoke Report",
        "",
        "GUI beta readiness for non-solver ACOM governance.",
        "",
        "This is not final evidence approval.",
        "Final evidence remains locked.",
        "Solver / ODB / metrics remain disabled.",
        "GUI does not call Codex CLI.",
        "Codex is external/manual and returns structured_result.json for intake.",
        "Recommendations are advisory; no automatic execution.",
        "Disabled high-risk actions remain callback-free.",
        "Unsafe final-approval claims are flagged, not fixed.",
        "",
        f"Verdict: `{result.get('verdict')}`",
        f"GUI beta ready: `{result.get('gui_beta_ready')}`",
        f"Generated at: `{result.get('generated_at')}`",
        "",
        "## Smoke Cases",
        "",
        "| Case | Status | Expected | Observed |",
        "| --- | --- | --- | --- |",
    ]
    for case in result.get("smoke_cases", []):
        lines.append(
            f"| {case.get('case_id')} | {'PASS' if case.get('passed') else 'FAIL'} | "
            f"{case.get('expected')} | {case.get('observed')} |"
        )
    lines.extend(["", "## Component Checks", ""])
    for key, value in result.get("component_checks", {}).items():
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(
        [
            "",
            "## Safety Boundary",
            "",
            f"- final_evidence_approved: `{result.get('final_evidence_approved')}`",
            f"- final_verdict_frozen: `{result.get('final_verdict_frozen')}`",
            f"- solver_approved: `{result.get('solver_approved')}`",
            f"- odb_metrics_approved: `{result.get('odb_metrics_approved')}`",
            f"- codex_cli_called: `{result.get('codex_cli_called')}`",
            f"- queue_runner_launched: `{result.get('queue_runner_launched')}`",
            f"- auto_execute_allowed: `{result.get('auto_execute_allowed')}`",
            "",
            "## Known Limitations",
            "",
        ]
    )
    lines.extend(f"- {item}" for item in result.get("known_limitations", []))
    return "\n".join(lines) + "\n"
