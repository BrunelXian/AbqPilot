from __future__ import annotations

from typing import Any


def render_dflux_lifecycle_summary(summary: dict[str, Any]) -> str:
    lines = [
        "# Stage 4.3 Guarded DFLUX Deactivation Patch Preview",
        "",
        f"Verdict: `{summary.get('verdict')}`",
        f"Source INP: `{summary.get('source_inp')}`",
        f"Preview INP: `{summary.get('candidate_preview_inp')}`",
        f"MCPGuard sub-check: `{summary.get('mcp_guard_subcheck')}`",
        f"Inserted keyword: `{summary.get('inserted_keyword')}`",
        f"Inserted lines count: `{summary.get('inserted_lines_count')}`",
        f"StaticValidator: `{summary.get('static_validator')}`",
        f"DiffGuard: `{summary.get('diff_guard')}`",
        f"PhysicsGuard: `{summary.get('physics_guard')}`",
        f"DFLUX lifecycle validator: `{summary.get('dflux_lifecycle_validator')}`",
        f"Unrelated changes: `{summary.get('unrelated_changes_count')}`",
        "",
        "No solver was run. No ODB was opened. Human review remains required.",
    ]
    return "\n".join(lines) + "\n"


def render_successful_comparison_markdown(comparison: dict[str, Any]) -> str:
    lines = [
        "# Successful vs Failed 2x Job Comparison",
        "",
        f"Comparison available: `{comparison.get('successful_2x_job_file_comparison_available')}`",
    ]
    for key, value in comparison.get("files", {}).items():
        lines.append(f"- {key}: `{value}`")
    lines.extend(["", "## Findings"])
    for finding in comparison.get("findings", []):
        lines.append(f"- {finding}")
    return "\n".join(lines) + "\n"
